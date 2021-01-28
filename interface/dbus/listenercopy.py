from gi.repository import GLib, GObject
import pydbus
import threading, Queue
import json
import logging
import time

logger = logging.getLogger('test_logger')
ready = threading.Event();

loop=None
listener_thread=None
q = Queue.Queue()

def clearqueue():
    if(not q.empty()):
        q.queue.clear()

def quit_handler():
    """Signal handler for quitting the receiver."""
    global loop
    logger.debug('Quitting....')
    clearqueue()
    if loop is not None:
        logger.debug("Instance of Loop found")
        loop.quit()
        logger.debug("Quitting Loop")
    else:
        logger.debug("No instance of Loop found")

def main():
    global listener_thread
    # GObject.threads_init()
    #GObject.timeout_add(100 * 1000, quit_handler)
    ready.set()
    listener_thread = threading.Thread(target=listen)
    listener_thread.start()

def catchall_handler(*args):
    """Catch all handler.
    Catch and print information about all signals.
    """
    # global q
    arr= []

    logger.debug('---- Caught signal ----')

    logger.debug('Arguments:')
    for arg in args:
        arr.append(arg)
    for i in arr:
        logger.debug('Argument type - %s', type(i))
        logger.debug('Argument value - %s', i)
    arr.append(time.time())
    q.put(arr)
    logger.debug('Signal added to queue successfully')
    logger.debug("Length of Queue is %s", q.qsize())

def register_listener(busname_temp, interface_name, signalname):
    sub = None
    logger.debug("before bus subscribe")
    sub = busname_temp.subscribe(iface=interface_name, signal=signalname, signal_fired=catchall_handler)
    logger.debug("after bus subscribe - %s", sub)
    return sub

def listen():
    global loop
    logger.debug("--listening to dbus--")
    # gobject.timeout_add_seconds(180)

    loop = GLib.MainLoop()
    logger.debug("loop object created")

    logger.debug("running loop")
    loop.run()

    logger.debug("Quit Loop Successfully")   # This portion will run after the loop is terminated by quit signal.)

class Test:
    def start_loop(self):
        main()

    def quit_loop(self):
        quit_handler()
#
if __name__ == "__main__":
    main()
