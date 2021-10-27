# netplan_config_creator
# Created by Jon York from Sharkbyte for Incuvers
# re-factored and integrated June 2020 by Incuvers Team

import os
import yaml
import logging
from time import sleep
from pathlib import Path 


class NetplanConfig:
    """
    This class is called from the flask webserver when the user enters the provided
    credentials when attempting to connect to the target network and then executes the encapsulated
    logic that updated the appropriate network yaml files and then proceeds to toggle the physical
    wifi radio ( via soft stop ) and then calls the daemon running on our system in the snap context
    see employ connection method below.
    """

    NETPLAN_SYSTEM_FILE = '/60-user-netplan.yaml'

    def __init__(self, ssid=None, password=None):
        """
        :param ssid: network name
        :param password: password associated with the network

        """
        self.ssid = ssid
        self.password = password
        self._logger = logging.getLogger(__name__)
        self._logger.info("Instantiation successful.")

    def employ_connection(self) -> None:
        """
        this method toggles the wifi radio in order to apply the new connection
        instead of a hard reboot of the system
        os command restarts the daemon see more in here  monitor/daemon/netplan
        sleep has been added to ensure the template has been returned to the client
        before executing the netplan apply command - which causes a potential to
        disconnect

        :raises OSError: if the netplan application returns a non-zero exit status code.
        """
        status = os.system('sudo netplan apply')
        if os.WEXITSTATUS(status) != 0:
            raise OSError
        self._logger.debug("Netplan application successful")
        sleep(2.0)

    def create_netplan_config_from_wifi_template(self) -> tuple:
        """
        this method is responsible for loading the template(s) as well as creating the netplan file
        with the ssid and password associated with the network they are attempting to connect to
        """
        netplan_template = str(
            Path(__file__).parent.joinpath('templates/netplan-template-wpa2.yaml')
        )
        try:
            with open(netplan_template, 'r') as file:
                try:
                    config = yaml.safe_load(file)
                except (yaml.scanner.ScannerError, yaml.parser.ParserError) as err:
                    self._logger.error("Unable to open and load the netplan template file %s", err)
                    return False,'Failed to configure the connection file, Please try again.'
            # edit SSID name
            config['network']['wifis']['wlan0']['access-points'][self.ssid] = \
                config['network']['wifis']['wlan0']['access-points']['SSID']
            del config['network']['wifis']['wlan0']['access-points']['SSID']
            # edit SSID password
            config['network']['wifis']['wlan0']['access-points'][self.ssid]['password'] = \
                self.password
        except OSError as err:
            self._logger.exception(
                "Unable to open the netplan template file and edit the credentials: %s", err
            )
            return False, 'Failed to configure the connection file, Please try again.'
        try:
            # save created file in /etc/netplan or the proper location for netplan system files
            with open(os.environ.get('MONTIOR_NETPLAN')+self.NETPLAN_SYSTEM_FILE, 'w') as file:
                yaml.dump(config, file)
            self.employ_connection()
        except OSError as err:
            self._logger.exception(
                "Unable to save the the netplan file in the /etc/netplan system directory %s",
                err
            )
            return False, 'Failed to configure the connection file, Please try again.'
        else:
            return True,'Your entry has been accepted by the system. If your IP address has \
                changed you may not be redirected and will have to re-connect'

    def create_netplan_config_from_upload(self, netplan_file) -> tuple:
        """
        :param netplan_file: netplan file use has uploaded from the front end
        :return: boolean value true if the file was accepted or false if it was not due to an error
            i.e invalid netplan
        config yaml
        """
        # verify that the file is valid yaml and we do not encounter any issues
        try:
            config = yaml.safe_load(netplan_file)
        except yaml.scanner.ScannerError as err:
            self._logger.error(
                "Unable to load the the netplan file due to indentiation or style errors %s", err
            )
            return False,'Please check the netplan file for syntax error(s).'

        except yaml.parser.ParserError as err:
            self._logger.error(
                "Unable to load the the netplan file due to indentiation or style errors %s",
                err
            )
            return False,'Please check the netplan file for syntax error(s).'
        try:
            with open(os.environ.get('MONTIOR_NETPLAN')+self.NETPLAN_SYSTEM_FILE, 'w') as file:
                yaml.dump(config, file)
            self.employ_connection()
        except OSError as err:
            self._logger.exception("Unable to save the the netplan file %s", err)
            return False, 'The system was unable to write to the proper file directory'
        else:
            return True,'Your entry has been accepted by the system. If your IP address has \
                changed you may not be redirected and will have to re-connect'
