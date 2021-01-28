"""
VSPE is a VIRTUAL SERIAL PORT EMULATOR
This file is to create a Virtual Serial port

"""
import logging
import sys

import pythoncom
import win32com.client

logger = logging.getLogger("test_logger")

activationKey = 'Pt8RUh7mhcUVs0bztg1v1Oue/4SxVoJTc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46Ag4sM8c0iWtju3d1/ITLDuQSn8YFj1+LG4Y9KVQSBWquMAZlWqHYVIXytRRLMfgAhtoUvDrq7XeHNZauN11+Ogc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46BzWWrjddfjoHNZauN11+Ogc1lq43XX46BzWWrjddfjoMyoKBJnFGcCulkeE7TBurYHdqd9vMu78HNZauN11+Ogc1lq43XX46BzWWrjddfjoBrF7KlHbKQfaLXZAY52WG2LLFIcoE4XkWxVc/UH7Ft4LkcPCvJSC3TxCsQ6Oqxb7jrtFg+F5NtEIK1BBmlex+dAy2j+k6eFXksUfbTDe6lW6ronXDm3VZH7S8RnCsA/DdCnLihXWzM/tGQxjsKibTkdsRD4UWmvzkV2A3/5F6nPltOBM80bQm7GghLvpXFSynprsspJ50DGw8JuSRz1i/WPNBciu/42rx/UxkfZ26jMpB7S3adITiULxParnLRXOxPuo1z3wjpDsQ58nk1HkBEIPO8XeZblEQJEe8DLlCbfgFaRrh05QFeqIw+l845fR25SX6Nwr14sPEm/+78dfZdsSKXxgpeuToLaSHj+w9MXKjRcEyhEL7wokoFuo6i2cQ==08CAB35B504F2BD9A6BF809EF5E2A92C'; # <-----  PUT ACTIVATION KEY HERE

class VSPE(object):
    __instance = None

    @staticmethod
    def getInstance():
        """ Static access method. """
        if VSPE.__instance is None:
            VSPE()
        return VSPE.__instance

    def __init__(self):
        if VSPE.__instance is not None:
            raise Exception("This class is a singleton!")
        pythoncom.CoInitialize()
        self.vspe = win32com.client.Dispatch("VSPE.VSPEApi")
        activation_status = self.vspe.vspe_activate(activationKey)
        logger.debug("Activation status is %s",activation_status)
        initialize_status = self.vspe.vspe_initialize()
        logger.debug("initialize status is %s", initialize_status)
        VSPE.__instance = self

    def createdevice(self,IN_PORT,OUT_PORT,baud_rate = "921600"):
        """
        Function adds a new device to virtual Serial list
        Args:
            IN_PORT: Input post for vitalization
            OUT_PORT: Output port for vitalization, Which will be used by the application
            baud_rate: baud_rate is a option parameter by default set to 921600

        Returns: None

        """
        cmd = OUT_PORT+";"+IN_PORT+";0;"+baud_rate+",0,8,1,0,0;0;0;0"
        create_device_status = self.vspe.vspe_createDevice('Splitter', cmd)
        if create_device_status < 1:
            logger.debug("Device is not created properly may be used by other application --> {}".format(create_device_status))
            create_device_status = self.vspe.vspe_createDevice('Splitter', cmd)
        logger.debug("Status of new device is %s",create_device_status)
        if create_device_status < 1:
            sys.exit("Device is not creating")

    def start_emulation(self):
        """
        Function starts the Serial port vitalization
        Returns: None

        """
        start_emulation_status = self.vspe.vspe_startEmulation()
        logger.debug("Start emulation status %s",start_emulation_status)

    def stop_emulation(self):
        """
        Function stops the Serial port vitalization
        Returns: None

        """
        stop_emulation_status = self.vspe.vspe_stopEmulation()
        logger.debug("Stop Emulation status %s",stop_emulation_status)
        self.vspe.vspe_release()