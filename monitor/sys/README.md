# System

## Kernel Interfacing

When we use `os.system` calls we route them through `monitor.sys.kernel.os_cmd` to translate the status code architecture into exception driven architecture which the monitor codebase follows. In essence this allows us to properly identify which kernel commands fail and write appropriate handles for those cases.

```python
def os_cmd(cmd:str) -> None:
    """
    Wrapper for executing os.system calls and returning the exit status through OSError.
    NOTE: all os calls should route to this function to homogenize exception handles.

    :param cmd: string of command 
    :raises OSError: if command returns a non-zero exit status
    """
    # save status of os system call
    status = os.system(cmd)
    # calculate exit code (MSB)
    exit_code = os.WEXITSTATUS(status)
    # if exit code is non-zero return an OSError with the errno attribute set
    if exit_code != 0:
        exception = OSError()
        exception.errno = exit_code
        raise exception
```
### Usage

Import the system module and call the `os_cmd` command as you would `os.system`. In your exception handle you can use the `errno` attribute inside the `OSError` object to customize your error handling for different exit status'

```python
from monitor.sys import kernel
...
try:
   kernel.os_cmd("command string here")
except OSError as exc:
    # write exception handle
   self._logger.exception("os command failed with exit status: %s", exc.errno)
```