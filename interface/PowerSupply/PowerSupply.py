# !/usr/bin/env python
# # -*- coding:utf-8 –*-
"""
-----------------------------------------------------------------------------
Class implementation for PPS(Programable Power Supply)
Current supported Sigilent and TMI USB based power supply
test should not use it directly should be called through PowerSupplyInterface only
-----------------------------------------------------------------------------
"""
import re
import time
import serial
import vxi11
from config import logger

# logger = logging.getLogger("test_logger")

class SigilentPowerSupply(object):
    __instance = None
    @staticmethod
    def getInstance(ip):
        if SigilentPowerSupply.__instance == None:
            SigilentPowerSupply(ip)
        return SigilentPowerSupply.__instance

    def __init__(self,ip):
        if SigilentPowerSupply.__instance != None:
            logger.debug(SigilentPowerSupply.__instance)
            raise Exception("This class is a singleton!")
        else:
            self.ip = ip
            self.instr = vxi11.Instrument(self.ip)
            SigilentPowerSupply.__instance = self

    def __del__(self):
        logger.debug("Socket del called")
        self.instr.close()
        self.socket_close()

    def socket_close(self):
        pass
        # logger.debug("closing the socket connection")
        # self.instr.close()
        # sys.exit()

    def GetVoltage(self,channel):
        try:
            cmd = "MEASure:VOLTage? " + channel
            return self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from API %s",str(e))
        finally:
            # logger.debug("Finally statement called")
            self.socket_close()

    def SetVoltage(self, channel, value):
        try:
            cmd = channel + ":VOLTage " + str(value)
            return self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from socket %s", str(e))
            if "10054" in e:
                try:
                    self.socket_close()
                    return self.instr.write(cmd)
                except Exception as e:
                    raise Exception(str(e))
            else:
                raise Exception(str(e))
        finally:
            # logger.debug("finally block called")
            self.socket_close()

    def disable_channel(self, channel):
        try:
            cmd = "OUTPut " + channel + ",OFF"
            self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from socket %s",str(e))
        finally:
            self.socket_close()

    def enable_channel(self, channel):
        try:
            cmd = "OUTPut " + channel + ",ON"
            self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from socket %s",str(e))
            raise Exception(str(e))
        finally:
            self.socket_close()

    def SetCurrent(self, channel, value):
        try:
            cmd = channel + ":CURRent " + str(value)
            self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from socket %s",str(e))
        finally:
            self.socket_close()

    def GetCurrent(self, channel):
        try:
            cmd = "MEASure:CURRent? " + channel
            return self.instr.ask(cmd)
        except Exception as e:
            logger.debug("Error from socket %s",str(e))
        finally:
            self.socket_close()

class UsbPowerSupply(object):
   __instance = None
   @staticmethod
   def getInstance(port):
      """ Static access method. """
      if UsbPowerSupply.__instance == None:
         UsbPowerSupply(port)
      return UsbPowerSupply.__instance

   def __init__(self,port):
      """ Virtually private constructor. """
      if UsbPowerSupply.__instance != None:
          raise Exception("This class is a singleton!")
      else:
          self.port = port
          self.serial_connection = serial.Serial(self.port, 115200)
          UsbPowerSupply.__instance = self

   def GetVoltage(self, channel):
       joined_seq = ''
       self.serial_connection.write("getv \r\n".encode())
       time.sleep(1)
       while self.serial_connection.inWaiting() > 0:
           joined_seq = self.serial_connection.read_all().decode('utf-8')
       logger.debug(joined_seq)
       match = re.findall(r'\d+', joined_seq)
       res = list(map(int, match))
       return res[0]

   def __del__(self):
       logger.debug("Closing the Serial connection ")
       self.serial_connection.close()

   def SetVoltage(self, channel, value):
       joined_seq = ''
       cmd = "setv {} \r\n".format(value).encode()
       self.serial_connection.write(cmd)
       time.sleep(1)
       while self.serial_connection.inWaiting() > 0:
           joined_seq = self.serial_connection.read_all().decode('utf-8')
       logger.debug(joined_seq)
       match = re.findall(r'\d+', joined_seq)
       res = list(map(int, match))
       return res[0]

   def GetCurrent(self, channel):
       joined_seq = ''
       self.serial_connection.write("geta \r\n".encode())
       time.sleep(1)
       while self.serial_connection.inWaiting() > 0:
           joined_seq = self.serial_connection.read_all().decode('utf-8')
       logger.debug("current value is -- {}".format(joined_seq))
       match = re.findall(r'\d+', joined_seq)
       res = list(map(int, match))
       return float(res[0])/1000

   def enable_channel(self, channel):
       logger.debug("Enable channel is not required for USB power supply")
