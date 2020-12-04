import logging
import pytest
import requests
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


def cancel_batch(batch_id):
    try:
        response = requests.delete(f"{settings.RIVER_API_URL}/batch/{batch_id}")
    except requests.exceptions.ConnectionError:
        raise Exception("Could not connect to the api service")

    assert (
            response.status_code == 200
    ), f"api DELETE /batch/{batch_id} returned an error: {response.text}"


def test_cancel_batch(pyrog_resources, cleanup):
    logger.debug("Start")

    # Send Patient and Encounter batch
    batch_id = send_batch(pyrog_resources)

    cancel_batch(batch_id)

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
