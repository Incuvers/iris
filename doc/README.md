# Incuvers Developers Guide
Updated 2020-08

## Navigation
1. [Guidelines](#guidelines)
2. [Development](#development)
3. [Packaging](#packaging)
4. [Git Contribution Standards](#gitflow)
5. [Testing](#unittests)
6. [Documentation](#inline-code-documentation)

## Guidelines
### Code Readability
During a sequence of method calls (especially during `__init__`) it is common to see chained method calls where each method is called by the previous method.
```python
class Sample:
   def __init__(self):
      self.first()

   def first(self):
      # do some stuff
      self.second(stuff)

   def second(self. stuff):
      # do some stuff
      self.third(stuff)
...
```
This implementation is hard to follow and can allow for errors to seep their way into startup sequences. Furthermore this can cause debugging headaches since the stack traces would include the entire sequence of methods rather than just the one that broke. Instead, I think we should have the starting method in the sequence of method calls (`__init__` in this case) be the master and guide the passing of information through each method as shown below:
```python
class Sample:
   def __init__(self):
      foo = self.first()
      bar = self.second(foo)
      # do some foo stuff
      self.third(foo)

   def first(self):
      # do some stuff
      return stuff

   def second(self, stuff):
      # do some stuff
      return stuff
...
```
This is much easier to read because it contains the methods called during the init and isolates each method in the sequence. This makes it very clear during debugging which specific method failed and caused the error. This can be applied to any other sequential method calls. 

A common occurence in our code base is assigning the `EventHandler` to an object's attribute then passing it into other methods. A snippet from `ProtocolHandler` demonstrates this guideline in action:
```python

import logging.config

from monitor.scheduler.setpoint import Setpoint
from monitor.protocol.layers import ProtocolLayers

class ProtocolHandler:

    def __init__(self, event_handler):
        self._logger = logging.getLogger(__name__)
        self.event_handler = event_handler
        # initialize layers
        layers = ProtocolLayers(event_handler)
        # intialize scheduling channels
        self.exp_channel = Setpoint(self.event_handler, layers, priority=0)
        self.usr_channel = Setpoint(self.event_handler, layers, priority=1)
        self._logger.info("Instantiated successfully")
```

## Development

## Getting Started
After cloning Incuvers:monitor navigate to the root of the repository and validate that your `pwd` has no whitespaces. This will cause `cp` executions to fail as a result of formatting.

### MacOSX
1. Install `pygame` from source:
```bash
brew install sdl2 sdl2_gfx sdl2_image sdl2_mixer sdl2_net sdl2_ttf pkg-config;
```
Go to site-packages:
For virtual environment go to cd `~/.virtualenvs/myvirtualenv/lib/python3.X/site-packages` where `~/.virtualenvs/myvirtualenv` is the path to your virtual environment and `python3.X` is the version of your Python.
For system-wide installation go to `/usr/local/lib/python3.X/site-packages` where `python3.X` is the version of your Python.
Delete any previous pygame
```bash
python -m pip uninstall pygame
```
Clone PyGame from GitHub:
```bash
git clone https://github.com/pygame/pygame.git
```
We want the latest (non-stable version)
Go into the newly cloned pygame directory: 
```bash
cd pygame;
python setup.py -config -auto -sdl2;
```
Finally install the package:
```bash
python setup.py install
```
2. Clone `Incuvers/monitor:develop` in your `$HOME` directory:
```bash
cd ~
git clone https://github.com/Incuvers/monitor
```
3. Install the iris python dependancies:
```bash
python -m pip install -r requirements.txt
```

4. In order to execute the app in development or production you are required to have a set of certification files we call *serial certs*. These files are listed [here](/daemon/ident/serial_certs/readme.md). On request you will be provided these credentials by David Sean. Once these serial certs are obtained you will need to move them into `daemon/ident/serial_certs`:
```bash
cd serial_certs
cp ./*.* "$HOME"/monitor/daemon/ident/serial_certs
```

1. Execute monitor from root:
```bash
make dev
```

This command will install our package locally as root as a python package and execute monitor in the dev environment. The package comes with a number of commands found in `bin`. We want to run these as root since our production app will be run as a daemon service. Note that on MacOSX the permissions command will return errors since it requires `wiringpi` to be installed and gpio pins
to be accessible in `/sys`. This can be ignored.

### Ubuntu Server 20.04 on RPi
1. See our [installation guide](./fresh-install.md) for setting up the 20.04 image for development runtime.

### Notes
In order to homogenize the dev environments between MacOSX and Ubuntu 20.04 I have opted to store runtime logs in a new directory under `/var/log/iris/logs` as per [FHS](https://www.pathname.com/fhs/pub/fhs-2.3.html#USRLOCALLOCALHIERARCHY) recommendations. During production in the snap context the logs will be stored in `$SNAP_DATA` which resolves to `/var/snap/iris/{revision}`.

## Packaging
`iris/README` and `iris/setup.py` are present to explain and install our software, respectively.
1. Name the root directory the same as your distribution name. In our case our app name is `iris` in the snap store and as a python application. 
2. When we do releases, we should include a version number suffix: `iris-0.1.1`.
3. `monitor/bin` contains our binary executables which are exposed to the user. Ensure the binaries have the appropriate shebang and have no file extensions.
4. For python package entry binaries keep the format simple:
```bash
#!/bin/bash

# environment setup
export IDENTITY_SERVER_IP=7.7.7.7
export IDENTITY_SERVER_PORT=8624
export IDENTITY_ENV=dev

# entry
python3 -m daemon
```

1. Avoid placing code in a directory called src or lib. This makes it hard to run without installing.
2. Avoid coming up with magical hacks to make Python able to import your module or package without having the user add the directory containing it to their import path (either via PYTHONPATH or some other mechanism). You will not correctly handle all cases and users will get angry at you when your software doesn't work in their environment.

## Git

### Workspaces
This repository is optimized for use with vscode's workspaces. The `monitor.code-workspace` file in the root defines the development environment in order to homogenize and standardize all work. To get started, when opening this repository in vscode a prompt will appear in the bottom right about the code workspace. Alternatively you can open the `monitor.code-workspace` directly and click the blue 'Open Workspace' button on the bottom right  After you open the repository as a workspace your environment will be configured.
> Please also install all the recommended extensions for the workspace.

The workspace file is source controlled and therefore should not be modified by individuals. Your local IDE settings can be tuned via `settings.json` and will extend the `.code-workspace` settings. It is also recommended that you change your python path in the bottom left corner and select your python environment for this project.


### Git flow
[Gitflow](https://www.atlassian.com/git/tutorials/comparing-workflows/gitflow-workflow) is a standardized way of naming and managing branches.

In the majority of situations one will start with `develop` (`git checkout develop`), create a feature branch `feature-myidea` `git checkout -b feature-myidea`, and once done create a pull request back towards `develop`.


## PEP8
https://www.python.org/dev/peps/pep-0008/

Use the tool `autopep8` (`autopep8 -i badly_formatted_file.py`), or configure your IDE to use use `autopep8` when saving (careful, this can sometimes be annoying since it can---in some cases---break your code).

## Naming Conventions
1. `snake_case.py` for filenames; all lowercase with underscores.
2. `snake_case` for variables and other python constructs
3. `class PascalCase()`  for classes, Capitals to separate words.

## Unittests
Unittests are placed in a sub-package of the package they are testing. Of course, make it a package with `monitor/test/__init__.py`. Place subsequent tests in files like `monitor/test/test_event_handler.py`. Avoid placing unittests outside of the Python package they belong to. This makes it hard to run the tests against an installed version.For example `monitor/tests` are tests belonging to the `monitor` package. 

The following examples are unittests applied to the `monitor` package. Since the `tests/` directory is a package, a single test within that package can be exeucted from root: 
``` bash
python3 -m unittest monitor/test/test_tis_camera.py
```
Alternatively, the entire test suite can be executed:
``` bash
python3 -m unittest discover -s monitor/tests
```

## Inline Code Documentation
[Docstrings](https://sphinx-rtd-tutorial.readthedocs.io/en/latest/docstrings.html) are are bits of text inserted in the source-code near class and method definitions.

These bits documents arguments, objects returned, errors that can be thrown and what the code does. Using Sphinx, these `docstrings` can be compiled in a single, great looking, hyper-linked, and searchable documentation. Not to mention the source-code itself becomes much more readable as well.

See the example class below :

```python
class MyClass():
  """
  [Summary]

  :param [ParamName]: [ParamDescription], defaults to [DefaultParamVal]
  :type [ParamName]: [ParamType](, optional)
  ...
  :raises [ErrorType]: [ErrorDescription]
  ...
  :return: [ReturnDescription]
  :rtype: [ReturnType]
  """

  def barf(self, number=0):
    """ 
    Just barfs back the number
    
    :param number: just a number, defaults to 0
    :type number: an integer, but no one is checking
    :return: the same number
    """

    pass
```
