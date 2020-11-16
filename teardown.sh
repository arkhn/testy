#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Trace execution
[[ "${DEBUG}" ]] && set -x

kill -9 "${TESTY_TUNNEL_PID}"