#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Sensors
=======
Modified: 2021-04

Dependencies:
-------------
```
import time
import serial
import logging
import binascii
from datetime import datetime, timezone
from monitor.environment.thread_manager import ThreadManager as tm
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""
import time
import serial
import logging
import binascii
from typing import Dict, Union
from threading import Condition

from monitor.models.icb import ICB
from monitor.events.registry import Registry as events
from monitor.environment.state_manager import StateManager
from monitor.environment.thread_manager import ThreadManager as tm


class Sensors:

    SETPOINT_TIMEOUT = 5    # setpoint timeout
    CC_TIMEOUT = 10         # CO2 calibration timeout

    def __init__(self, serial_port: str):
        self._logger = logging.getLogger(__name__)
        # thread condition variables
        self._setpoint_condition = Condition()
        self._cc_condition = Condition()
        # set verbosity=1 to view more
        self.verbosity = 1
        self.buffer = {}
        # register events
        events.co2_calibration.register(self.send_co2_calibration_time)
        events.aux_duty.register(self.queue_buffer)
        events.op_mode.register(self.queue_buffer)
        events.fan_duty.register(self.queue_buffer)
        # subscribe isv
        with StateManager() as state:
            state.subscribe_isv(ICB, self.validator)
        try:
            self.serial_connection = serial.Serial(
                port=serial_port,
                baudrate=9600,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                xonxoff=False,
                rtscts=False,
                dsrdtr=False,
                timeout=5.0
            )
        except (serial.SerialException, FileNotFoundError) as exc:
            self._logger.critical("Failed to create interface to IRIS motherboard: %s", exc)
            self.serial_connection = None
        self._logger.info("Instantiation successful.")

    @tm.threaded(daemon=True)
    def monitor(self) -> None:
        """
        ICB runtime interface loop. Processes sensorframe and request buffer values.
        """
        while True:
            try:
                line = self.serial_interface()
            except (serial.SerialTimeoutException, serial.SerialException) as exc:
                self._logger.exception("Arduino connection lost: %s", exc)
            else:
                # validate the sensorframe checksum
                if self._validate_checksum(line):
                    # parse arduino message
                    try:
                        sensorframe = self._parser(line)
                    except ValueError as exc:
                        self._logger.exception("Sensorframe parse failed: %s", exc)
                    else:
                        # validate kvp against buffer
                        self._update_accepted_sensorframe(sensorframe)
                        self._update_state(sensorframe)
            # report request buffer
            self._logger.info("Request Buffer: %s", self.buffer)
            # DO NOT REMOVE (used for unittest mocking)
            time.sleep(0.1)

    @tm.lock(tm.arduino_lock)
    def serial_interface(self) -> str:
        """
        Send pending command strings and read a new sensorframe line

        :return: decoded sensorframe line from serial monitor
        :rtype: str
        """
        if self.serial_connection is None:
            raise serial.SerialException
        # generate command strings from buffer if available
        if len(self.buffer) > 0:
            cmd_str = self._process_requests(self.buffer)
            self._logger.debug("Generated command string: %s", cmd_str)
            self.serial_connection.write(str.encode(cmd_str))
            self.serial_connection.flush()
        # read new sensorframe from serial monitor
        line = ""
        try:
            line = self.serial_connection.readline().decode()
        except UnicodeDecodeError as exc:
            self._logger.exception("Arduino log line: %s decode failed with %s", exc, line)
            line = ""
        return line

    def _validate_checksum(self, msg: str) -> bool:
        """
        Check if the checksum passed recompute message checksum and compares with appended hash
        :param msg: (str) a string containing the message, having the following format:
        Len~CRC32$Param|Value&Param|Value

        :return: `True` when `msg` passes the checksum, `False` otherwise
        """
        if not len(msg) > 0:
            self._logger.debug("Message string empty")
            return False
        # pop the Len
        sub_msg = msg.split('~')
        if len(sub_msg) != 2 or sub_msg[0] == '' or sub_msg[1] == '':
            self._logger.debug("Corrupt message: while splitting with special character ~ ")
            return False
        # pop the Crc
        sub_msg = sub_msg[1].rstrip().split('$')
        if len(sub_msg) != 2 or sub_msg[0] == '' or sub_msg[1] == '':
            self._logger.debug("Corrupt message: while splitting with special character $ ")
            return False
        # convert crc string to hex
        msg_crc, msg = int(sub_msg[0], 16), sub_msg[1].rstrip()
        # compare CRC32
        calc_crc = binascii.crc32(msg.rstrip().encode('utf-8')) & 0xffffffff
        if calc_crc == msg_crc:
            self._logger.info("CRC32 checksum passed for: %s", msg)
            return True
        self._logger.warning(
            "CRC32 Fail: calculated: %s but received: %s", format(calc_crc, 'x'), format(msg_crc, 'x'))
        return False

    def _parser(self, msg: str) -> Dict[str, Union[str, int]]:
        """
        Takes the serial output from the incubator and creates a dictionary
        using the two letter ident as a key and the value as a value.

        :param msg: (str) The raw serial message (including the trailing checksum)
        :return: dict sensorframe
        """
        # pop the Len and CRC out
        sub_msg = msg.split('$')
        msg = sub_msg[1].rstrip()
        sensorframe = {}
        # the message begins with an item delimeter so remove the first one
        for params in msg.split('&')[1:]:
            kvp = params.split("|")
            if len(kvp) != 2 or kvp[0] == '' or kvp[1] == '':
                # check and log malformed key value pairs
                self._logger.warning(
                    "Detected malformed key-value pair in message string for %s", params)
                continue
            icb_key, icb_value = kvp
            if icb_key in ['TP', 'CP', 'OP', 'TC', 'OC', 'CC', 'RH', 'CT', 'TM', 'CM', 'OM', 'FP', 'FC', 'HP',
                           'HC', 'OPT1', 'TO']:
                sensorframe[icb_key] = int(icb_value)
            elif icb_key == 'CTR':
                sensorframe[icb_key] = float(icb_value)
            elif icb_key == 'IV':
                sensorframe[icb_key] = icb_value
        return sensorframe

    def _update_state(self, sensorframe: dict) -> None:
        """
        Convert sensorframe dict to system state change

        :param sensorframe: sensorframe dict
        :type sensorframe: dict
        """
        with StateManager() as state:
            icb = state.icb
            payload = {
                "tp": icb.int_to_float(sensorframe['TP']),
                "tc": icb.int_to_float(sensorframe['TC']),
                "cp": icb.int_to_float(sensorframe['CP']),
                "cc": icb.int_to_float(sensorframe['CC']),
                "op": icb.int_to_float(sensorframe['OP']),
                "oc": icb.int_to_float(sensorframe['OC']),
                "rh": icb.int_to_float(sensorframe['RH']),
                "fp": sensorframe['FP'],
                "fc": sensorframe['FC'],
                "hp": sensorframe['HP'],
                "tm": sensorframe['TM'],
                "cm": sensorframe['CM'],
                "om": sensorframe['OM'],
                "ctr": sensorframe['CTR'],
                "iv": sensorframe['IV'],
                "to": sensorframe['TO'],
                "ct": icb.calibration_time_to_iso(sensorframe['CT']),
                "timestamp": icb.generate_timestamp()
            }
            icb.setattrs(**payload)
            # do not trigger validators
            state.commit(icb, source=True)

    def _update_accepted_sensorframe(self, int_sensorframe: dict) -> None:
        """
        Matches the int sensorframe values to converted buffer
        """
        accepted = list()
        # looping over the buffered items instead of the sensorframe is significantly more efficient
        for buffer_key, buffer_value in self.buffer.items():
            self._logger.debug("Validating update for buffer item %s: %s", buffer_key, buffer_value)
            # perform conversion to sensors against sensorframe value
            if buffer_value == int_sensorframe[buffer_key]:
                accepted.append(buffer_key)
            else:
                self._logger.debug(
                    "Buffer entry %s:%s not been processed according to converted sensorframe value %s",
                    buffer_key, buffer_value, int_sensorframe[buffer_key]
                )
        # remove accepted in seperate loop to avoid modifying the length of the iteratable
        for buffer_key in accepted:
            val = self.buffer.pop(buffer_key)
            self._logger.info("Removed %s: %s from buffer", buffer_key, val)
            if buffer_key == 'CT':
                with self._cc_condition:
                    self._cc_condition.notify_all()
                    self._logger.debug("calibration time CT accepted by icb")
        # check if all setpoint conditions have been satisfied
        if not any(k in self.buffer for k in ('TP', 'OP', 'CP', 'FP', 'HP', 'TM', 'OM', 'CM')):
            self._logger.debug("All setpoints accepted by arduino")
            with self._setpoint_condition:
                self._setpoint_condition.notify_all()

    def validator(self, candidate: ICB) -> bool:
        """
        Validate proposed setpoint changes

        :param candidate: proposed setpoint changes
        :type candidate: ICB
        :return: validation result
        :rtype: bool
        """
        # compare deltas against current state
        with StateManager() as state:
            icb = state.icb
            tp = icb.tp
            cp = icb.cp
            op = icb.op
            hp = icb.hp
            fp = icb.fp
            tm = icb.tm
            om = icb.om
            cm = icb.cm
        # check for co2 delta
        if cp != candidate.cp or cm != candidate.cm:
            state = False
            # check if setpoint delta
            if cp != candidate.cp:
                self.queue_buffer('CP', candidate.float_to_int(candidate.cp))
            if cm != candidate.cm:
                self.queue_buffer('CM', candidate.cm)
                state = True
            # trigger appropriate gauge loading view depending on state/setpoint outcome
            events.co2_loader.trigger(state)
        # check for o2 delta
        if op != candidate.op or om != candidate.om:
            state = False
            # check if setpoint delta
            if op != candidate.op:
                self.queue_buffer('OP', candidate.float_to_int(candidate.op))
            if om != candidate.om:
                self.queue_buffer('OM', candidate.om)
                state = True
            # trigger appropriate gauge loading view depending on state/setpoint outcome
            events.o2_loader.trigger(state)
        # check for temp delta
        if tp != candidate.tp or tm != candidate.tm:
            state = False
            # check if setpoint delta
            if tp != candidate.tp:
                self.queue_buffer('TP', candidate.float_to_int(candidate.tp))
            if tm != candidate.tm:
                self.queue_buffer('TM', candidate.tm)
                state = True
            # trigger appropriate gauge loading view depending on state/setpoint outcome
            events.temp_loader.trigger(state)
        if fp != candidate.fp:
            self.queue_buffer('FP', candidate.fp)
        if hp != candidate.hp:
            self.queue_buffer('HP', candidate.hp)
        # block until setpoint condition is triggered
        with self._setpoint_condition:
            result = self._setpoint_condition.wait(timeout=self.SETPOINT_TIMEOUT)
        return result

    def queue_buffer(self, param: str, value: Union[float, int]) -> None:
        """
        Adds a parameter to the update queue, the updates will be sent
        at a later time. If this update follows another requested update,
        overwrite it.  The item will remain in the queue until the action
        has been verified

        :param param: (str) the identifier of the parameter to update
        :param value:  the value of the parameter to update
        """
        # check if the key is valid
        # TODO: if the value is invalid the arduino will never accept it causing the value
        # stay in the buffer indefinitely
        if param in ['TP', 'CP', 'OP', 'CT', 'HP', 'FP', 'TM', 'CM', 'OM']:
            # add to buffer
            self.buffer[param] = value

    def send_co2_calibration_time(self) -> None:
        """
        Epoch time stamp generated from service menu controller of assumed calibration time
        this function contains all the required actions to actually send the command string to the Arduino and
        is located in this function because of the special use case of the co2 calibration action

        :raises TimeoutError: if the buffer key 'CT' has not been updated due to arduino value acceptance
        """
        self._logger.debug("Updating co2 caibration timestamp")
        # checkout icb to access conversion functions
        with StateManager() as state:
            icb = state.icb
        self.queue_buffer('CT', icb.generate_co2_calibration_time())
        # add polling backoff to validate the calibration time has been accepted by the arduino
        with self._cc_condition:
            result = self._cc_condition.wait(timeout=self.CC_TIMEOUT)
        if not result: raise TimeoutError

    @ staticmethod
    def _process_requests(buffer: dict) -> str:
        """
        Convert buffer value requests into icb command strings and send through the serial monitor.

        :param buffer: snapshot of request buffer
        :type buffer: dict
        :return: arduino command string representation of request buffer
        :rtype: str
        """
        command_string = ""
        for param in buffer:
            if (len(command_string) + len(param) + len(str(buffer[param])) + 2) <= 80:
                if len(command_string) > 0:
                    command_string = command_string + "&"
                command_string = command_string + param + "|" + str(buffer[param])
        cs_length = len(command_string)
        command_string = command_string + "\r"
        # 0xFFFFFFFF truncates to 8-digits
        crc_int = binascii.crc32(command_string.encode()) & 0xFFFFFFFF
        # pad with zeroes in case it's less than 8 characters
        crc_str = "{0:08x}".format(crc_int)
        # now generate the full string
        command_string = str(cs_length) + "~" + crc_str + "$" + command_string + "\n"
        return command_string
