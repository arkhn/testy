import logging
import pytest
import redis
import requests

from fhirstore import FHIRStore

from .. import settings

logger = logging.getLogger(__file__)


@pytest.fixture(scope="module")
def store(fhirstore: FHIRStore):
    yield fhirstore
    encounters = fhirstore.db["Encounter"]
    patients = fhirstore.db["Patient"]
    encounters.delete_many({})
    patients.delete_many({})


def handle_kafka_error(err):
    raise err


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

    logger.debug("Waiting for a batch_size event...")
    return response.text


def test_batch_reference_binder(store, pyrog_resources):
    redis_client = redis.Redis(
        host=settings.REDIS_COUNTER_HOST,
        port=settings.REDIS_COUNTER_PORT,
        db=settings.REDIS_COUNTER_DB
    )
    # Enable keyspace notifications for keyevent events E
    # and generic commands g
    redis_client.config_set("notify-keyspace-events", "Eg")
    redis_ps = redis_client.pubsub()
    redis_ps.subscribe(f"__keyevent@{settings.REDIS_COUNTER_DB}__:del")

    # Send Patient and Encounter batch
    batch_id = send_batch(pyrog_resources)

    logger.debug(f"Waiting for stop signal of batch {batch_id}")
    # psubscribe message
    msg = redis_ps.get_message(timeout=500.0)
    logger.debug(f"Redis msg: {msg}")
    # Actual signaling message
    msg = redis_ps.get_message(timeout=500.0)
    logger.debug(f"Redis msg: {msg}")
    assert msg is not None, f"No response from batch {batch_id}"
    assert msg['data'] == f"batch:{batch_id}:resources", \
        f"Validation error on Redis message: {msg}"

    # Check reference binding
    encounters = store.db["Encounter"]
    patients = store.db["Patient"]
    cursor = encounters.find({})
    for document in cursor:
        assert "reference" in document["subject"]
        reference = document["subject"]["reference"].split("/")
        assert reference[0] == "Patient"
        patient = patients.find_one(filter={"id": reference[1]})
        assert patient
