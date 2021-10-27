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

## Monitor Cert Files