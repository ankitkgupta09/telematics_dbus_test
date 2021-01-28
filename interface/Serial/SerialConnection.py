import platform
import serial
import time
import serial.tools.list_ports
from serial.serialutil import SerialBase
from config import logger,interfaces

def check_comport_in_config_file(configuration):
    com_port = interfaces.get(configuration, 'COM_PORT_ID')
    if com_port == '':
        return False
    return True

def check_if_login_screen(serial_connection, configuration):
    time.sleep(2)
    serial_connection.flushOutput()
    serial_connection.flushInput()
    serial_connection.write("\r\n".encode('utf-8'))
    time.sleep(5)
    # console_output = serial_connection.read_all().decode()
    console_output = str(serial_connection.read_all())
    if " login" in console_output:
        logger.info("Login required entering username")
        serial_connection.write((interfaces.get(configuration, 'username') + "\r\n").encode('utf-8'))
        time.sleep(1)
        output = serial_connection.read_all().decode('utf-8')
        if "#" in output:
            logger.debug("Login to TCU successful")
        serial_connection.flushOutput()

class SerialConnection():
    class __SerialConnection(SerialBase):
        def __init__(self, configuration):
            self.configuration = configuration
            com_port_value = check_comport_in_config_file(configuration)
            self.port_name = None
            if com_port_value == True:
                autodetect = False
            else:
                autodetect = True

            if autodetect:
                if "Linux" in platform.platform():
                    serial_port = interfaces.get(configuration, 'Linux_FHE')
                else:
                    serial_port = interfaces.get(configuration, 'Windows_FHE')
                ports = list(serial.tools.list_ports.comports())
                for p in ports:
                    if serial_port in str(p):
                        #print p
                        self.port_name = p.device
                        #print self.port_name
                self.baud_rate = interfaces.get(configuration,'baud_rate')
                self.time_out = int(interfaces.get(configuration,'timeout', vars={'timeout' : '30'}))
                self.serial_connection = serial.Serial(port=self.port_name, baudrate=self.baud_rate, timeout=self.time_out)
            else:
                self.port_name = interfaces.get(configuration, 'COM_PORT_ID')
                self.baud_rate = interfaces.get(configuration, 'baud_rate')
                self.time_out = int(interfaces.get(configuration, 'timeout', vars={'timeout': '30'}))
                self.serial_connection = serial.Serial(port=self.port_name, baudrate=self.baud_rate, timeout=self.time_out)
    instance = None

    def __init__(self, configuration):
        if not SerialConnection.instance:
            SerialConnection.instance = SerialConnection.__SerialConnection(configuration)

    def __getattr__(self):
        return getattr(self.instance)

    def read_boot_messages(self):
        #delimiter = 'Reached target multi-user'
        boot_message = SerialConnection.instance.serial_connection.read(int(interfaces.get("serial", "boot_buffer_size")))
        #print "boot_message = \n", boot_message
        return boot_message

    def get_serial_connection(self):
        if SerialConnection.instance.serial_connection.isOpen():
            check_if_login_screen(SerialConnection.instance.serial_connection, SerialConnection.instance.configuration)
            time.sleep(5)
        return SerialConnection.instance.serial_connection