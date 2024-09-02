#!/usr/bin/env bash
set -ex

if [[ $1 == "--help" ]]; then
    echo "./test.sh --no-db --debug --nox"
    exit
fi

flake8 vitals *.py

flask test-matcher

http --multipart POST http://localhost:5001/api/v1/query_album_match query@queries/what-is-beat.png
