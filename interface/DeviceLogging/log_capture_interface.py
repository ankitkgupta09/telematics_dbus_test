from __future__ import print_function
import os
import threading
import time

from config import interfaces, interfaces_path,LOGPATH
from gta_release.generic_libs.interfaces.dlt import DltLib

log_folder = interfaces.get('logging', 'location')
from datetime import datetime
# from interface.VSPE.VSPE import VSPE
# from interface.Serial.SerialInterface import find_serial_port

from interface.utils import remove_process,TCU_IP

out_port = interfaces.get('logging', 'logging_port')
execution_port = interfaces.get('logging', 'execution_port')

# os.system('taskkill /im dlt_viewer.exe')
location = os.path.dirname(os.path.abspath(__file__))

script_options = {
    "-dlt": dict(help="make dlt logging enable"),
    "-Serial": {"help": "Capture Serial logs"},
    "-filename": dict(type=str, default="LogFile",
                      help="log file name for capture"),
    "-dlt_stop": dict(help="make dlt logging enable"),
    "-serial_stop": {"help": "Capture Serial logs"},
}


def write_port_for_execution():
    """
    Writes the virtual Serial port in the configuration file
    """
    interfaces.set('Serial', 'COM_PORT_ID', "COM" + execution_port)
    with open(interfaces_path, "w+") as configfile:
        interfaces.write(configfile)


def set_execution_port_as_null():
    """
    Sets the virtual Serial port to EMPTY (NULL)
    """
    interfaces.set('Serial', 'COM_PORT_ID', '')
    with open(interfaces_path, "w+") as configfile:
        interfaces.write(configfile)


class DeviceLogger(object):
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if DeviceLogger.__instance is None:
            DeviceLogger()
        return DeviceLogger.__instance

    def __init__(self):
        if DeviceLogger.__instance is not None:
            raise Exception("This class is a singleton!")
        DeviceLogger.__instance = self

    def dltlogcapture(self, filename):
        """
        Capture the dlt logs
        Args:
            filename: File to save the dlt log

        Returns: None

        """
        self.dlt_logs = DltLib(TCU_IP)
        self.dlt_logs.start_dlt_log(LOGPATH, file_name=filename)
        # filename = filename + ".dlt"
        # open(filename, 'w+').close()
        # cmd = 'dlt_viewer.exe -p ' + location + '\dlt_configuration.dlp -l ' + filename
        # print(cmd)
        # ret = os.system(cmd)
        # print(("return status is: %s", ret))

    # def serial_capture(self):
    #     self.startVSPE()
    #     print("Serial port capture")
    #     cmd = "ttpmacro.exe " + location + "\\serial_logger.ttl " + str(out_port)
    #     os.system(cmd)

    # def startVSPE(self):
    #     In_port = find_serial_port()
    #     VSPE_obj = VSPE.getInstance()
    #     VSPE_obj.createdevice(str(In_port), str(out_port))
    #     VSPE_obj.createdevice(str(out_port), str(execution_port))
    #     VSPE_obj.start_emulation()
    #     print("VSPE started You can use Virtual ports now")
    #     write_port_for_execution()
    #
    # def stopVSPE(self):
    #     VSPE_obj = VSPE.getInstance()
    #     VSPE_obj.stop_emulation()
    #     print("VSPE Stop")
    #     set_execution_port_as_null()

    def _parser_options(self):
        import argparse
        parser = argparse.ArgumentParser(add_help=False)
        for arg, options in script_options.items():
            parser.add_argument(arg, **options)
        args = vars(parser.parse_known_args()[0])
        if args is None:
            print("NO args pass for the run function")
            return
        print(args)
        if args["filename"]:
            self.filename = args["filename"] + "_" + time.ctime()
            # self.filename = args["filename"] + "_" + time.ctime()
            self.filename = self.filename.replace(" ", "_")
            self.filename = self.filename.replace(":", "_")
            self.filename = location + '\\..\Logs\\' + self.filename

        if args["dlt"]:
            self.process_id_dlt = self.dlt = threading.Thread(target=self.dltlogcapture, args=(self.filename,))
            print("value of dlt is ", self.dlt.ident)
            print("value of process_id is ", self.process_id_dlt)
            self.dlt.daemon = False
            self.dlt.start()

        # if args["Serial"]:
        #     self.process_id_Serial = Serial = threading.Thread(target=self.serial_capture, args=())
        #     print(self.process_id_Serial)
        #     Serial.daemon = False
        #     Serial.start()

        if args["dlt_stop"]:
            self.dlt_close()

        if args["serial_stop"]:
            self.serial_close(self.filename)

    def dlt_close(self):
        print("Closing dlt logging")
        self.dlt_logs.stop_dlt_log()

    # def serial_close(self, filename):
    #     print("closing Serial logging")
    #     current_time_stamp = datetime.today().strftime(r'%Y%m%d_%H%M%S')
    #     list = ['ttpmacro.exe', 'ttermpro.exe']
    #     remove_process(list)
    #     time.sleep(2)
    #     self.stopVSPE()
    #     # filename = filename +"_"+current_time_stamp
    #     # destination = location+"\\..\\Logs\\"+filename+".log"
    #     destination = self.filename + ".log"
    #     print(destination)
    #     file_path = log_folder + "\BMW_logs.log"
    #     print(file_path)
    #     if os.path.exists(destination):
    #         os.remove(destination)
    #         time.sleep(2)
    #     os.rename(file_path, destination)
    #     # os.rename(os.path.join(str(log_folder), "BMW_logs.log"), os.path.join(location, filename))
    #     # os.rename("C:\Logs\BMW_logs.log", "C:\Logs\BMW_logs_1.log")


if __name__ == '__main__':  # pragma: no cover
    logger_object = DeviceLogger()
    logger_object._parser_options()
