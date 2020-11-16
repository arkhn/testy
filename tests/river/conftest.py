import json

import pytest
from pymongo import MongoClient

from fhirstore import FHIRStore

from .. import settings
from .utils.pyrog import PyrogClient


@pytest.fixture(scope="session")
def fhirstore() -> FHIRStore:
    mongo_client = MongoClient(
        host=settings.FHIRSTORE_HOST,
        port=settings.FHIRSTORE_PORT,
        username=settings.FHIRSTORE_USER,
        password=settings.FHIRSTORE_PASSWORD,
    )
    return FHIRStore(mongo_client, None, settings.FHIRSTORE_DATABASE)


@pytest.fixture(scope="session")
def pyrog_resources():
    with open("./river/data/mapping.json") as mapping_file:
        mapping = json.load(mapping_file)
    with open("./river/data/credentials.json") as credentials_file:
        credentials = json.load(credentials_file)

    pyrog_client = PyrogClient(f"{settings.REMOTE_URL}/pyrog-api")
    try:
        pyrog_client.create_template(mapping["template"]["name"])
    except Exception:
        pass
    source_id = pyrog_client.create_source(
        mapping["template"]["name"], mapping["source"]["name"], json.dumps(mapping)
    )
    pyrog_client.upsert_credentials(source_id, credentials)

    # yield the inserted resources
    yield pyrog_client.get_resources()

    # cleanup the created source
    pyrog_client.delete_source(source_id)
