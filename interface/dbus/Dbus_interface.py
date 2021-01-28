import execnet
import os
import time
from pebble import ThreadPool
# from interface.utils import TCU_IP
from config import interfaces,logger
TCU_IP = interfaces.get('ssh','ip')
os.environ['DBUS_SYSTEM_BUS_ADDRESS'] = 'tcp:host={},port=55556,family=ipv4'.format(TCU_IP)

# gw = execnet.makegateway("popen//python=py -2")

def dbus_function_verification(bus_name, object_path, interface_name, function, argument, expected=None, function_timeout=30):
    gw = execnet.makegateway("popen//python=py -2")
    create_ch = gw.remote_exec("""
    from interface.dbus.DbusClass import Dbus,logger
    import time
    try:
        busname, object_path, interface_name, function, argument  = channel.receive()
        obj = Dbus(busname, object_path, interface_name)
        if argument == None:
            ret = obj.method_call(function)
        else:
            logger.debug("I am in else")
            ret = obj.method_call(function, argument)
        channel.send(ret)
    except Exception as e:
        logger.debug('Exception during function call: %s', str(e))
        assert False,"Exception during function call {} for function {}".format(e,function)
    """)
    create_ch.send((bus_name, object_path, interface_name, function, argument))
    result = create_ch.receive(timeout=function_timeout)
    gw.exit()
    logger.debug("Function called -- {} response is -- {}".format(function,result))
    if expected is not None:
        assert expected == result,"Expected is not found"
    return result

def dbus_function_verification_async(bus_name, object_path, interface_name, function, argument, expected=None, function_timeout=30):
    pool = ThreadPool()
    # logger.debug("pool object -- {} -- for event : {}".format(pool,event))
    future = pool.schedule(dbus_function_verification, args=[bus_name, object_path, interface_name, function, argument, expected, function_timeout])
    return [future,pool]

def signal_call(bus_name, object_path, interface_name, event, timeout):
    gw = execnet.makegateway("popen//python=py -2")
    create_ch = gw.remote_exec("""
    from interface.dbus.DbusClass import Dbus,logger
    from interface.dbus import listenercopy
    import time
    busname, object_path, interface_name, event, timeout  = channel.receive()
    obj = Dbus(busname, object_path, interface_name)
    listenercopy.main()
    obj.add_event(event)
    ret = 'Empty'
    try:
        for i in range(0, timeout):
            try:
                ret = obj.recieve_event()
                break
            except Exception as e:
                time.sleep(1)
                logger.debug('Registered event is not received yet')
                ret = 'Empty'
                continue
    except Exception as e:
        logger.debug('No signal received in given time'.format(e))
        ret = 'Empty'
    finally:
        listenercopy.quit_handler()
    logger.debug('Ret value is: %s', ret)
    channel.send(ret)
        """)
    create_ch.send((bus_name, object_path, interface_name, event, timeout))
    result = create_ch.receive()
    gw.exit()
    logger.debug("Response is in sync function for {} -- {}".format(event,result))
    return result

def signal_call_async(bus_name, object_path, interface_name, event, timeout):
    pool = ThreadPool()
    # logger.debug("pool object -- {} -- for event : {}".format(pool,event))
    future = pool.schedule(signal_call, args=[bus_name, object_path, interface_name, event, timeout])
    time.sleep(3)
    return [future,pool]

def get_async_result(async_object,timeout=10):
    logger.debug("get result function called at --{}".format(time.ctime()))
    response = None
    try:
        logger.info("Event subscription function status -- {}".format(async_object[0].running()))
        response = async_object[0].result(timeout=timeout)
        logger.debug("Response is --{}".format(response))
    except Exception as e:
        logger.error("No response Received --> {}".format(e.__class__))
        pass
    finally:
        async_object[0].cancel()
        async_object[1].stop()
    logger.debug("get result function End at -- {}".format(time.ctime()))
    return response

# def direct(busname, object_path, interface_name, function, arrgument):
#     try:
#         #busname, object_path, interface_name, function, arrgument  = channel.receive()
#         from interface.dbus.DbusClass import Dbus
#         obj = Dbus(busname, object_path, interface_name)
#         if arrgument == None:
#             ret = obj.method_call(function)
#         else:
#             ret = obj.method_call(function, arrgument)
#         return ret
#         #channel.send(ret)
#     except Exception as e:
#         print ('Exception during function call: %s', str(e))
#
# if __name__ =="__main__":
#     busname_ofono = 'org.ofono'
#     object_path_ril_0 = '/ril_0'
#     object_path_ril_1 = '/ril_1'
#     interface_NetworkRegistration = 'org.ofono.NetworkRegistration'
#     interface_SimManager = 'org.ofono.SimManager'
#     interface_Modem = 'org.ofono.Modem'
#     interface_Manager = 'org.ofono.Manager'
#     interface_MessageManager = 'org.ofono.MessageManager'
#     interface_VoiceCallManager = 'org.ofono.VoiceCallManager'
#     interface_ConnectionContext = 'org.ofono.ConnectionContext'
#     interface_SupplementaryServices = 'org.ofono.SupplementaryServices'
#     interface_ConnectionManager = 'org.ofono.ConnectionManager'
#     interface_CallSettings = 'org.ofono.CallSettings'
#     interface_CallForwarding = 'org.ofono.CallForwarding'
#     interface_VoiceCall = 'org.ofono.VoiceCall'
#     interface_LongTermEvolution = 'org.ofono.LongTermEvolution'
#     interfaces_IpMultimediaSystem = 'org.ofono.IpMultimediaSystem'
#     interface_RadioSettings = 'org.ofono.RadioSettings'

    # number = "8317325137"
    # obj = signal_call_async(busname_ofono, object_path_ril_0, interface_VoiceCallManager, 'CallAdded', 8)
    # time.sleep(4)
    # print(dbus_function_verification(busname_ofono, object_path_ril_0, interface_Modem, 'GetProperties', None, None))
    # dial_object = dbus_function_verification(busname_ofono, object_path_ril_0, interface_VoiceCallManager, 'Dial',"'8317325137','default'")
    # get_calls = dbus_function_verification(busname_ofono, object_path_ril_0, interface_VoiceCallManager, 'GetCalls', None, None)
    # print("Get call is -- {}".format(get_calls))
    # print(get_async_result(obj,30))
    # dbus_function_verification(busname_ofono, dial_object, interface_VoiceCall, 'Hangup', None, None)
    # time.sleep(1)
    # get_calls = dbus_function_verification(busname_ofono, object_path_ril_0, interface_VoiceCallManager, 'GetCalls', None, None)
    # print("Get call is -- {}".format(get_calls))
    # print(direct(busname_ofono, object_path_ril_0, interface_Modem, 'GetProperties',None))
