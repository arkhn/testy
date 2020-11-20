# Usage

## Quickstart

### Prerequisites

- an Arkhn's stack deployed with in the `test` env, either locally or remotely.

### Run

The available configuration settings can be seen in the repo [`docker-compose.yml`](./docker-compose.yml) (provided for the development).

The settings must be overriden depending on the target stack and context.

For instance, the most simple case would be to run the tests directly from the stack host, using the stack network.

#### With docker

    docker run \
        --network=STACK_NETWORK
        -e MONGO_PASSWORD=whatever \
        arkhn/testy:latest

where:

- `STACK_NETWORK` is the docker network in which the stack has been deployed.
- `MONGO_PASSWORD` is the password for the default user.

#### With docker-compose

For more complex context, use a compose file.

    docker-compose run testy
