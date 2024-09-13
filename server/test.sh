#!/usr/bin/env bash
set -ex

if [[ $1 == "--help" ]]; then
    echo "./test.sh --no-db --debug --nox"
    exit
fi

flake8 vitals *.py tests

if [[ $1 == "--no-db" ]]; then
    shift
else
    flask db-reset
    flask db-load-test-data
fi

ARGS="--cov --cov-report html"

if [[ $1 == "--debug" ]]; then
    shift
    ARGS="$ARGS --capture=no --pdb"
fi

if [[ $1 == "--nox" ]]; then
    shift
else
    ARGS="$ARGS --exitfirst"
fi

python3 -m pytest $ARGS "$@"
