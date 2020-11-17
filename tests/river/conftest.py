import json
from pathlib import Path

import pytest
from pymongo import MongoClient

from fhirstore import FHIRStore

from .. import settings
from .utils.pyrog import PyrogClient

DATA_DIR = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def fhirstore() -> FHIRStore:
    mongo_client = MongoClient(
        host=settings.MONGO_HOST,
        port=settings.MONGO_PORT,
        username=settings.MONGO_USER,
        password=settings.MONGO_PASSWORD,
    )
    return FHIRStore(mongo_client, None, settings.MONGO_DB)


@pytest.fixture(scope="session")
def pyrog_resources():
    with open(DATA_DIR / "mapping.json") as mapping_file:
        mapping = json.load(mapping_file)
    with open(DATA_DIR / "credentials.json") as credentials_file:
        credentials = json.load(credentials_file)

    pyrog_client = PyrogClient(settings.PYROG_API_URL)
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
