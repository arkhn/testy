import os
import json
import pytest

from pymongo import MongoClient
from fhirstore import FHIRStore

from .pyrog_client import PyrogClient

FHIRSTORE_HOST = os.getenv("FHIRSTORE_HOST")
if not FHIRSTORE_HOST:
    raise Exception("env: missing FHIRSTORE_HOST")

FHIRSTORE_PORT = os.getenv("FHIRSTORE_PORT")
if not FHIRSTORE_PORT:
    raise Exception("env: missing FHIRSTORE_PORT")

FHIRSTORE_DATABASE = os.getenv("FHIRSTORE_DATABASE")
if not FHIRSTORE_DATABASE:
    raise Exception("env: missing FHIRSTORE_DATABASE")

FHIRSTORE_USER = os.getenv("FHIRSTORE_USER")
if not FHIRSTORE_USER:
    raise Exception("env: missing FHIRSTORE_USER")

FHIRSTORE_PASSWORD = os.getenv("FHIRSTORE_PASSWORD")
if not FHIRSTORE_PASSWORD:
    raise Exception("env: missing FHIRSTORE_PASSWORD")

KAFKA_BOOTSTRAP_SERVERS_EXTERNAL = os.getenv("KAFKA_BOOTSTRAP_SERVERS_EXTERNAL")
if not KAFKA_BOOTSTRAP_SERVERS_EXTERNAL:
    raise Exception("env: missing KAFKA_BOOTSTRAP_SERVERS_EXTERNAL")

REMOTE_URL = os.getenv("REMOTE_URL")
if not REMOTE_URL:
    raise Exception("env: missing REMOTE_URL")


@pytest.fixture(scope="session")
def fhirstore() -> FHIRStore:
    mongo_client = MongoClient(
        host=FHIRSTORE_HOST,
        port=int(FHIRSTORE_PORT),
        username=FHIRSTORE_USER,
        password=FHIRSTORE_PASSWORD,
    )
    return FHIRStore(mongo_client, None, FHIRSTORE_DATABASE)

@pytest.fixture(scope="session")
def pyrog_resources():
    with open('./river/fixtures/mapping.json') as mapping_file:
        mapping = json.load(mapping_file)
    with open('./river/fixtures/credentials.json') as credentials_file:
        credentials = json.load(credentials_file)

    pyrog_client = PyrogClient(f"{REMOTE_URL}/pyrog-api")
    try:
        pyrog_client.create_template(mapping["template"]["name"])
    except Exception as e:
        pass
    source_id = pyrog_client.create_source(mapping["template"]["name"], mapping["source"]["name"], json.dumps(mapping))
    pyrog_client.upsert_credentials(source_id, credentials)

    # yield the inserted resources
    yield pyrog_client.get_resources()

    # cleanup the created source
    pyrog_client.delete_source(source_id)

