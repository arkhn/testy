import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

FHIRSTORE_HOST = os.environ.get("FHIRSTORE_HOST", "localhost")
FHIRSTORE_PORT = int(os.environ.get("FHIRSTORE_PORT", "27017"))
FHIRSTORE_DATABASE = os.environ.get("FHIRSTORE_DATABASE", "fhirstore")
FHIRSTORE_USER = os.environ.get("FHIRSTORE_USER", "arkhn")
FHIRSTORE_PASSWORD = os.environ["FHIRSTORE_PASSWORD"]
KAFKA_BOOTSTRAP_SERVERS_EXTERNAL = os.environ["KAFKA_BOOTSTRAP_SERVERS_EXTERNAL"]
PUBLIC_HOST=os.environ["TESTY_PUBLIC_HOST"]
USE_SSL=os.environ.get("USE_SSL", False)
REMOTE_URL = f"{'https' if USE_SSL else 'http'}://{PUBLIC_HOST}"
