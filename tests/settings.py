import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

FHIRSTORE_HOST = os.environ["FHIRSTORE_HOST"]
FHIRSTORE_PORT = int(os.environ["FHIRSTORE_PORT"])
FHIRSTORE_DATABASE = os.environ["FHIRSTORE_DATABASE"]
FHIRSTORE_USER = os.environ["FHIRSTORE_USER"]
FHIRSTORE_PASSWORD = os.environ["FHIRSTORE_PASSWORD"]

KAFKA_BOOTSTRAP_SERVERS_EXTERNAL = os.environ["KAFKA_BOOTSTRAP_SERVERS_EXTERNAL"]

REMOTE_URL = os.environ["REMOTE_URL"]
