"""
Power supply interface contains the PPS helper functions,
which can be called from the test cases
"""
from config import peripherals,interfaces
from interface.PowerSupply.PowerSupply import SigilentPowerSupply
from interface.PowerSupply.PowerSupply import UsbPowerSupply
import allure

POWER_SUPPLY_IP = peripherals.get('powersupply', 'ip')
"""IP address to connect with PPS"""
PORT = peripherals.get('powersupply', 'port')
"""PORT to connect with PPS"""
POWER_SUPPLY_CHANNEL = peripherals.get('powersupply','channel')
"""PPS channel Number"""


def __getPowerSupplyObject():
    """
    Gets the power supply object
    Returns: Power supply object

    """
    Ptype = peripherals.get('powersupply', 'type')
    # powersupply_object = None
    if Ptype == "IP":
        powersupply_object = SigilentPowerSupply.getInstance(POWER_SUPPLY_IP)
    if Ptype == "USB":
        powersupply_object = UsbPowerSupply.getInstance(PORT)
    return powersupply_object

def switch_on(channel):
    """
    Switch on the Power supply channel
    Args:
        channel: Channel Number like CH1 or CH2

    Returns: None

    """
    powersupply_object = __getPowerSupplyObject()
    powersupply_object.enable_channel(channel)

def switch_off(channel):
    """
    Switch off the Power supply channel
    Args:
        channel: Channel Number like CH1 or CH2

    Returns: None

    """
    powersupply_object = __getPowerSupplyObject()
    powersupply_object.disable_channel(channel)

@allure.step('Power Supply Volatge set to - "{value}"')
def set_voltage(channel, value):
    """
    Sets the voltage
    Args:
        channel: Power Supply channel
        value: Voltage for Input can be in range of 6 to 15
        set_voltage("CH1",12) To set the 12 Volt on CH! channel

    Returns: None

    """
    powersupply_object = __getPowerSupplyObject()
    powersupply_object.SetVoltage(channel, value)

@allure.step('Power Supply Current set to - "{value}"')
def set_current(channel, value):
    """
    Sets the current
    Args:
        channel: Power Supply channel
        value: current, Input can be in range of 0.5 to 3
        set_voltage("CH1",2) To set the 2 Amp(max current) on CH! channel

    Returns: None

    """
    powersupply_object = __getPowerSupplyObject()
    powersupply_object.SetCurrent(channel, value)

@allure.step('Get Power Supply Voltage ')
def get_voltage(channel):
    """
    Gets the Voltage
    Args:
        channel: Channel Number like CH1 or CH2

    Returns: Voltage value in Volt

    """
    powersupply_object = __getPowerSupplyObject()
    return powersupply_object.GetVoltage(channel)

@allure.step('Get Power Supply Current ')
def get_current(channel):
    """
    Gets the current value in A(ampere)
    Args:
        channel: Channel Number like CH1 or CH2

    Returns: current value in A(ampere)

    """
    powersupply_object = __getPowerSupplyObject()
    return powersupply_object.GetCurrent(channel)

if __name__ =="__main__":
    import time
    print(set_voltage("CH1",15))
    time.sleep(2)
    print(get_voltage("CH1"))
    print(set_voltage("CH1", 12))
    time.sleep(2)
    print(get_voltage("CH1"))