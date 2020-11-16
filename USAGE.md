# Usage

## Prerequisites

- `python => 3.8`
- An SSH key on the host machine listed in the remote machine's `~/.ssh/authorized_keys`

## Requirements

    # Create and activate local virtualenv    
    virtualenv -p python3.8 --prompt "(testy) " .venv && source ./.venv/bin/activate

    # Install requirements
    pip install -r requirements.txt

## Running the tests

    REMOTE_URL=http[s]://<MY.MACHINE.IP.OR.HOSTNAME> ./entrypoint.sh
