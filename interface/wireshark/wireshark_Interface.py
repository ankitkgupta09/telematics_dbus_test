"""
Wireshark log capturing functions
"""
from config import LOGPATH,CURRENT_TIME_STAMP
import os
from multiprocessing import Process
import time
import logging
import platform
logger = logging.getLogger("test_logger")

class ip_logs(object):
    """
    IP log capture
    Args:
        interface: tshark interface ID or interface Name. To list of all the interfaces \
                   run --> tshark -D
        filename: Log file name, file name will be appender by time stamp and *.pcap
    """
    def __init__(self,interface, filename):
        self.interface = interface
        "Interface used in IP log capture"
        self.filename = LOGPATH + filename + CURRENT_TIME_STAMP + ".pcap"
        "File Name given to the log file"

    def _start_ip_capture(self):
        """
        Start capturing The IP packet
        Returns: None
        """
        if 'Windows' in platform.architecture()[1]:
            cmd = "tshark -i {} -w {}".format(self.interface, self.filename)
        else:
            cmd = "sudo tshark -i {} -w {}".format(self.interface, self.filename)
        logger.debug("Log capturing started --> {}".format(os.system(cmd)))

    def start_ip_capture_async(self):
        """
        Start capturing The IP packet into another Thread this function will not block the execution.
        Returns: None
        """
        self.log_started = Process(target=self._start_ip_capture, args=())
        self.log_started.daemon = True
        if not self.log_started.is_alive():
            self.log_started.start()

    def stop_ip_logs(self):
        """
        Stop the log capturing
        Returns: None
        """
        logger.debug("Stop the IP log capture")
        self.log_started.terminate()


if __name__ =="__main__":
    obj = ip_logs(5,"out")
    obj.start_ip_capture_async()
    time.sleep(50)
    obj.stop_ip_logs()
    print("Done")