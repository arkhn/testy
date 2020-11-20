import os

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

MONGO_DB = os.environ.get("MONGO_DB", "fhirstore")
MONGO_HOST = os.environ.get("MONGO_HOST", "localhost")
MONGO_PORT = int(os.environ.get("MONGO_PORT", "27017"))
MONGO_USER = os.environ.get("MONGO_USER", "arkhn")
MONGO_PASSWORD = os.environ["MONGO_PASSWORD"]

PYROG_API_HOST = os.environ.get("PYROG_API_HOST", "pyrog-server")
PYROG_API_PORT = int(os.environ.get("PYROG_API_PORT", "1000"))
PYROG_API_URL = f"http://{PYROG_API_HOST}:{PYROG_API_PORT}/"

RIVER_API_HOST = os.environ.get("RIVER_API_HOST", "river-api")
RIVER_API_PORT = int(os.environ.get("RIVER_API_PORT", "3000"))
RIVER_API_URL = f"http://{RIVER_API_HOST}:{RIVER_API_PORT}"

KAFKA_HOST = os.environ.get("KAFKA_HOST", "kafka")
KAFKA_PORT = os.environ.get("KAFKA_PORT", "9092")
KAFKA_PROTO = os.environ.get("KAFKA_PROTO", "PLAINTEXT")
KAFKA_LISTENER = (
    os.environ.get("KAFKA_LISTENER") or f"{KAFKA_PROTO}://{KAFKA_HOST}:{KAFKA_PORT}"
)
