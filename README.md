# Monitor: IRIS Embedded Development
[![ci](https://github.com/Incuvers/iris/actions/workflows/ci.yml/badge.svg)](https://github.com/Incuvers/iris/actions/workflows/ci.yml)
[![deploy](https://github.com/Incuvers/iris/actions/workflows/image.yml/badge.svg)](https://github.com/Incuvers/iris/actions/workflows/image.yml)
![img](/doc/img/Incuvers-black.png)

Updated: 2021-11

## Navigation
1. [Quickstart](#quickstart)
2. [Developers Guide](#developers-guide)
3. [Development Team](#development-team)

## Quickstart
This repository is built and controlled using the Makefile in the root in order to homogenize our dev environments. Run `make help` for more information on the available make targets.

### Authentication
IRIS devices require certificate files to be mounted to `/app/instance/certs` to run successfully. The certificate files must be located [here](instance/certs/README.md) at runtime and include the following:
- [x] amqp.ini
- [x] device.ini

>Please contact <a href="mailto:christian@incuvers.com?">christian@incuvers.com</a> for these files.

### Development Stack
Once the certs are added run the development stack:
```bash
make dev
```

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

## Developers Guide
Welcome to the team. Please see the [developers guide](./dev/README.md) for Incuvers guidelines and best practices.
http://localhost:8080/vnc.html

## Development Team
David Sean (CTO) (david@incuvers.com)\
Christian Sargusingh (christian@incuvers.com)
