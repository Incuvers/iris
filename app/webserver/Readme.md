#Flask Webserver

## installing requirements
for some reason pip kept on breaking, I had to run --upgrades between installing the packages
The following is not EXACTLY what I  didn't, but it's pretty much sums up the required workflow

```
pip3 install MarkupSafe
pip3 install --upgrade requests
pip3 install Flask-Bootstrap
pip3 install --upgrade requests
pip3 install flask-nav
pip3 install --upgrade urllib3
pip3 install setuptools
pip3 install --upgrade urllib3
pip3 install wifi
pip3 install --upgrade urllib3
```

## serving

to test it, got to the root of the /monitor directory and run:
```./runwebserver.sh```
use a different computer and navigate to ```http://10.1.53.10:5000/network``` (where of course you replace with the IP ofthe RPi).
=======
Flask Webserver

### Spin up the GUI
## making the classes accessible
For some reason the flask app cannot access stuff outside it's directory.
**As a hack**, I just copied over the directories: `monitor/ui`, `monitor/rotary_encoder` and `monitor/arduino_link` into the flask app directory: `monitor/webserver/ui`, `monitor/webserver/rotary_encoder` and  `monitor/webserver/arduino_link` respectively.

## prevent two flask instances
By default flask is started twice, this means we will start two GUIs and they will fight for the framebuffer operations (and also the serial connection). Edit the `/monitor/runserver.sh` script so that the command is:
```python3 -m flask run -h '0.0.0.0' --no-reload```

## fix the paths
the files: `config.py`, `device.py` and `main.py` have file references that will have a broken path.
I fix this using absolute paths using the `___file__` variable.
make sure to include `import os` and change:
- in `config.py`
```FONT_PATH = "{}/fonts/DroidSansFallback.ttf".format(os.path.dirname(os.path.realpath(__file__))) ```
- in `main.py` (near line 255)
```device_info = Device(480, 100, "Incubator Name", pygame.image.load('{}/logo.png'.format(os.path.dirname(os.path.realpath(__file__)))))```
- in `device.py` (near line 80)
```mask = pygame.image.load("{}/mask.png".format(os.path.dirname(os.path.realpath(__file__)))).convert_alpha()```

## create the instance!
To get the gui to start with the flask server, add this in the `webserver/__init__.py`
```
from flask import Flask
from flask_bootstrap import Bootstrap
from .nav import nav, init_custom_nav_renderer
from .ui.main import UserInterfaceController
ui=UserInterfaceController() # <-- create it!
```
and an instance will start up. 
**note this will block unless it's created on a separate thread.**

