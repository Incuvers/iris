import subprocess
import logging.config


class LogRequest:

    def __init__(self):
        self. _logger = logging.getLogger(__name__)
        # used for the filename when the user downloads
        self.selected_log = None

    def get_log(self, cmd: str, log_type: str) -> str:
        """
            provides the mechanism in which we run the command and obtain the desired target logs

           :param cmd: command string for the subprocess function to run
           :param log_type: log type name as a string to set the global field state
           :return: contents of the target log as a string
        """
        command = subprocess.run(cmd, shell=True,stdout=subprocess.PIPE)
        self.set_selected_log(log_type)
        return command.stdout.decode()

    def set_selected_log(self, requested_log: str) -> None :
        """
            setter that is used to define the log name

           :param requested_log: setter or the requested log to set the global field state
           :return: None
        """
        self.selected_log = requested_log

    def get_selected_log(self) -> str:
        """
            getter that is used to obtain the target log name

           :return: selected log name called when flask serves the log file
         """
        return self.selected_log
