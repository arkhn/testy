import json
import logging

import pytest
import requests

from fhirstore import FHIRStore

from .. import settings
from .utils.kafka import EventConsumer

logger = logging.getLogger(__file__)

BATCH_SIZE_TOPIC = "batch_size"
LOAD_TOPIC = "load"


@pytest.fixture(scope="module")
def cleanup(fhirstore: FHIRStore):
    yield
    encounters = fhirstore.db["Encounter"]
    patients = fhirstore.db["Patient"]
    encounters.delete_many({})
    patients.delete_many({})


def handle_kafka_error(err):
    raise err


def test_batch_single_row(pyrog_resources):
    logger.info("Start")

    # declare kafka consumer of "load" events
    consumer = EventConsumer(
        broker=settings.KAFKA_LISTENER,
        topics=LOAD_TOPIC,
        group_id="test_batch_single_row",
        manage_error=handle_kafka_error,
    )

    def wait_batch(msg):
        msg_value = json.loads(msg.value())
        print(f"Go batch of size {msg_value['size']}, consuming events...")
        consumer.run_consumer(event_count=msg_value["size"], poll_timeout=15)

    batch_size_consumer = EventConsumer(
        broker=settings.KAFKA_LISTENER,
        topics=BATCH_SIZE_TOPIC,
        group_id="test_batch_size",
        manage_error=handle_kafka_error,
        process_event=wait_batch,
    )

    for resource in pyrog_resources:
        try:
            # send a batch request
            response = requests.post(
                f"{settings.RIVER_API_URL}/batch",
                json={"resources": [resource]},
            )
        except requests.exceptions.ConnectionError:
            raise Exception("Could not connect to the api service")

        assert (
            response.status_code == 200
        ), f"api POST /batch returned an error: {response.text}"

        print("Waiting for a batch_size event...")
        batch_size_consumer.run_consumer(event_count=1, poll_timeout=15)


# check in elastic that references have been set
