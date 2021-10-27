#!/usr/bin/python3
"""
Ident
=====
Modified: 2020-08

Dependencies:
-------------
```
import os
import socket
import sys
import zipfile
from pathlib import Path
import hashlib
import yaml
```
Copyright © 2021 Incuvers. All rights reserved.
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
"""

import os
import socket
import zipfile
import json
import hashlib
import logging
from pathlib import Path


# NOTE: need to watch for usage of paths based on cwd!

class Identity:

    ident_host = os.environ['IDENTITY_SERVER_IP']
    ident_port = int(os.environ['IDENTITY_SERVER_PORT'])
    ident_env = os.environ['IDENTITY_ENV']
    common_path = os.environ['SNAP_COMMON']
    serial_certs = {
        '/cert_arn.txt',
        '/cert_id.txt',
        '/certificate.pem.crt',
        '/id.txt',
        '/private.pem.key',
        '/public.pem.key',
        '/uuid.txt',
        '/access_key_id.txt',
        '/secret_access_key.txt',
        '/hardware.env'
    }

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        if self.ident_port > 65535 or self.ident_port < 1024:
            raise ValueError
        # Do not give execution permissions to any user on files in this directory.
        # Here we ensure the common path directory exists specifically for our dev environment
        # which points to /etc/iris/
        self.certs_path = self.common_path + '/certs'
        # create certs directory for both production and dev environments
        os.makedirs(self.certs_path, mode=0o666, exist_ok=True)

    def update_aws_cert(self):
        """
        Update and replace AmazonRootCA1.pem in $SNAP_COMMON if a diff is detected between it and
        the AmazonRootCA1.pem file in ./aws

        :raises FileNotFoundError: if required AmazonRootCA1.pem is missing from ./aws
        """
        common_pem_path = self.certs_path + '/AmazonRootCA1.pem'
        ident_pem_path = str(Path(__file__).parent.joinpath('aws/AmazonRootCA1.pem'))
        ident_md5 = self.md5_hash(ident_pem_path)
        # ensure the system has a local aws pem file. Otherwise apply the pem shipped with the SNAP
        try:
            common_md5 = self.md5_hash(common_pem_path)
        except FileNotFoundError:
            self._logger.warning("AmazonRootCA1.pem file was missing from SNAP_COMMON. Copying \
                AmazonRootCA1.pem file from identity.")
            status = os.system("cp {} {}".format(ident_pem_path, common_pem_path))
            err_code = os.WEXITSTATUS(status)
            if err_code != 0:
                self._logger.critical("AmazonRootCA1.pem cp failed with status code: %s", err_code)
            else:
                self._logger.debug("AmazonRootCA1.pem cp succeeded.")
        else:
            # compare the local aws pem file against the one shipped in the SNAP
            # if there is a diff update the local aws pem with the SNAP copy
            if ident_md5 != common_md5:
                self._logger.info("Detected a difference in AmazonRootCA1.pem file in SNAP_COMMON \
                    and identity. Copying AmazonRootCA1.pem file from identity.")
                status = os.system("cp {} {}".format(ident_pem_path, common_pem_path))
                err_code = os.WEXITSTATUS(status)
                if err_code != 0:
                    self._logger.critical(
                        "AmazonRootCA1.pem cp failed with status code: %s", err_code)
                else:
                    self._logger.debug("AmazonRootCA1.pem cp succeeded.")

    def update_certs(self):
        """
        NOTE: This is only called in daemon dev mode >> fast serial cert injection for mocking
        production runtime.

        Iteratively check all the expected contents within SNAP_COMMON. If a file(s) is missing from
        SNAP_COMMON we add it to SNAP_COMMON from the daemon/ident/serial_certs directory. If the
        file does not exist in daemon/ident/serial_certs raise an error and exit

        :raises FileNotFoundError: if required file is missing from daemon/ident/serial_certs
        """
        # if certification validation fails manually copy serial certs from ~/monitor/dev/SNAP_COMMON
        if not self.verify_certs():
            for cert in self.serial_certs:
                dev_sc = "/home/ubuntu/monitor/dev/SNAP_COMMON/certs"
                self._logger.debug("Copying %s to %s ...", dev_sc + cert, self.certs_path + cert)
                os.system("cp {} {}".format(dev_sc + cert, self.certs_path + cert))

    def verify_certs(self) -> bool:
        """
        Ensure all serial certification files are present and not empty. Monitor depends on these
        files being present and not empty for expected operation.

        :returns bool: True if all serial certs are validated; False otherwise
        """
        for cert in self.serial_certs:
            try:
                with open(self.certs_path + cert) as f:
                    if len(f.readlines()) == 0:
                        exc_message = "Certification {} is empty".format(cert)
                        raise IOError(exc_message)
            except IOError as exc:
                if cert != '/hardware.env':
                    self._logger.exception(
                        "Unable to verify file: %s due to file IO exception: %s", cert, exc)
                    return False
                else:
                    self._logger.warning("No hardware.env file found")
        return True

    @staticmethod
    def md5_hash(file_path: str) -> str:
        """ File hashing helper function for module logger unittests. """
        _hash = hashlib.md5()
        with open(file_path, 'rb') as _file:
            _bytes = _file.read(65536)  # The size of each read from the file
            while len(_bytes) > 0:
                _hash.update(_bytes)
                _bytes = _file.read(65536)
        return _hash.hexdigest()

    # NOTE: Not implemented on the beta platform
    def connect_identhost(self):
        """
        Method fetches serial_certs zip file from identity server and saves it to this working
        directory, extracts it and deletes the remaining .zip file.

        :raises ConnectionError: if a socket error is caught
        """
        # we connect with the server script via socket, and send a short message to as a handshake and
        # initiate all the work on the server script. We then receive a zipfile containing a text file
        # with id and associated certificates and extract them.
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.settimeout(10)
            try:
                sock.connect((self.ident_host, self.ident_port))
            except socket.gaierror as exc:
                raise ConnectionError from exc
            except socket.error as exc:
                raise ConnectionError from exc
            except socket.timeout as exc:
                raise ConnectionError from exc
            try:
                eth0_addr = open('/sys/class/net/eth0/address').readline()
                wlan0_addr = open('/sys/class/net/wlan0/address').readline()
            except OSError:
                eth0_addr = ''
                wlan0_addr = ''
            message = json.dumps({
                'id': 'NEW',
                'eth0': eth0_addr.rstrip(),
                'wlan0': wlan0_addr.rstrip()})
            sock.send(message.encode('utf-8'))
            data = sock.recv(1024)
            # Create variable with snap path
            zip_path = str(Identity.common_path) + '/serial_certs.zip'
            zip_extract_path = self.certs_path
            serial_certs = open(zip_path, 'wb+')
            while data != bytes(''.encode()):
                serial_certs.write(data)
                data = sock.recv(1024)
            serial_certs.close()
        finally:
            sock.close()  # type: ignore
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall((zip_extract_path))
            self._logger.warning("unzipped cert contents in: %s", zip_extract_path)
        os.remove(zip_path)
