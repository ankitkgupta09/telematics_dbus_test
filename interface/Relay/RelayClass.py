"""
USB relay class implementation using Ctype.
Class should be used directly inside the test case use RelayInterface for the same
"""
import ctypes
import os
import platform
import sys
import logging

libpath = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger('test_logger')

if sys.version_info.major >= 3:
  def charpToString(charp):
    return str(ctypes.string_at(charp), 'ascii')

  def stringToCharp(s):
    return bytes(s, "ascii")
else:
  def charpToString(charp):
    return str(ctypes.string_at(charp))

  def stringToCharp(s):
    return bytes(s)  # bytes(s, "ascii")

libfile = {'WindowsPE': {'64bit': "USB_RELAY_DEVICE_64.dll",
           '32bit': "USB_RELAY_DEVICE_32.dll"},
           'ELF': {'64bit': "usb_relay_device.so",
            '32bit': "usb_relay_device.so"}}[platform.architecture()[1]][platform.architecture()[0]]

usb_relay_lib_funcs = [
  # TYpes: h=handle (pointer sized), p=pointer, i=int, e=error num (int), s=string
  ("usb_relay_device_enumerate", 'h', None),
  ("usb_relay_device_close", 'e', 'h'),
  ("usb_relay_device_open_with_serial_number", 'h', 'si'),
  ("usb_relay_device_get_num_relays", 'i', 'h'),
  ("usb_relay_device_get_id_string", 's', 'h'),
  ("usb_relay_device_next_dev", 'h', 'h'),
  ("usb_relay_device_get_status_bitmap", 'i', 'h'),
  ("usb_relay_device_open_one_relay_channel", 'e', 'hi'),
  ("usb_relay_device_close_one_relay_channel", 'e', 'hi'),
  ("usb_relay_device_close_all_relay_channel", 'e', 'h')
]

class Relay(object):
  """
  Relay control class
  """
  def __init__(self,relayID,CloseAllRelay = False):
    self.relayID = relayID
    self.relaystate = CloseAllRelay
    self.loadLib()
    self.getLibFunctions()
    self.openDevById(self.relayID)
    if self.relaystate == True:
      self.closeAllChannel()

  def loadLib(self):
    """Load the C++ DLL"""
    try:
      # self.mydll = ctypes.WinDLL('/'.join([libpath, libfile]))
      self.mydll = ctypes.CDLL('/'.join([libpath, libfile]))
    except OSError:
      print ("Failed load lib")

  def getLibFunctions(self):
    """ Get needed functions and configure types; call lib. init.
    """
    assert  self.mydll

    # Get lib version (my extension, not in the original dll)
    libver =  self.mydll.usb_relay_device_lib_version()
    print("%s version: 0x%X" % (libfile, libver))

    ret =  self.mydll.usb_relay_init()
    if ret != 0: raise ValueError("Failed lib init!")

    ctypemap = {'e': ctypes.c_int, 'h': ctypes.c_void_p, 'p': ctypes.c_void_p,
                'i': ctypes.c_int, 's': ctypes.c_char_p}
    for x in usb_relay_lib_funcs:
      fname, ret, param = x
      try:
        f = getattr(self.mydll, fname)
      except Exception:
        raise LookupError("Missing lib export:" + fname)

      ps = []
      if param:
        for p in param:
          ps.append(ctypemap[p])
      f.restype = ctypemap[ret]
      f.argtypes = ps
      setattr(self.mydll, fname, f)

  def openDevById(self,idstr):
    """
    Open the Relay handler
    Args:
      idstr: Relay ID

    Returns: None

    """
    print(("Opening " + idstr))
    self.hdev = self.mydll.usb_relay_device_open_with_serial_number(stringToCharp(idstr), 5)

  def get_relay_info(self):
      devids = []
      enuminfo = self.mydll.usb_relay_device_enumerate()
      while enuminfo:
        idstrp = self.mydll.usb_relay_device_get_id_string(enuminfo)
        idstr = charpToString(idstrp)
        print(idstr)
        assert len(idstr) == 5
        if not idstr in devids:
          devids.append(idstr)
        else:
          print("Warning! found duplicate ID=" + idstr)
        enuminfo = self.mydll.usb_relay_device_next_dev(enuminfo)

      print("Found devices: %d" % len(devids))
      return devids


  def closeDev(self):
    """
    Close the relay dll
    Returns:

    """
    global hdev
    self.mydll.usb_relay_device_close(self.hdev)
    hdev = None

  def openChannel(self, number):
    """
    Open relay PIN
    Args:
      number: Relay PIN number which you want to open

    Returns: Relay PIN current status

    """
    self.number = number
    open_one_relay_status = self.mydll.usb_relay_device_open_one_relay_channel(self.hdev, self.number)
    logger.debug("Open single relay PIN status --> {}".format(open_one_relay_status))
    return open_one_relay_status

  def closechannel(self,number):
    """
    Close the relay PIN
    Args:
      number: Relay PIN number which you want to close

    Returns: Relay PIN current status

    """
    self.number = number
    close_one_relay_status = self.mydll.usb_relay_device_close_one_relay_channel(self.hdev, self.number)
    logger.debug("Close single relay PIN status --> {}".format(close_one_relay_status))
    return close_one_relay_status

  def channelStatus(self,n):
    """
    Relay PIN current status
    Args:
      n: Relay PIN number which you want to check the status

    Returns: Relay PIN current status

    """
    self.n = n-1
    ret = self.mydll.usb_relay_device_get_status_bitmap(self.hdev)
    return ret & 1 << self.n != 0

  # def get_bin(self,x, n=0):
  #   """
  #   Get the binary data
  #   Args:
  #     x:
  #     n:
  #
  #   Returns:
  #
  #   """
  #   return format(x, 'b').zfill(n)

  def closeAllChannel(self):
    """
    Close all the relay PINS
    Returns: status
    """
    close_all_status = self.mydll.usb_relay_device_close_all_relay_channel(self.hdev)
    logger.debug("Close all relay status --> {}".format(close_all_status))
    return close_all_status


  def unloadLib(self):
    """
    Unload the C++ dll from the memory
    Returns: None
    """
    global hdev, L
    self.closeDev()
    self.mydll.usb_relay_exit()
    self.mydll = None
    print("Lib closed")