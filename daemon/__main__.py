# -*- coding: utf-8 -*-
"""
Daemon __main__
================

Dependancies
------------
```
import logging
import os
from daemon.ident.identity import Identity
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import logging.config
import os
import sys
import time

from daemon.ident.identity import Identity

# NOTE: Not implemented for beta units
def factory_issuer():
    # unconditionally shutdown the system once the serial certs are dumped
    # if the serial certs were not dumped properly during the connect to ident host this could
    # cause the system to continously shutdown. We need some mechanism to indicate to the factory
    # workers whether the fetch was successful or not. Furthermore we need a built in validation
    # mechanism for those certs for quality control.
    logger.info("No serial certs detected. Connecting to identity server ...")
    try:
        ident.connect_identhost()
    except (ConnectionError) as exc:
        logger.exception("Daemon encountered an error when trying to connect to identity server: %s", exc)
        time.sleep(.3)
    else:
        logger.info("Successfully saved serial certs.")
        return

def boot_handler():
    """ When things go horribly wrong. 
        Attempt to make things repairable.
    """
    # set hostname
    status = os.system('set-hostname')
    err = os.WEXITSTATUS(status)
    if err != 0:
        logger.critical("set-hostname binary failed with exit status: %s", err)
    else:
        logger.debug("set-hostname succeeded.")

    # host-ap
    status = os.system('host-ap')
    err = os.WEXITSTATUS(status)
    if err != 0:
        logger.critical("host-ap binary failed with exit status: %s", err)
    else:
        logger.debug("host-ap succeeded.")
    sys.exit(1)

# basic console logger for factory
logger = logging.getLogger(__name__)

logger.info("Initiating daemon identity issuer")

# Ident daemon must be active on main thread since its success defines whether monitor should start
# successfully or not
try:
    ident = Identity()
except BaseException as exc:
    logger.critical("An uncaught exception occured when initializing the identity service: %s", exc)
    boot_handler()

if os.environ['IDENTITY_ENV'] == 'production':
    try:
        ident.update_aws_cert()
        validation = ident.verify_certs()
    except BaseException as exc:
        logger.exception("An uncaught exception occured when validating AWS certificate: %s", exc)
        boot_handler()
    else:
        if not validation:
            logger.critical("Certification validation checks failed.")
            factory_issuer()
        else:
            logger.info("Certification validation checks succeeded. Booting into monitor.")
else:
    # devmode
    ident.update_aws_cert()
    ident.update_certs()
# set hostname generates and saves hostname.txt in $SNAP_COMMON
status = os.system('set-hostname')
err_code = os.WEXITSTATUS(status)
if err_code != 0:
    logger.critical("set-hostname binary failed with exit status: %s", err_code)
else:
    logger.debug("set-hostname succeeded.")
