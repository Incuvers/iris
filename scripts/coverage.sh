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

printf "%b" "${OKB}Computing code coverage${NC}\n"
# execute coverage report for case unittests or entire suite
if [ -z "$1" ]; then
    coverage run -m unittest discover -s monitor/tests
    coverage report --skip-empty -m 
    coverage-badge -o doc/img/coverage.svg -f
else
    coverage run -m unittest monitor/tests/test_"$1".py
    coverage report --skip-empty -m | grep "$1"
fi

rm -f .coverage
printf "%b" "${OKG} ✓ ${NC} Pass\n"
