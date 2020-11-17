# Usage

## Prerequisites

- `python => 3.8`
- An SSH key on the host machine listed in the remote machine's `~/.ssh/authorized_keys`

## Requirements

    # Create and activate local virtualenv
    virtualenv -p python3.8 --prompt "(testy) " .venv && source ./.venv/bin/activate

    # Install requirements
    pip install -r requirements.txt

## Quickstart

### Setup the environment

    FHIRSTORE_PASSWORD=MY_LITTLE_SECRET source setup.sh HOST_IP SSH_IDENTITY_FILE

where:

* `MY_LITTLE_SECRET` is the mongo password
* `HOST_IP` is the remote host ip or fqdn
* `SSH_IDENTITY_FILE` is the private ssh key listed in the remote `~/.ssh/authorized_keys`

### Run the tests

    pytest -svv

### Teardown the environment

    ./teardown.sh
