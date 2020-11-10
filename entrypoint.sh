# setup port forwarding
REMOTE_HOST=$(echo $REMOTE_URL | sed -E 's/(https|http)(:\/\/)(.*)$/\3/')

MONGO_PRIVATE_IP=$(ssh root@$REMOTE_HOST 'docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $(docker ps -q --filter "label=com.docker.compose.service=mongo")')
REMOTE_MONGO_PORT=27017
ssh -fN -L localhost:$REMOTE_MONGO_PORT:$MONGO_PRIVATE_IP:$REMOTE_MONGO_PORT root@$REMOTE_HOST

KAFKA_PRIVATE_IP=$(ssh root@$REMOTE_HOST 'docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $(docker ps -q --filter "label=com.docker.compose.service=kafka")')
REMOTE_KAFKA_PORT=9093
ssh -fN -L localhost:$REMOTE_KAFKA_PORT:$KAFKA_PRIVATE_IP:$REMOTE_KAFKA_PORT root@$REMOTE_HOST

# inject environment variables and run pytest
REMOTE_URL=$REMOTE_URL
KAFKA_BOOTSTRAP_SERVERS_EXTERNAL=0.0.0.0:$REMOTE_KAFKA_PORT \
FHIRSTORE_HOST=localhost \
FHIRSTORE_PORT=$REMOTE_MONGO_PORT \
FHIRSTORE_DATABASE=fhirstore \
FHIRSTORE_USER=arkhn \
FHIRSTORE_PASSWORD=<MONGO_DB_PASSWORD> \
pytest -svv

# teardown port forwarding
lsof -Fp -i :$REMOTE_MONGO_PORT | sed -n "s/^p//p" | xargs kill -9
lsof -Fp -i :$REMOTE_KAFKA_PORT | sed -n "s/^p//p" | xargs kill -9
