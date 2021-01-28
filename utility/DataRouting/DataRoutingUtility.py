import allure
import subprocess
from config import *
from interface.SSH.SSHInterface import execute_command_and_return_console_output,\
    execute_command_and_return_value

from utility.Telephony.TelephonyUtility import object_path_ril_0,\
    data_status,nad_status

Test_Bench_IP = interfaces.get("DOIP","SOCKET_ADDRESS")
API_OVER_DBUS = False

@allure.step('Setting Default route SIM Object:"{ril_object}" ')
def set_default_route(ril_object=object_path_ril_0):
    """
    Set Default route
    Arg: ril_0/ril_1
    Returns: True/False
    """
    pdn_info = data_status(ril_object)
    if not pdn_info["Active"]:
        logger.info("Internet PDN currently Not Activated. PDN Info:\n{}".format(pdn_info))
        return False
    # check if default route already set or not
    cmd = "/sbin/route|grep default"
    grep_data = execute_command_and_return_console_output(cmd)
    if pdn_info["Interface"] in grep_data or pdn_info["Address"] in grep_data:
        logger.info("Default route already set. Default Route: {}".format(grep_data))
        return True
    default_cmd = "/sbin/route add default gw "
    exec_status = execute_command_and_return_value(default_cmd + pdn_info["Address"])
    assert exec_status is 0, "Failed to Set default gw. execution status: {}".format(exec_status)
    logger.info("Default route set. Address: {}".format(pdn_info["Address"]))
    return True

@allure.step('get current Default route')
def get_default_route():
    '''
    Get Current default route
    Returns: {"Interface": None,"Address": None}
    '''
    def_route = {"Interface": None,"Address": None}
    grep_data = execute_command_and_return_console_output("/sbin/ip route | grep default")
    if not grep_data:
        logger.info("No Default Route set.")
        return def_route
    grep_data = str(grep_data).replace("\n","")
    grep_data = grep_data.split(" ")
    def_route["Address"] = grep_data[2]
    def_route["Interface"] = grep_data[4]
    return def_route

@allure.step('Enable ethernet tethering')
def enable_tethering(sim_object=object_path_ril_0):
    '''
    Set Firewall rules for enabling Ethernet tethering
    Arg: ril_0/ril_1
    Returns: True/False

    '''
    pdn_info = data_status(sim_object)
    if pdn_info["Interface"] not in get_default_route()["Interface"] and get_default_route()["Interface"]:
        logger.info("PDN Interface: {} not available as default route.".format(pdn_info["Interface"]))
        return False
    ip_forward_cmd = "/bin/echo 1 > /proc/sys/net/ipv4/ip_forward"
    assert execute_command_and_return_value(ip_forward_cmd) is 0,"Failed to enable ip_forwarding"
    iptable_cmd = "/usr/sbin/iptables -t nat -A POSTROUTING -o {} -j MASQUERADE".format(pdn_info["Interface"])
    assert execute_command_and_return_value(iptable_cmd) is 0,"Failed to set POSTROUTING Rule"
    logger.info("Enable Tethering Completed.")
    return True

@allure.step('check ping over tethering. Ping Address: "{ping_address}" ')
def check_tether_ping(ping_address = "www.google.com",timeout = 5000):
    '''
    Set Firewall rules for enabling Ethernet tethering
    ping_address = address to ping
    timeout = Timeout in milliseconds to wait for each reply
    Returns: True/False

    '''
    ping_result = subprocess.check_output("ping -w {0} -S {1} {2}".format(timeout,Test_Bench_IP,ping_address))
    logger.debug("Ping Outcome: %s" % ping_result)
    if 'TTL' not in str(ping_result).upper():
        logger.info("Ping to Address: {0} Failed. Ping Result:\{1}".format(ping_address,ping_result))
        return False
    logger.debug("Ping to Address: {} ==> Success".format(ping_address))
    return True

@allure.step('Checking Modem State. SIM: "{SIM}" State: "{state}" Waittime: "{waittime}"')
def wait_modem_state(SIM = object_path_ril_0, state = True, waittime=30):
    """
    API is developed to get Modem state till waittime
    SIM: [ril_1/ril_0]
    state: [True/False]
    waittime: time to wait
    :return: [True/False]
    """ 
    logger.debug("Inside Wait Modem state function")   
    for i in range(0,waittime,2):
        modem_state = nad_status(SIM).boolValue            
        if modem_state == state:
            logger.debug("Expected Modem State found. Expected: {0} Current: {1}".format(state,modem_state))
            return True
        time.sleep(2)
        logger.debug("Expected Modem State not found. Expected: {0} Current: {1}".format(state,modem_state))
    logger.info("Expected Modem state not found after Waittime: {0}. Expected: {1}".format(waittime,state))
    return False