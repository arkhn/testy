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


def send_batch(resources) -> str:
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
    return response.text


def test_batch(pyrog_resources, cleanup):
    logger.debug("Start")

    redis_client = redis.Redis(
        host=settings.REDIS_COUNTER_HOST,
        port=settings.REDIS_COUNTER_PORT,
        db=settings.REDIS_COUNTER_DB
    )
    # Enable keyspace notifications for keyevent events E
    # and generic commands g
    redis_client.config_set("notify-keyspace-events", "Eg")
    redis_ps = redis_client.pubsub()
    redis_ps.psubscribe(f"__keyevent@{settings.REDIS_COUNTER_DB}__:del")

    # Send Patient and Encounter batch
    batch_id = send_batch(pyrog_resources)
    # UUID will raise a ValueError if batch_id is not a valid uuid
    UUID(batch_id, version=4)

    logger.debug(f"Waiting for stop signal of batch {batch_id}")
    # psubscribe message
    msg = redis_ps.get_message(timeout=5.0)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, f"No response from Redis"
    # Actual signaling message
    msg = redis_ps.get_message(timeout=300.0)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, f"No response from batch {batch_id}"
    assert msg['data'].decode("utf-8") == f"batch:{batch_id}:resources", \
        f"Validation error on Redis message: {msg}"
    # Exit subscribed state. It is required to issue any other command
    redis_ps.reset()

    # Test wether what has been extracted has been eventually loaded
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
