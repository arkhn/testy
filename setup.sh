#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Trace execution
[[ "${DEBUG}" ]] && set -x

function clean() {
    set +e
    set +x
}

if [[ -z "${FHIRSTORE_PASSWORD}" ]]; then
    echo "Please provide the fhirstore password like this:"
    echo "$ FHIRSTORE_PASSWORD=... source setup.sh HOST_IP SSH_IDENTITY_FILE"
    clean && return
fi

HOST="$1"
SSH_IDENTITY_FILE="$2"

MONGO_PRIVATE_IP=$(ssh -o IdentityFile="${SSH_IDENTITY_FILE}" root@"${HOST}" 'docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $(docker ps -q --filter "label=com.docker.compose.service=mongo")')
KAFKA_PRIVATE_IP=$(ssh -o IdentityFile="${SSH_IDENTITY_FILE}" root@"${HOST}" 'docker inspect --format "{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}" $(docker ps -q --filter "label=com.docker.compose.service=kafka")')

ssh -o IdentityFile="${SSH_IDENTITY_FILE}" \
    -fN \
    -L localhost:27017:"${MONGO_PRIVATE_IP}":27017 root@"${HOST}" \
    -L localhost:9093:"${KAFKA_PRIVATE_IP}":9093 root@"${HOST}"
export TESTY_TUNNEL_PID="$!"

export TESTY_PUBLIC_HOST="${HOST}"
export TESTY_USE_SSL=False

export KAFKA_BOOTSTRAP_SERVERS_EXTERNAL=0.0.0.0:9093
export FHIRSTORE_HOST=localhost
export FHIRSTORE_PORT=27017
export FHIRSTORE_DATABASE=fhirstore
export FHIRSTORE_USER=arkhn

clean
