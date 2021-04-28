import contextlib
import json
from pathlib import Path
import requests

from fhirpy import SyncFHIRClient

import pytest

from .. import settings
from .utils.pyrog import PyrogClient

DATA_DIR = Path(__file__).resolve().parent / "data"


@pytest.fixture(scope="session")
def fhir_client() -> SyncFHIRClient:
    return SyncFHIRClient(settings.FHIR_API_URL, authorization=settings.FHIR_API_AUTH_TOKEN)


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
        source = pyrog_client.create_source(name=name, template_name=template_name, mapping=mapping)
        yield source
        pyrog_client.delete_source(source["id"])

    return _source_factory


@pytest.fixture(scope="session")
def credentials_factory(pyrog_client: PyrogClient):
    @contextlib.contextmanager
    def _credentials_factory(source_id: str, credentials: dict):
        yield pyrog_client.upsert_credentials(source_id=source_id, credentials=credentials)
        # TODO(vmttn): remove credentials

    return _credentials_factory


@pytest.fixture(scope="session")
def concept_maps_factory(fhir_client: SyncFHIRClient):
    @contextlib.contextmanager
    def _concept_maps_factory(bundle):
        for entry in bundle.get("entry", []):
            resource = entry.get("resource")
            resource_type = resource.get("resourceType")
            response = requests.post(
                f"{settings.FHIR_API_URL}/{resource_type}",
                json=resource,
                headers={"Authorizarion": settings.FHIR_API_AUTH_TOKEN},
            )
        yield "OK"

    return _concept_maps_factory


@pytest.fixture(scope="session")
def pyrog_resources(
    pyrog_client: PyrogClient,
    template_factory,
    source_factory,
    credentials_factory,
    concept_maps_factory,
):
    with open(DATA_DIR / "conceptMaps.json") as concept_maps_file:
        concept_maps = json.load(concept_maps_file)
    with open(DATA_DIR / "mapping.json") as mapping_file:
        mapping = json.load(mapping_file)
    with open(DATA_DIR / "credentials.json") as credentials_file:
        credentials = json.load(credentials_file)

    with contextlib.ExitStack() as stack:
        stack.enter_context(concept_maps_factory(concept_maps))
        stack.enter_context(template_factory(mapping["template"]["name"]))
        source = stack.enter_context(
            source_factory(
                mapping["source"]["name"],
                mapping["template"]["name"],
                json.dumps(mapping),
            )
        )
        stack.enter_context(credentials_factory(source["id"], credentials))

        yield pyrog_client.list_resources()
