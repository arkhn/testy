import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

MONGO_DB = os.environ.get("MONGO_DB", "fhirstore")
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", "27017"))
MONGO_USER = os.environ.get("MONGO_USER", "arkhn")
MONGO_PASSWORD = os.environ["MONGO_PASSWORD"]

PYROG_API_HOST = os.environ["PYROG_API_HOST"]
RIVER_API_HOST = os.environ["RIVER_API_HOST"]

KAFKA_BOOTSTRAP_SERVERS_EXTERNAL = os.environ["KAFKA_BOOTSTRAP_SERVERS_EXTERNAL"]
