"""
Serial Function are exposed from SerialInterface which can be called from the test case
"""
import platform
import re

from serial.tools import list_ports
import time
from config import interfaces,logger
from interface.Serial.SerialConnection import SerialConnection


def find_serial_port():
    """
    Find the Serial COM port connected.
    Returns: COM port number

    """
    port_number = 0
    if "Linux" in platform.platform():
        serial_port = interfaces.get('serial', 'Linux_FHE')
    else:
        serial_port = interfaces.get('serial', 'Windows_FHE')
    ports = list(list_ports.comports())
    for p in ports:
        if serial_port in str(p):
            port_name = str(p.device)
            port_number = str(re.findall('\d+', port_name)[0])
    assert port_number != 0, "Not able to find the FHE port, Check if FHE is connected"
    return port_number

def get_serial_connection(type_of_connection):
    logger.debug("opening serial connection of type -- {}".format(type_of_connection))
    serial_connection = SerialConnection(type_of_connection).get_serial_connection()
    return serial_connection

def execute_command_over_serial(cmd):
    serial = get_serial_connection("serial")
    serial.flushInput()
    serial.flushOutput()
    time.sleep(1)
    # serial.write(cmd.encode() + '\r\n')
    serial.write(('{} \r\n'.format(cmd)).encode())
    time.sleep(1)
    output = serial.read_until('#', size=9999).decode('utf-8')
    logger.debug("OUTPUT is -- {}".format(output))
    # output = output.split('\n')
    # serial.close()
    if len(output) > 1:
        logger.debug("Serial connection is up and running")
        return output
    else:
        logger.debug("Serial connection is disabled")
        return False

if __name__ == "__main__":
    print(execute_command_over_serial("pwd"))
