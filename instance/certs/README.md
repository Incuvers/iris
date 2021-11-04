# Monitor Certs
App authentication is performed entirely at runtime as the containers must be certless when deployed. The certs will exist on the devices local filesystem which will be mounted into the container at runtime. This allows fast swapping of certs for ease of use for devs while also being a required pre-condition for the application.

![img](/doc/img/secret_management.png)