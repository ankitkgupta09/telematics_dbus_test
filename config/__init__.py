"""
All the configuration and constant variables are kept inside the config folder
"""
try:
    # noinspection PyCompatibility
    import configparser as configparser
except Exception as e:
    # noinspection PyCompatibility
    import ConfigParser as configparser
import os
import time
import pytest
import logging
import sys

location = os.path.abspath(os.path.dirname(__file__))
LOGPATH = os.path.join(location, '..\\Log\\')
"""Log folder path"""
config_path = os.path.join(location, 'config.cfg')
config = configparser.ConfigParser()
"""handler for the config can be used in test case to read any value from config.cfg
Example: - \n
from config import config \n
config.get('SECTION','VARIABLE')
"""
config.read(config_path)

interfaces_path = os.path.join(location, 'interfaces.cfg')
interfaces = configparser.ConfigParser()
"""handler for the interfaces can be used in test case to read any value from interfaces.cfg
Example: - \n
from config import interfaces \n
interfaces.get('SECTION','VARIABLE')"""
interfaces.read(interfaces_path)

peripherals_path = os.path.join(location, 'peripherals.cfg')
peripherals = configparser.ConfigParser()
"""handler for the peripherals can be used in test case to read any value from peripherals.cfg
Example: - \n
from config import peripherals \n
peripherals.get('SECTION','VARIABLE')"""
peripherals.read(peripherals_path)

board_path = os.path.join(location, 'board.cfg')
board = configparser.ConfigParser()
"""handler for the board can be used in test case to read any value from board.cfg
Example: - \n
from config import board \n
peripherals.get('SECTION','VARIABLE')"""
board.read(board_path)

CURRENT_TIME_STAMP = time.ctime().replace(" ", "_").replace(":", "_")
"""Variable can be used to append current timestamp in logs"""

L1 = pytest.mark.L1
"Pytest Marker for L1 test"
L2 = pytest.mark.L2
"Pytest Marker for L2 test"
L3 = pytest.mark.L3
"Pytest Marker for L3 test"
stability = pytest.mark.stability
"Pytest Marker for stability test"
KPI = pytest.mark.KPI
"Pytest Marker for KPI test"
under_development = pytest.mark.under_development
"Pytest Marker for Testing"
ETH_CONNECTION_TIMEOUT = 30
"Wait time for ETH to up"

logger = logging.getLogger('test_logger')
"""logger can be used in Lib and Test case"""
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(LOGPATH+"/exection_logs.log", mode='w')
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(module)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
handler1 = logging.StreamHandler(sys.stdout)
formatter1 = logging.Formatter('%(asctime)s - %(funcName)s - %(module)s - %(message)s')
handler1.setFormatter(formatter1)
logger.addHandler(handler1)

if 'nt' == os.name:
    WINDOWS = True
else:
    WINDOWS = False