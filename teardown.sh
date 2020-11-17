#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Trace execution
[[ "${DEBUG}" ]] && set -x

kill -9 "${TESTY_TUNNEL_PID}"

unset TESTY_TUNNEL_PID
unset TESTY_PUBLIC_HOST
unset KAFKA_BOOTSTRAP_SERVERS_EXTERNAL
unset FHIRSTORE_HOST
unset FHIRSTORE_PORT
unset FHIRSTORE_DATABASE
unset FHIRSTORE_USER