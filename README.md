# Monitor: IRIS Embedded Development
[![deployment](https://github.com/Incuvers/monitor/actions/workflows/deploy.yml/badge.svg?branch=master)](https://github.com/Incuvers/monitor/actions/workflows/deploy.yml)
[![build](https://github.com/Incuvers/monitor/actions/workflows/iris.yml/badge.svg)](https://github.com/Incuvers/monitor/actions/workflows/iris.yml)
[![ci](https://github.com/Incuvers/monitor/actions/workflows/ci.yml/badge.svg)](https://github.com/Incuvers/monitor/actions/workflows/ci.yml)
![coverage](/doc/img/coverage.svg)

![img](/doc/img/Incuvers-black.png)

Updated: 2020-11

## Navigation
1. [Quickstart](#quickstart)
2. [Developers Guide](#developers-guide)
3. [Development Team](#development-team)

## Quickstart
This repository is built and controlled using the Makefile in the root in order to homogenize our dev environments. Run `make help` for more information on the available make targets.

### Unittest and Coverage
```bash
make unit
```
Unittest suite for the `monitor` app is located [here](/monitor/tests). This target uses unittest discovery to run the entire test suite. Alternatively you can execute a single test case by referencing the test case name:
```bash
make unit case=<NAME>
```
Where `<NAME>` is the name of the test case by its filename schema: `test_<NAME>.py`. For example the `<NAME>` of `test_cache.py` would be `cache`.

Code Coverage can be performed on the entire unittest suite:
```bash
make coverage
```
or by referencing a specific test case module:
```bash
make coverage case=<NAME>
```
Where `<NAME>` is the name of the test case by its filename schema: `test_<NAME>.py`. For example the `<NAME>` of `test_cache.py` would be `cache`. A cli code coverage report will be generated displaying the coverage per file as well as the lines which have not been covered. The coverage configuration for monitor can be found in the [.coveragerc](/.coveragerc) in root.

### Codebase Linting
```bash
make lint
```
This target requires `yamllint` (all `.yaml` files), `shellcheck` (binaries located under `bin/`)and `flake8` (python app codebase) to be installed and in your `$PATH`. The `yamllint` and `flake8` configuration for monitor can be found in the [.yamllint](/.yamllint) and [.flake8](/.flake8) in root respectively.

### Test CI Build Specs
```bash
make ci
```
This target will build a multipass container for both the linting and unittest suite jobs. The parameters for the containers can be edited in the [.env](/.env) file. This route is recommended for developing on non-Ubuntu platforms to ensure the features are conforment to the production environment and package dependancies.

### Simulated Snap Environment
```bash
make dev
```
This target installs and runs our app in a simulated snap environment by setting `SNAP` runtime environment variables and pointing them to linux directives as if it was run as an `apt` package. You will need a set of credentials to run the app. See the list of required files to be saved in [this](/daemon/ident/serial_certs) directory.

### Build and Install Snap
```bash
make all
```
This will build a `devmode` confined version of our snap using `lxd` container

## Developers Guide
Welcome to the team. Please see the [developers guide](./dev/README.md) for Incuvers guidelines and best practices.

## Development Team
David Sean (CTO) (david@incuvers.com)\
Travis Haycock (travis@incuvers.com)\
Christian Sargusingh (christian@incuvers.com)