# -*- coding: utf-8 -*-
import time
import serial
import logging

from monitor.environment.thread_manager import ThreadManager as tm


class ICBLogger:
    def __init__(self, serial_port: str) -> None:
        self._logger = logging.getLogger(__name__)
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
    def start(self) -> None:
        """
        Logging loop loop. Process serial data as logging calls.
        """
        while self.serial_connection is not None:
            try:
                line = self.serial_connection.readline()
            except (serial.SerialTimeoutException, serial.SerialException) as exc:
                self._logger.exception("Arduino connection lost: %s", exc)
            else:
                try:
                    log_msg = line.decode('utf-8')
                except UnicodeDecodeError as exc:
                    self._logger.exception("Arduino log line: %s decode failed with %s", exc, line)
                else:
                    self._logger.info(log_msg)
            # DO NOT REMOVE (used for unittest mocking)
            time.sleep(0.1)
