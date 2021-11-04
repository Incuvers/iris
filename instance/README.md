# Instance Environment Variables

## Unittesting
The monitor environment requires environment variables to run. This is handled automatically by the `unit` make target:
```bash
make unit
```

The tests can be invoked directly against the unittest module as well. We just need to source the `ci.env` file:
```bash
source ./instance/ci.env
python3 -m unittest monitor.tests.test_mqtt -v
```

# Development
## Monitor Cache

## Monitor Certs
App authentication is performed entirely at runtime as the containers must be certless when deployed. The certs will exist on the devices local filesystem which will be mounted into the container at runtime. This allows fast swapping of certs for ease of use for devs while also being a required pre-condition for the application.

![img](/doc/img/secret_management.png)