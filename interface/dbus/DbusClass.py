import sys
import pydbus
import os
import time
from pydbus import Variant
from interface.dbus import listenercopy
from interface.dbus.listenercopy import Test
from gi.repository import GLib
location = os.path.abspath(os.path.dirname(__file__))
import logging
logger = logging.getLogger('Class_logger')
from config import config,LOGPATH,logger

class Dbus(Test):
    def __init__(self,busname,ObjectPath,interface):
        self.busname = busname
        self.ObjectPath = ObjectPath
        self.interface = interface
        self.event_timeout = 30.0
        logger.debug('bus name %s , and Object path is %s ', self.busname, self.ObjectPath)
        self.bus = pydbus.SystemBus()
        self.proxy = self.bus.get(self.busname, self.ObjectPath,timeout=60)[self.interface]

    def args_parser(self,args):
        return_args = []
        logger.debug("arguments is : %s", args)
        args = args[0]
        if (type(args) == str) or (type(args)== unicode):
            for arg in args.split(","):
                logger.debug("single args %s",arg)
                arg = arg.replace(':', ',')
                return_args.append(eval(arg))
        else:
            return_args.append(args)
        return return_args


    def method_call(self,*args):
        # logger.debug("args is -- {}".format(args))
        try:
            self.arrg = args
            if len(args) == 1:
                self.function = args[0]
                func = getattr(self.proxy, self.function)
                ret = func()
                return ret
            else:
                self.function = args[0]
                logger.debug("Function name is -- {}".format(self.function))
                args = self.args_parser(args[1:])
                logger.debug('args value : %s', args)
                # print (args)
                func = getattr(self.proxy, self.function)
                ret = func(*args)
                return ret
        except Exception as e:
            logger.debug('Exception during function call: %s Function name : %s',str(e),self.function)
            print(('Exception during function call:' + str(e)))
            if isinstance(e, GLib.Error):
                logger.error('GLib error %s ', e)
                time.sleep(5)
            raise e

    def add_event(self, event_name):
        return listenercopy.register_listener(self.bus, self.interface, event_name)

    def recieve_event(self):
        # logger.debug("Length of the queue is %s", listenercopy.q.qsize())
        return listenercopy.q.get(timeout=float(self.event_timeout))