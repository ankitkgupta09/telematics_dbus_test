"""
USB relay interface which can be called inside the test cases
"""
from interface.Relay.RelayClass import Relay
import allure
import time
import logging
logger = logging.getLogger('test_logger')

@allure.step("Wakeup Interrupt send")
def Relay_ON_OFF(RelayID, relay_pin_01, relay_pin_02):
    """
    Functions exposed to send a wakeup interrupt to TCU using relay board
    Args:
        RelayID: Relay ID, which can be find using relay application
        relay_pin_01: Relay PIN number which is connected to interrupt source
        relay_pin_02: Interrupt needs to be shot to "GND or VCC"
    Returns: None
    """
    relay_pin_01 = int(relay_pin_01)
    relay_pin_02 = int(relay_pin_02)
    # time.sleep(3)
    R = Relay(RelayID, CloseAllRelay=True)
    R.openChannel(relay_pin_01)
    time.sleep(1)
    R.openChannel(relay_pin_02)
    time.sleep(1)
    R.closechannel(relay_pin_01)
    time.sleep(1)
    R.closechannel(relay_pin_02)

@allure.step('Short: "{relay_pin_01}", to "{relay_pin_02}"')
def Relay_ON(RelayID, relay_pin_01, relay_pin_02, CloseAllRelay=True):
    """
    Turn on a 2 particular relays on relay board
    Args:
        RelayID: Relay ID which needs to be controlled.
        relay_pin_01: Relay 1 which you need to control
        relay_pin_02: Relay 2 which you need to control
        CloseAllRelay: By default True
                    if True --> Turn off all the relay PINS
                    if False --> No effect
    Returns: None
    """
    relay_pin_01 = int(relay_pin_01)
    relay_pin_02 = int(relay_pin_02)
    time.sleep(1)
    R = Relay(RelayID, CloseAllRelay)
    R.openChannel(relay_pin_01)
    time.sleep(2)
    R.openChannel(relay_pin_02)

def Relay_OFF(RelayID, relay_pin_01, relay_pin_02):
    """
    Turn off 2 particular relay
    Args:
        RelayID: Relay ID which needs to be controlled.
        relay_pin_01: Relay Number which needs to be Turn off
        relay_pin_02: Second Relay Number which needs to be Turn off

    Returns: None

    """
    relay_pin_01 = int(relay_pin_01)
    relay_pin_02 = int(relay_pin_02)
    time.sleep(1)
    R = Relay(RelayID)
    R.closechannel(relay_pin_01)
    time.sleep(2)
    R.closechannel(relay_pin_02)

if __name__ =="__main__":
    # print(Relay_OFF('HAR37',3,4))
    # R = Relay('HAR37')
    # relay_device = R.get_relay_info()
    Relay_OFF('HAR95',1,2)
    Relay_OFF('HAR95', 3, 4)