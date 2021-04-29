from confluent_kafka.admin import AdminClient
from fhirpy import SyncFHIRClient
import logging
import pytest
import redis
import re
import requests
import time
from uuid import UUID

from .. import settings


logger = logging.getLogger(__file__)


def send_batch(resources) -> dict:
    try:
        # send a batch request
        response = requests.post(f"{settings.RIVER_API_URL}/batch/", json={"resources": resources})
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to the api service")

    assert response.status_code == 200, f"api POST /batch returned an error: {response.text}"
    return response.json()


redis_client = redis.Redis(
    host=settings.REDIS_COUNTER_HOST,
    port=settings.REDIS_COUNTER_PORT,
    db=settings.REDIS_COUNTER_DB,
)
# Enable keyspace notifications for keyevent events
# and hash commands
redis_client.config_set("notify-keyspace-events", "Eh")


@pytest.fixture(autouse=True, scope="session")
def batch(pyrog_resources):
    redis_ps = redis_client.pubsub()
    redis_ps.subscribe(f"__keyevent@{settings.REDIS_COUNTER_DB}__:hdel")

    # Send Patient and Encounter batch
    batch = send_batch(pyrog_resources)
    # UUID will raise a ValueError if batch_id is not a valid uuid
    UUID(batch["id"], version=4)

    # When a batch ends, the API deletes the corresponding field in the Redis key "batch'.
    # Here we want to get the notification of this event.
    logger.debug("Waiting for the current batch to end")
    # psubscribe message telling us the subscription works
    msg = redis_ps.get_message(timeout=5.0)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, "No response from Redis"
    # The following message signals that a batch has been deleted
    msg = redis_ps.get_message(timeout=settings.BATCH_DURATION_TIMEOUT)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, f"No response from batch {batch['id']}"
    assert msg["data"].decode("utf-8") == "batch", f"Validation error on Redis message: {msg}"
    # Exit subscribed state. It is required to issue any other command
    redis_ps.reset()
    yield batch


def test_batch(pyrog_resources, batch):
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
    logger.debug(f"Processing {batch['id']} counter...")
    counter = {
        k.decode("utf-8"): int(v)
        for k, v in redis_client.hgetall(f"batch:{batch['id']}:counter").items()
    }
    logger.debug(f"Redis counter: {counter}")
    assert any(v != 0 for v in counter.values()), f"Counter is empty: {counter}"
    for key, value in counter.items():
        if key.endswith(":extracted") and value != 0:
            resource_id = re.search("^resource:(.*):extracted$", key).group(1)
            assert (
                value == counter[f"resource:{resource_id}:loaded"]
            ), f"Equality error on batch {batch['id']} for resource {resource_id}"

    # Test if the batch topics have been deleted
    # At the end of a batch, its topics are deleted from Kafka
    # NOTE with the Python API, topics are only marked as "to delete" and the operation is asynchronous.
    # Thus, we sleep.
    time.sleep(10)
    batch_topics = [
        f"batch.{batch['id']}",
        f"extract.{batch['id']}",
        f"transform.{batch['id']}",
        f"load.{batch['id']}",
    ]
    topics = AdminClient({"bootstrap.servers": settings.KAFKA_LISTENER}).list_topics().topics
    logger.debug(f"Existing Kafka topics: {topics}")
    assert not set(batch_topics) & set(topics)


def test_batch_reference_binder(fhir_client: SyncFHIRClient):
    def find_ref_in_bundle(bundle, resource_ref):
        resource_id = resource_ref.split("/")[1]
        for entry in [e for e in bundle.entry if e.search.mode == "include"]:
            if entry.resource.id == resource_id:
                return entry.resource
        return None

    # Check reference binding
    result = (
        fhir_client.resources("Observation")
        .limit(settings.MAX_RESOURCE_COUNT)
        .include("Observation", "subject")
        .fetch_raw()
    )
    for entry in [e for e in result.entry if e.search.mode == "match"]:
        observation = entry.resource
        included_ref = find_ref_in_bundle(result, observation.subject.reference)
        assert (
            included_ref is not None
        ), f"missing referenced resource {observation.subject.reference}"
