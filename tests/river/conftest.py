import contextlib
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
def pyrog_client():
    return PyrogClient(settings.PYROG_API_URL)


@pytest.fixture(scope="session")
def template_factory(pyrog_client: PyrogClient):
    @contextlib.contextmanager
    def _template_factory(name: str):
        template = pyrog_client.create_template(name)
        yield template
        pyrog_client.delete_template(template["id"])

    return _template_factory


@pytest.fixture(scope="session")
def source_factory(pyrog_client: PyrogClient):
    @contextlib.contextmanager
    def _source_factory(name: str, template_name: str, mapping: str):
        source_id = pyrog_client.create_source(
            name=name, template_name=template_name, mapping=mapping
        )
        yield source_id
        pyrog_client.delete_source(source_id)

    return _source_factory


@pytest.fixture(scope="session")
def credentials_factory(pyrog_client: PyrogClient):
    @contextlib.contextmanager
    def _credentials_factory(source_id: str, credentials: dict):
        yield pyrog_client.upsert_credentials(
            source_id=source_id, credentials=credentials
        )
        # TODO(vmttn): remove credentials

    return _credentials_factory


@pytest.fixture(scope="session")
def pyrog_resources(
    pyrog_client: PyrogClient, template_factory, source_factory, credentials_factory
):
    with open(DATA_DIR / "mapping.json") as mapping_file:
        mapping = json.load(mapping_file)
    with open(DATA_DIR / "credentials.json") as credentials_file:
        credentials = json.load(credentials_file)

    with contextlib.ExitStack() as stack:
        stack.enter_context(template_factory(mapping["template"]["name"]))
        source_id = stack.enter_context(
            source_factory(
                mapping["source"]["name"],
                mapping["template"]["name"],
                json.dumps(mapping),
            )
        )
        stack.enter_context(credentials_factory(source_id, credentials))

        yield pyrog_client.list_resources()
