#!/bin/bash

source .env

# handle all non-zero error status codes
trap 'handler $? $LINENO' ERR

handler () {
    # print error message and propagate error status
    if [ "$1" != "0" ]; then
        printf "%b" "${FAIL} ✗ ${NC} Failed with status: $1 on line: $2\n"
        exit "$1"
    fi
}

printf "%b" "${OKB}Executing unittest suite${NC}\n"
# execute case unittests or entire suite
if [ -z "$1" ]; then
    python3 -m unittest discover -v -s monitor/tests
else
    python3 -m unittest -v monitor/tests/test_"$1".py
fi

printf "%b" "${OKG} ✓ ${NC} Pass\n"
