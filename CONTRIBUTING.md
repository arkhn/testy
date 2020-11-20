# Contributing

## Quickstart

### Create a dedicated virtualenv

    virtualenv -p python3.8 --prompt "(testy) " .venv && source .venv/bin/python

If using `vscode`, make sure this interpreter is selected.
Else, activate the virtualenv.

    source .venv/bin/activate

### Install dev requirements

    pip install -r requirements/dev.txt

### Install precommit hooks

    pre-commit install

All set.

## Advanced

### Validating the tests

With the right setup, it is possible to run the tests while developing them.

#### Set the configuration settings

Tests can be configured using a dotenv file.

Edit a `.env` file the project root directory.

#### Validate the test

    pytest
