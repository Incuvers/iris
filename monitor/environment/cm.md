# Context Manager Design Pattern
The `ContextManager` (CM) provides every module underneath the `app/monitor/` level hierarchy the context of the runtime environment. The CM also performs the ability to perform system checks to validate the systems state during system initialization and the ability for various modules to have divergent code based on the runtime context. Furthermore the CM provides a builtin set of security features to protect access to unsafe methods and environment variable modification which can compromise the system runtime execution.

## Objectives
The priorities of the CM can be summarized by the numbered list below:
1. Validate the system state during system initialization based on select buisness requirements
2. Provide a runtime context for all `app/monitor/` level modules
3. Enable the ability to unittest all modules in isolated environments from `2.`
4. Provide a fundamental level of system security by restricting access to unsafe libraries and methods and monitoring environment variables in real-time.
5. Simple to use, concise interfacing policy with CM for developers
6. Provide descriptive and concise logging details to monitor the runtime environment.
7. Platform for selective integration tests (to be implemented)

## Environment Registration
Environment registration determines the state of the system based on the current environment variable context. The seperation is based on the system runtime requirements where each permutation of 1 2 3 has different buisness logic against 4 and 5. The 5 main system runtime environments are described below:
1. Unittest Environment
2. Integration Test Environment
3. Production Environment
----
4. RPi Environment 
5. Desktop Environment

Again all these distinguishments are neccessary since, for example, an integration test on a desktop requires different setup than an integration test executed on the RPi etc..
### Unittest Environment
```
FLASK_ENV = Undefined
```
We define the unittest environment as any environment not run in the `FLASK` context. This includes running scripts, unittests etc...

### Integration Test Environment
```
FLASK_ENV = development
```
We define the integration test environment as any environment run in the `FLASK` context with the development tag. In essence any runtime instance executed from:
```
./app/runwebserver-dev.sh
```

### Production Environment
```
FLASK_ENV = production
```
We define the production environment as any environment run in the `FLASK` context with the production tag. This system runtime is only valid if the following command is executed from within the `SNAP` context, on a linux OS and on the ARM64 architecture:
```
./app/runwebserver.sh
```

### RPi Environment
```python
platform.processor() == "aarch64"
```
RPi's use an `ARM64` processor which corresponds to `aarch64`. For the purposes of identification I believe this is sufficient because we are trying to distinguish the runtime platforms of the RPi and our desktop computers. `ARM` processors are generally used in systems less powerful than your modern laptop.
### Desktop Environment
```python
platform.processor() != "aarch64"
```
Our desktops are unlucky to ever have an `ARM64` processor powering them.

The environment registration is done by CM's `register()` method. This method is designed to be called exactly once in any given runtime instance. The code is shown below:
```python
def register(self):
    """
    Registers the os environment variables by generating a hash of the environment variables,
    and pushing it to the environment variables. This registration should only be called at the
    top level system __init__. This is a one time function call for a system runtime instance.
    """
    # verify caller id is registered to perform env registration
    if not self.REGISTERED_MODULES.get(self.caller_id):
        self._logger.warning(
            "Revoked unregistered caller %s permissions to register environment",
            self.caller_id)
        raise OSError
    if 'registration' not in self.REGISTERED_MODULES.get(self.caller_id):
        self._logger.warning(
            "Revoked unregistered caller %s permissions to register environment",
            self.caller_id)
        raise OSError

    # for double monitor/__init__ calls
    if os.environ.get('ENV_HASH'):
        self._logger.warning("Environment already registered. Passing..")
        return

    # determine the system state for context
    self._set_state()

    # verify lauch platform for first time registration
    if os.environ['unit']:
        # allow unittests to be performed on macos and linux distros
        if sys.platform != 'linux' and sys.platform != 'darwin':
            self._logger.critical("Unittests not supported on non-linux/non-darwin machine.")
            raise OSError
        # set display environment variables if on the RPi
        if os.environ['rpi']:
            self._set_display_env()
    elif os.environ['dev']:
        # integration tests can be on linux or macos
        if sys.platform != 'linux' and sys.platform != 'darwin':
            self._logger.critical("System not supported on non-linux OS.")
            raise OSError
        # enter first time environment configuration
        self._configure_env()
    elif os.environ['prod']:
        # real system always must be linux
        if sys.platform != 'linux':
            self._logger.critical("System not supported on non-linux OS.")
            raise OSError
        # enter first time environment configuration
        self._configure_env()
    # create / register with environment hash
    self._logger.info("Verified launch platform OS.")
    os.environ['ENV_HASH'] = self._get_env_hash()
    self._logger.info(
        "Created first-time environment registration hash from %s", self.caller_id)
```
There is alot to unpack here. First we verify that the caller id is a registered module and that it is allowed to execute registration by referencing the `REGISTERED_MODULES`. Second, we ensure that the environment registration is not performed more than once. Next we set the system state based on the current environment variables (aformentioned). These states are pushed to the environment variables to protect against runtime modification (more on this below). Now we perform a top level system check on the operating system for each system state. In `unit` and `dev` we allow darwin and linux systems to execute the app since we perform unittests and integration tests on both systems. For `prod` however we only allow linux systems to execute the app in that context. Furthermore we ensure that on the rasberry pi architeture we enable the display environment variables. `configure_env()` is executed for `prod` and `dev` system states:
 - For `dev` we want to setup a permenant set of `SNAP` environment variables if outside of the snap context.
 - For `prod` we want to validate the `SNAP` environment variables exist and that we are running on the RPi platform. If not we need to stop the runtime instance.

Once these checks and environment setup is complete, we lock-in the environment variables by hashing the current set of environment variables and pushing it to a new environment variable named `ENV_HASH`. This hash is verified during every new CM entry to validate that these system variables have not been modified during runtime.

Environment registration is executed at `app/monitor/__init__.py`. This is caller instance is defined by `ContextManager.REGISTERED_MODULES` dictionary and therefore can only be registered from the `app.monitor` context (not including unittesting modules):
```python
# defines module permissions to access specified os methods
REGISTERED_MODULES = {
     'app.monitor':"registration",
     'app.monitor.arduino_firmware_flash_service.flash_service': [os.system]
}
```
Registration is very simple and is executed as shown below:
```python
from app.monitor.environment.context_manager import ContextManager
...
ContextManager().register()
```

## Using ContextManager
The CM should be used whenever we have an execution divergence which depends on the runtime context. The formatting for using the context manager in any module is shown below:
To use the context manager
```python
from app.monitor.environment.context_manager.py import ContextManager
...
with ContextManager() as context:
   ...
```

When the execution enters the `with` block the `__init__` followed by the `__enter__` method within the CM is executed. When the `with` block is left the `__exit__` method is called. The `__init__` registers its logger instance and identifies the caller id for logging and restricted access validation:
```python
def __init__(self):
    # bind logging configuration to config file 
    self._logger = logging.getLogger(__name__)
    # determine caller id for logging info
    self.caller_id = inspect.getmodule(inspect.stack()[1][0]).__name__
    self._logger.info("Context manager entered from %s", self.caller_id)
```

The `__enter__` method must return a CM instance when complete for access to CM methods. First the method checks if the environment has been registered if not it raises `OSError`. Next it verifies no environment variable modification has been perfomed between this method being executed and the environment registration by comparing the current environment hash against the saved environment hash. If the hashes are different we know that the environment has been modified since registration and we raise an `OSError`. Finally for unittest runtimes, we create a virtual set of `SNAP` environment variables which exist only within the `with` block to allow methods executed in the unittest context to have a virtualized pointer to paths that we desire for the unittest context.

```python
def __enter__(self):
    self._logger.debug(os.environ)
    # verify the environment has been registered (self.reg)
    if os.environ.get('ENV_HASH') is None:
        self._logger.error("Environment not registered!")
        raise OSError
    # compare the enviornment hash to ensure the environment has not been modified
    if self.compare_hash():
        self._logger.info("Context successfully registered from %s", self.caller_id)
    else:
        # otherwise raise
        self._logger.critical(
            "Context registeration failed. Environment variable modification detected during runtime.")
        raise OSError
    # configure state after entry checks for environment modification.
    if os.environ['unit']:
        self._configure_venv()
    return self
```

Finally the `__exit__` method cleans up the virtual environment variables for the unittest runtime only:
```python
def __exit__(self, exc_type, exc_val, exc_tb):
    """
    Remove temporary environment variables (if any)
    """
    if os.environ['unit']:
        self._restore_env()
```

Within the `with` block we can perform two main functions:
1. get the system runtime context
2. perform operations involving the `os` library

### Get Runtime Context
```python
get_state()
```
This is the most common use of the CM. We generally will use this to diverge execution between unittest runs, integration test runs, production runs and runs on the RPi/desktop.

For example, the UI main menu can have two additional buttons `exit` and `reboot` which are available only during development modes and not during the production runtime:
```python
# only provide these menu options in the development environment
with ContextManager() as context:
    if context.get_state('unit') or context.get_state('dev'):
        self.main.add_option('Reboot', self._call_reboot)
        self.main.add_option('Exit', events.PYGAME_MENU_EXIT)
```

### OS level operations
```python
get_os_cmd()
```
This method removes the need for other modules to `import os` and execute unsafe methods that can compromise the system integrity. We use this method to safeguard the `os` method access through the `REGISTERED_MODULES` internal database within the CM:
```python
REGISTERED_MODULES = {
    'app.monitor': ["registration"],
    'app.monitor.test.test_context_manager': ["registration"],
    # added for unittest discover since it launches in a different context
    'test_context_manager': ["registration"],
    'app.monitor.arduino_firmware_flash_service.flash_service': [os.system],
    'app.monitor.ui.main_menu': [os.system]
}
```
We can see here that `flash_service` and `main_menu` have permissions to access `os.system`. As a note, it is insecure to hold this database inside the CM object since it can be modified by any module that imports the CM. In the future we plan on saving this data to the environment variables to protect its modification by the environment hash. Furthermore we plan on blacklisting the use of `os` throughout the system except through the CM using this method.

For example, the UI main menu requires the ability to reboot the system if the reboot option is selected. Instead of granting the ability to execute kernel level operations to any module we hold the `os` level methods inside context manager and bind the permissions to its own internal `REGISTERED_MODULES` database. If the caller id matches that of the `REGISTERED_MODULES`, `get_os_cmd()` returns a list of `os` methods that module is permitted to execute. In the example below `app.monitor.ui.main_menu` is registered to use `os.system` and so the method is returned by `get_os_cmd()`.
```python
def _call_reboot(self):
    """
    :action: when activated this will reboot the system
    """
    with ContextManager() as context:
        context.get_os_cmd()('sudo reboot')

```