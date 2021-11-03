# -*- coding: utf-8 -*-
"""
System Service Functions
========================
Modified: 2021-07

This file is a collection standalone service (system-level) menu functions which can be accessed by any component.

Dependancies
------------
```
from monitor.environment.state_manager import StateManager
import time
import os
import logging
from typing import Optional
import numpy as np
import monitor.imaging.constants as IC
import uuid
import socket
import fcntl
import struct
from pathlib import Path
from monitor.sys import kernel
from monitor.sys import decorators
from monitor.cloud.mqtt import MQTT
from monitor.arduino_link.sensors import Sensors
from monitor.arduino_link.icb_logger import ICBLogger
from monitor.microscope.microscope import Microscope as scope
from monitor.events.registry import Registry as events
from monitor.flash_service.flash_service import FlashService
from monitor.environment.context_manager import ContextManager
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
from monitor.scheduler.imaging import ImagingScheduler
import time
import os
import logging
from typing import Optional
import numpy as np
import monitor.imaging.constants as IC
import uuid
import socket
import fcntl
import struct
from pathlib import Path
from monitor.sys import kernel
from monitor.sys import decorators
from monitor.cloud.mqtt import MQTT
# from monitor.microscope.microscope import Microscope as scope
from monitor.events.registry import Registry as events
from monitor.scheduler.setpoint import SetpointScheduler
from monitor.environment.state_manager import StateManager
from monitor.environment.context_manager import ContextManager
from monitor.ui.static.settings import UISettings as uis
from monitor.environment.thread_manager import ThreadManager as tm

_logger = logging.getLogger(__name__)


@tm.threaded(daemon=True)
@decorators.splash
def main():
    """
    System boot sequence into monitor app
    """
    try:
        # update system status
        try:
            result = kernel.os_cmd("lsusb")
        except OSError as exc:
            _logger.critical("os command failed with message: %s and exit status: %s",
                             exc.strerror, exc.errno)
        else:
            _logger.info("%s", result)
        events.system_status.trigger(msg="Initializing modules")
        _mqtt = MQTT(device_id=os.environ.get('ID', None))
        SetpointScheduler()
        ImagingScheduler()
        # load runtime models from cache into state manager
        with StateManager() as state:
            state._load_runtime_models()
            device = state.device
            lab_id = device.lab_id
        _logger.info("Lab ID: %s", lab_id)
        # time.sleep(1)
        events.system_status.trigger(msg="Initializing hardware link")
        # time.sleep(1)
        _logger.info("Done!")
        events.system_status.trigger(msg="Loading cloud resources")
        _logger.info("Starting MQTT...")
        _mqtt.start()


    except BaseException as exc:
        _logger.exception(exc)
        events.system_status.trigger(
            status=uis.STATUS_ALERT,
            msg="Contact info@incuvers.com for assistance."
        )
    else:
        _logger.info("main boot successful")


@tm.threaded(daemon=True)
@decorators.load
def service_boot():
    """
    System boot sequence into monitor app
    """
    try:
        # update system status
        try:
            result = kernel.os_cmd("lsusb")
        except OSError as exc:
            _logger.critical("os command failed with message: %s and exit status: %s",
                             exc.strerror, exc.errno)
        else:
            _logger.info("%s", result)
        events.system_status.trigger(msg="Loading servicing assets. Please wait.")
        # create a sink for SENSORFRAME_UPDATED trigger
    except BaseException as exc:
        _logger.exception(exc)
        events.system_status.trigger(
            status=uis.STATUS_ALERT,
            msg="Contact info@incuvers.com for assistance.",
        )
    else:
        _logger.info("Service boot successful")


@tm.threaded(daemon=True)
@decorators.load
def update_snap():
    """
    Update snap using edge channel in devmode
    """
    _logger.info("Updating snap")
    try:
        # update system status
        events.system_status.trigger(msg="Verifying connection status")
        # check the connectivity status to the store
        kernel.os_cmd('sudo snap debug connectivity')
        events.system_status.trigger(msg="Updating system software")
        kernel.os_cmd('sudo snap refresh --channel=edge iris-incuvers --devmode')
    except OSError as exc:
        _logger.critical("os command failed with message: %s and exit status: %s",
                         exc.strerror, exc.errno)
        events.system_status.trigger(
            status=uis.STATUS_ALERT,
            msg="Contact info@incuvers.com for assistance."
        )
    else:
        _logger.info("Software update successful")
        events.system_reboot.trigger()
        events.system_status.trigger(status=uis.STATUS_OK, msg="Rebooting System")


@tm.threaded(daemon=True)
@decorators.load
def factory_reset():
    """
    Resets the incubator to factory settings deleting all the users personal files located
    in COMMON
    """
    _logger.info("Resetting to factory defaults")
    file_list = ['/hostname.txt', '/thumbnail.png', '/device_avatar.png']
    dir_list = ['/dpc_background', '/cache']

    # remove specific files #
    # if they do not exist then report success
    # if they exist delete them then report success
    with ContextManager() as context:
        common = context.get_env('COMMON')

    file_list = list(map(lambda x: common + x, file_list))
    dir_list = list(map(lambda x: common + x, dir_list))
    try:
        events.system_status.trigger(msg="Resetting IRIS to factory defaults")
        # clear top level user files
        # this one will always fail but its ok since some files are directories
        for fp in file_list:
            if Path(fp).exists():
                events.system_status.trigger(msg=f"Clearing user presets: {fp.split('/')[-1]}")
                os.remove(fp)
                _logger.info("file %s removed", fp)
            else:
                _logger.debug("file %s already removed", fp)
        # clear system cache
        # remove all files in listed directories
        for dp in dir_list:
            if Path(dp).exists():
                dp = str(Path(dp))
                if len(os.listdir(dp)) != 0:
                    _logger.info("directory %s has files: %s", dp, os.listdir(dp))
                    for fp in os.listdir(dp):
                        full_path = str(Path(dp).joinpath(fp))
                        events.system_status.trigger(msg=f"Cleaning system cache: {fp}")
                        os.remove(full_path)
                        _logger.info("file %s removed", fp)
                else:
                    _logger.debug("directory %s already empty", dp)
            else:
                _logger.debug("directory %s is removed", dp)
        # clear lab id for this incubator
        events.system_status.trigger(msg="Removing lab identification")
        os.remove(context.get_env('COMMON_CERTS') + 'lab_id.txt')
    except BaseException as exc:
        _logger.exception("Factory reset failed: %s", exc)
        events.system_status.trigger(
            status=uis.STATUS_ALERT,
            msg="Contact info@incuvers.com for assistance."
        )
    else:
        # reset networking
        reset_network()
        # reboot the system
        reboot()


@tm.threaded(daemon=True)
@decorators.load
def reset_network():
    """
    Locates the user netplan yaml file and removes it.
    """
    with ContextManager() as context:
        monitor_netplan = context.get_env('MONITOR_NETPLAN')
    # filter by all netplan files but the default 50-cloud-init template
    netplan_files = list(filter(lambda x: x != '50-cloud-init.yaml', os.listdir(monitor_netplan)))
    try:
        if len(netplan_files) != 0:
            for nf in netplan_files:
                full_path = str(Path(monitor_netplan).joinpath(nf))
                events.system_status.trigger(msg=f"Clearing network config: {nf}")
                os.remove(full_path)
                _logger.info("file %s removed", nf)
        else:
            _logger.debug("directory %s already empty", monitor_netplan)
    except BaseException as exc:
        _logger.exception("Network reset failed: %s", exc)
        events.system_status.trigger(status=uis.STATUS_ALERT, msg="Network reset failed.")
    else:
        _logger.info("Network reset successful.")
        events.system_status.trigger(status=uis.STATUS_OK, msg="Network reset successful")


@tm.threaded(daemon=True)
@decorators.load
def reboot():
    """
    Reboot the system using the dbus to workaround snap confinement
    """
    events.system_status.trigger(msg="Rebooting IRIS")
    events.system_reboot.trigger()


@tm.threaded(daemon=True)
@decorators.load
def shutdown():
    """
    Shutdown the system using the dbus to workaround snap confinement
    """
    # send shutdown command through system dbus
    events.system_status.trigger(msg="Shutting Down IRIS")
    events.system_shutdown.trigger()


@tm.threaded(daemon=True)
@decorators.load
def flash_firmware():
    """
    performs a flash using the hex file within the directory location of the below class 
    """
    try:
        events.system_status.trigger(msg="Applying firmware update")
        _logger.debug("flashing device")
    except FileNotFoundError:
        _logger.exception("Failed to flash ATMEGA2560, file not present")
        events.system_status.trigger(status=uis.STATUS_ALERT,
                                     msg="Firmware not present in current distribution")
    except OSError:
        _logger.exception("Failed to flash ATMEGA2560")
        events.system_status.trigger(status=uis.STATUS_ALERT,
                                     msg="Contact info@incuvers.com for assistance.")
    else:
        _logger.info("Firmware flashed successfully.")
        events.system_status.trigger(status=uis.STATUS_OK,
                                     msg="Firmware update successful")


@tm.threaded(daemon=True)
@decorators.load
def calibrate_co2():
    """
    Just trigger the event
    """
    try:
        events.system_status.trigger(msg="Calibrating your CO\u2082 sensor")
        events.co2_calibration.trigger()
    except BaseException as exc:
        _logger.exception("CO2 calibration failed: %s", exc)
        events.system_status.trigger(status=uis.STATUS_ALERT,
                                     msg="CO\u2082 calibration failed.")
    else:
        _logger.info("CO2 calibration successful")
        events.system_status.trigger(status=uis.STATUS_OK, msg="CO\u2082 sensor calibrated.")


@tm.threaded(daemon=True)
@decorators.load
def calibrate_dpc():
    """
    Scans the full exposure grades and save background images
    """
    try:
        _logger.info("Starting DPC background calibration.")
        events.system_status.trigger(msg="Performing calibration. This may take a while.")
        with ContextManager() as context:
            background_path = context.get_env('COMMON_DPC')
        if not os.path.isdir(background_path):
            os.makedirs(background_path, mode=0o777, exist_ok=True)
        # full exposure grade sweep
        for current_exposure_grade in range(0, 101, 1):
            events.update_progress.trigger(current_exposure_grade)
            events.system_status.trigger(msg="Scanning range {}/100".format(current_exposure_grade))
            # converted exposure time
            exposure_us = IC.dpc_grade_to_exposure(current_exposure_grade)
            fname = f'{background_path}/dpc_{exposure_us}'
            # get current settings as runtime obj
            # apply change and digest
            with StateManager() as state:
                imaging_profile = state.imaging_profile
                imaging_profile.dpc_exposure = exposure_us
                result = state.commit(imaging_profile, cache=False)
                _logger.debug("Exposure change result: %s", result)
            # data = scope.dpc_capture()
            for idx, capture in enumerate([]):
                np.savez_compressed(f'{fname}_{idx}.npz', data=capture.astype(np.uint8))
            _logger.debug("%s exposure saved", exposure_us)
    except BaseException as exc:
        _logger.exception("Phase calibration failed: %s", exc)
        events.system_status.trigger(status=uis.STATUS_ALERT, msg="Background calibration failed.")
    else:
        _logger.info("Phase calibration successful.")
        events.system_status.trigger(status=uis.STATUS_OK, msg="Background calibration successful")


@tm.threaded(daemon=True)
@decorators.load
def temp_benchmark():
    """
    Execute temp. benchmark
    """
    events.start_benchmark.trigger(benchmark_test_type='TEMP')


@tm.threaded(daemon=True)
@decorators.load
def co2_benchmark():
    """
    Execute CO2 benchmark
    """
    events.start_benchmark.trigger(benchmark_test_type='CO2')


@tm.threaded(daemon=True)
@decorators.load
def o2_benchmark():
    """
    Execute O2 benchmark
    """
    events.start_benchmark.trigger(benchmark_test_type='O2')


@tm.threaded(daemon=True)
@decorators.load
def benchmark():
    """
    Execute all benchmarks (temp, co2, o2)
    """
    events.start_benchmark.trigger(benchmark_test_type='FULL')


def test_connection(host: str = "8.8.8.8", port: int = 53, timeout: int = 3):
    """
    Tests internet connectivity
    Test intenet connectivity by checking with Google
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    :param host: (str) the host to test connection
    :param port: (int) the port to use
    :param timeout:
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
    except socket.error:
        return False
    return True


def get_iface_list() -> list:
    """
    Get the list of interfaces
    :return:  ifaces (list) : a list of interface identifiers (string)
    """
    # define the path
    iface_path = Path('/sys/class/net').resolve()
    # parse all paths from interface path
    iface_paths = iface_path.glob("*")
    # if file doesnt exist we skip (ie an empty list means path was not resolved)
    ifaces_dirs = [x for x in iface_paths if x.is_dir()]
    ifaces = list(map(
        lambda x: x.parts[-1], ifaces_dirs
    ))
    if len(ifaces) == 0:
        _logger.warning("No interfaces found in interface path: %s", iface_path)
    return ifaces


def get_iface_hardware_address(_iface: str) -> Optional[str]:
    """
    Get the hardware (MAC) address of the given interface
    :param iface:  iface (str) interface to return the mac off
    :return: str colon-delimited hardware address
    """
    if _iface not in get_iface_list():
        _logger.warning("invalid interface: %s", _iface)
        return None
    try:
        mac = open('/sys/class/net/' + _iface + '/address').readline()
    except OSError:
        _hex = uuid.getnode()
        mac = ':'.join(['{:02x}'.format((_hex >> ele) & 0xff)
                        for ele in range(0, 8 * 6, 8)][::-1])
    return mac[0:17]


def get_ip_address(_iface: str) -> str:
    """
    Get the primary IP address
    :return: (str) standard representation of the device's IP address
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        ip_addr = socket.inet_ntoa(
            fcntl.ioctl(
                sock.fileno(),
                0x8915,  # SIOCGIFADDR
                struct.pack('256s', bytes(_iface[:15], encoding='utf8'))
            )[20:24]
        )
    except OSError:
        ip_addr = "No IP"
    return ip_addr
