"""
Enum related to software update module are exposed here
"""
from enum import Enum

class Software_Partition():
    """
    Software partitions
    """
    APPKERNEL1 = "00"
    "Variable used to switch ['APPLICATION','LEFT']"
    APPKERNEL2 = "15"
    "Variable used to switch ['APPLICATION','RIGHT']"
    BTLDKERNEL1 = "128"
    "Variable used to switch ['BOOTLOADER','LEFT']"
    BTLDKERNEL2 = "143"
    "Variable used to switch ['BOOTLOADER','RIGHT']"
    APPLICATION = 0
    BOOTLOADER = 1
    LEFT = 0
    RIGHT = 1