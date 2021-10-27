#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Arduino
=======
Modified: 2020-12

Dependencies:
-------------
```
import os
import subprocess
from app.webserver.flask_hardware_interface import FlaskHardwareInterface
from flask import (
    Blueprint, render_template
)
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import os
import subprocess
from app.webserver.flask_hardware_interface import FlaskHardwareInterface
from flask import (
    Blueprint, render_template
)

bp = Blueprint('arduino', __name__, url_prefix='/')


@bp.route('/details', methods=('GET', 'POST'))
def details():
    iface = FlaskHardwareInterface()
    system_details = {
        'Model': 'IRIS',
        'Hardware': 'Raspberry Pi 4 1GB + IRIS board 2.23',
        'Ethernet MAC': iface.get_iface_hardware_address('eth0'),
        'Wlan': iface.get_iface_hardware_address('wlan0'),
        'IP Address': iface.get_ip_address('wlan0'),
        'Host name': os.uname()[1],
        'Internet connection': iface.connects_to_internet(),
        'IRIS ID': os.environ.get('ID')
    }
    try:
        access_points = subprocess.check_output('iwgetid -r', shell=True).decode('ascii')
        if access_points != 255:
            system_details['Access Point'] = access_points
    except subprocess.CalledProcessError:
        system_details['Access Point'] = 'Currently unable to scan for access points'

    del iface
    return render_template('details.html', details=system_details)
