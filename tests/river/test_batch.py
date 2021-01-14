import logging
import redis
import pytest
import requests
import re
from uuid import UUID
from confluent_kafka.admin import AdminClient

from fhirstore import FHIRStore

from .. import settings

logger = logging.getLogger(__file__)


@pytest.fixture(scope="module")
def cleanup(fhirstore: FHIRStore):
    yield
    encounters = fhirstore.db["Encounter"]
    patients = fhirstore.db["Patient"]
    encounters.delete_many({})
    patients.delete_many({})


def send_batch(resources) -> dict:
    try:
        # send a batch request
        response = requests.post(
            f"{settings.RIVER_API_URL}/batch", json={"resources": resources}
        )
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to the api service")

    assert (
            response.status_code == 200
    ), f"api POST /batch returned an error: {response.text}"
    return response.json()


def test_batch(pyrog_resources, cleanup):
    logger.debug("Start")

    redis_client = redis.Redis(
        host=settings.REDIS_COUNTER_HOST,
        port=settings.REDIS_COUNTER_PORT,
        db=settings.REDIS_COUNTER_DB
    )
    # Enable keyspace notifications for keyevent events
    # and hash commands
    redis_client.config_set("notify-keyspace-events", "Eh")
    redis_ps = redis_client.pubsub()
    redis_ps.psubscribe(f"__keyevent@{settings.REDIS_COUNTER_DB}__:hdel")

    # Send Patient and Encounter batch
    batch = send_batch(pyrog_resources)
    batch_id = batch["id"]
    # UUID will raise a ValueError if batch_id is not a valid uuid
    UUID(batch_id, version=4)

    # When a batch ends, the API deletes the corresponding field in the Redis key "batch'.
    # Here we want to get the notification of this event.
    logger.debug(f"Waiting for the current batch to end")
    # psubscribe message telling us the subscription works
    msg = redis_ps.get_message(timeout=5.0)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, "No response from Redis"
    # The following message signals that a batch has been deleted
    msg = redis_ps.get_message(timeout=settings.BATCH_DURATION_TIMEOUT)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None and msg['data'].decode("utf-8") == "batch", \
        f"Validation error on Redis message: {msg}"
    # Exit subscribed state. It is required to issue any other command
    redis_ps.reset()

    # Test whether what has been extracted has been eventually loaded
    # thank to the Redis key batch:{batch_id}:counter which counts every
    # records extracted in the Extractor and documents loaded in the Loader.
    # The key batch:{batch_id}:counter is a hash of the form
    # {
    #   "resource:{resource_id}:extracted": integer,
    #   "resource:{resource_id}:loaded": integer,
    #   ...
    # }
    # The counter contains an extracted key for each resource of the batch
    # which can be null if no record has been extracted. In this last case,
    # the loaded key won't exist.
    logger.debug(f"Processing {batch_id} counter...")
    counter = {
        k.decode("utf-8"): int(v) for k, v
        in redis_client.hgetall(f"batch:{batch_id}:counter").items()
    }
    logger.debug(f"Redis counter: {counter}")
    assert counter is not None and any(v != 0 for v in counter.values()), \
        f"Counter is empty: {counter}"
    for key, value in counter.items():
        if key.endswith(":extracted") and value != 0:
            resource_id = re.search("^resource:(.*):extracted$", key).group(1)
            assert value == counter[f"resource:{resource_id}:loaded"], \
                f"Equality error on batch {batch_id} for resource {resource_id}"

    # Test if the batch topics have been deleted
    # At the end of a batch, its topics are deleted from Kafka
    batch_topics = [
        f"batch.{batch_id}",
        f"extract.{batch_id}",
        f"transform.{batch_id}",
        f"load.{batch_id}"
    ]
    topics = AdminClient({"bootstrap.servers": settings.KAFKA_LISTENER}).list_topics().topics
    logger.debug(f"Existing Kafka topics: {topics}")
    assert not set(batch_topics) & set(topics)

# TODO: check in elastic that references have been set
