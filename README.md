# `testy`

## Requirements

- python >= 3.6
- An SSH key on the host machine listed in the remote machine's `~/.ssh/authorized_keys`

## Dependencies

```
pip install -r requirements.txt
```

## Running integration tests

This repository contains integration test to be run against a live Arkhn's stack.

```sh
REMOTE_URL=http[s]://<MY.MACHINE.IP.OR.HOSTNAME> ./entrypoint.sh
```
