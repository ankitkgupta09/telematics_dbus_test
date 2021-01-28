"""
OS Helper function and High level cross interface functionality are
exposed from utility
"""
from __future__ import print_function
import os
import platform
import subprocess
import time
import pytest
import shutil
import sys
import allure
import psutil
from threading import Timer

from interface.SSH.SSHInterface import execute_command_and_return_value,status_service_systemctl,\
    execute_command_and_return_console_output,remount_device,status_service_systemctl_in_loop
from interface.PowerSupply.PowerSupplyInterface import POWER_SUPPLY_CHANNEL,set_voltage,switch_on
from interface.Serial.SerialInterface import find_serial_port
from interface.Relay.RelayInterface import Relay_ON,Relay_OFF

from config import config,peripherals,interfaces,logger

RELAY_ID = peripherals.get('USB-Relay', 'Id')
"""USB Relay ID """
FHE_RELAY_NUMBER = peripherals.get('USB-Relay', 'FHE')
"""Relay PIN connected to FHE"""
FASTBOOT_NUMBER = peripherals.get('USB-Relay', 'FastBoot')
"""Relay PIN connected to Fastboot cable"""
AIRBAG_NUMBER = peripherals.get('USB-Relay', 'Airbag')
"""Relay PIN connected to Airbag module"""
TCU_IP = interfaces.get('ssh','ip')
"""TCU ETH IP address to access the TCU over SSH"""
ALM_URL = 'https://alm.harman.com/qm3/web/console/TCAM2%20(QM3)/_whMlEDXsEeqzEo0fCRGL0w#action=com.ibm.rqm.planning.home.actionDispatcher&subAction=viewTestCase&id='
"""ALM url """

def execute_command_on_cmd_get_the_output(cmd,timeout=5):
    """

    :param cmd:
    :param timeout:
    :return:
    """
    sys.stdout.flush()
    sys.stderr.flush()
    kill = lambda process: process.kill()
    cmd_exe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    my_timer = Timer(timeout, kill, [cmd_exe])
    try:
        my_timer.start()
        stdout, stderr = cmd_exe.communicate()
    except Exception as e:
        logger.error("exception --> {} timer value is --> {}".format(e,my_timer))
    finally:
        my_timer.cancel()
    # logger.debug("stdout --> {}, stderr --> {}".format(stdout,stderr))
    return stdout.decode(encoding='windows-1252')

def __connection_test(ip):
    if platform.system() == "Windows":
        cmd = "ping " + ip + " -n 1"
        try:
            # response = str(subprocess.check_output(cmd))
            response = execute_command_on_cmd_get_the_output(cmd)
            logger.debug("cmd is --> {},  response is --> {}".format(cmd,response))
            if 'TTL' in response.upper():
                response = 1
            else:
                response = 0
            return response
        except Exception as e:
            logger.debug("exception is %s", str(e))
            return 0
    else:
        logger.debug("Test OS not a Windows PC")
        response = os.popen("ping -c 1 " + ip).read()
        if 'TTL' in response.upper():
            response = 1
        else:
            response = 0
        return response

@allure.step('Check the connection for "{ip}" is established')
def connection_wait_in_loop(ip, timeout=50, connection_status=True):
    """
    Wait for TCU to wakeup and start the ETH connection
    Args:
        ip: TCU IP address
        timeout: Max time to wait for ETH to up and running
        connection_status: True if expected to have a connection,
                    False for negative validation will be used in power management

    Returns: If SSH connection is up and running return Time taken to establish the SSH connection.
             else return the max timeout

    """
    logger.debug('Waiting for IP %s ping for , %s ', ip, timeout)
    start_time = time.time()
    elapsed_time = 0
    expect_status = 1
    if not connection_status:
        expect_status = 0
    while (__connection_test(ip) != expect_status) and elapsed_time < timeout:
        elapsed_time = time.time() - start_time
        logger.debug('Waiting for board to wakeup, time elapsed: %s',
                     time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
        print('Waiting for board to wakeup, time elapsed: ', time.strftime("%H:%M:%S", time.gmtime(elapsed_time)))
        time.sleep(1)
    if connection_status:
        assert elapsed_time < timeout, "NO ETH connection to TCU after --> {} sec".format(elapsed_time)
    return elapsed_time

def remove_process(process_list):
    """
    Function to remove the list of process which need to be killed
    Args:
        process_list: List of services

    Returns: None

    """
    try:
        for process in process_list:
            for proc in psutil.process_iter():
                if proc.name() == process:
                    print("Termination process --> " + proc.name())
                    proc.kill()
    except:
        pass

def update_configuration_file(word_to_search,word_to_replace,file):
    """
    Function to search and replace the string matched with word_to_search.
    Args:
        word_to_search: Search the string in the given file
        word_to_replace: replace the string with word_to_search
        file: input configuration file which need the update

    Returns: Int value
        0 : success
        -1 : if not found
        4 : if "sed" is not present
    """
    remount_device()
    return execute_command_and_return_value("/bin/sed -i 's/{}/{}/g' {}".format(word_to_search,word_to_replace,file))

def get_configuration_from_file(word_to_search,file):
    """
    Function gets the required configuration from a config file based on the word_to_search parameter.
    Args:
        word_to_search: string to be searched in the file
        file: search result

    Returns: configuration lines matches with the search criteria

    """
    return execute_command_and_return_console_output("sed -n -e '/{}/p' {}".format(word_to_search,file)).rstrip('\n')

def restart(number=POWER_SUPPLY_CHANNEL, ip_connection_timeout=60, connection_status=True):
    """
    Function can be used to restart the TCU with the help of programmable power supply
    :param number: Channel number where TCU is connected (CH1/CH2)
    :param ip_connection_timeout: Time to wait for the connection
    :param connection_status: Expected connection status True if you expect connection should be available
    :return: None
    """
    set_voltage(number, 0)
    time.sleep(2)
    set_voltage(number, 12)
    switch_on(number)
    connection_wait_in_loop(TCU_IP, ip_connection_timeout, connection_status)

def xfail_update(xfail_reason, elvis_id):
    """
    Any test if you have raised a Ticket you can make the test as xfail with help of this function
    Args:
        xfail_reason: Reason of failure
        elvis_id: Ticket ID

    Returns: Assertion message

    """
    return allure.dynamic.link(name="Elvis Id: {}".format(elvis_id), url="https://elvis.harman.com/cgi-bin/ticket?TID={}".format(elvis_id)), pytest.xfail(reason=xfail_reason)

@allure.step("Asserting if {test_result} {op} {expected_result}")
def assertion(test_result, op, expected_result, assert_msg, ticket_id=None):
    """
    Function that wraps any assert in order to display it as an Allure step with a descriptive message.
    Args:
        test_result: Test Result which need to be validated
        op: Which operator need to be apply for validation
        expected_result: Expected result for validation
        assert_msg: Assertion message to show if validation failed
        ticket_id: Ticket ID if any By default None

    Returns: None

    """
    if op is None and expected_result is None:
        assert test_result, assert_msg
        return True
    import operator
    ops = {'>': operator.gt,
           '<': operator.lt,
           '==': operator.eq,
           '<=': operator.le,
           '>=': operator.ge,
           '!=': operator.ne,
           'and': operator.and_,
           'or': operator.or_,
           'xor': operator.xor,
           'is': operator.is_,
           }
    logger.debug(" ~ Asserting if " + str(test_result) + " " + op + " " + str(expected_result))
    if op in ops:
        if ticket_id is None:
            assert ops[op](test_result, expected_result), assert_msg
        else:
            assert ops[op](test_result, expected_result), xfail_update(assert_msg, ticket_id)
    if op == 'in':
        if ticket_id is None:
            assert test_result in expected_result, assert_msg
        else:
            assert test_result in expected_result, xfail_update(assert_msg, ticket_id)
    if op == 'not in':
        if ticket_id is None:
            assert test_result not in expected_result, assert_msg
        else:
            assert test_result not in expected_result, xfail_update(assert_msg, ticket_id)

def __bluebox_recover():
    """
    Recover the bluebox if not working (should not be used directly)
    Returns: None
    """
    Relay_OFF(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
    set_voltage(POWER_SUPPLY_CHANNEL, 0)
    time.sleep(5)
    Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
    time.sleep(8)

def bluebox_command(cmd,retry=3):
    """
    Function can be used to run bluebox command, Command need to be pass as string
    Args:
        cmd: diffrent mode Ex -
            1. 0x02 - for Normal mode
            2. 0x03 - for WUC flashing
            3. 0x06 - for SOC flashing

        retry: Number of retry By default 3

    Returns:

    """
    while retry > 0:
        try:
            bluebox_cmd = "bluebox.exe -s"+str(cmd)+ " -c"+find_serial_port()
            cmd_status = os.popen(bluebox_cmd).read()
            logger.debug("Bluebox command status is --> {}".format(cmd_status))
            if "Timeout!" not in cmd_status:
                time.sleep(2)
                set_voltage(POWER_SUPPLY_CHANNEL, 12)
                return True
            __bluebox_recover()
        except Exception as e:
            logger.error("Error while switching Bluebox -- {}".format(e))
        retry = retry-1
    set_voltage(POWER_SUPPLY_CHANNEL, 12)
    return False

def PadHexwithLead0s(hexStr):
    """
    Padding for a Hex string
    Args:
        hexStr: hex string

    Returns: updated hex string

    """
    if isinstance(hexStr, str):  # Make sure input argument is string
        if len(hexStr) % 2 != 0:  # If the length is not even
             hexStr = '0' + hexStr  # Add a leading '0' to get even length
    return hexStr

def is_hex(s):
    try:
        int(s, 16)
        return True
    except ValueError:
        return False

def get_service_list(component,partition):
    """
    Gets the list of service applicable to respective partition
    Args:
        component: Module you need a service list Ex - software_update, diagnostics etc..
        partition: Partition Ex -ONLY_BOOTLOADER, ONLY_APP
    Returns: List of services
    """
    service_list = ""
    partition_list = ['COMMON']
    partition_list.append(partition)
    for i in partition_list:
        if config.has_option(i,component):
            service_list = service_list + config.get(i,component)
    if service_list != "":
        return list(eval(service_list))
    return []

def unzip(name):
    """
    Extract the file
    Args:
        name: File name you want to extract

    Returns: None

    """
    cmd = "7z e -y {}".format(name)
    unzip_response = os.system(cmd)
    assert unzip_response == 0,"unzip/extract Failed"
    # os.system("rm {}".format(name))

def space_separated_string(string: str) -> str:
    """
    space formatting for a string
    Args:
        string: String which you want to do formaating

    Returns: formatted string with space after 2 char

    """
    t = iter(string.replace(" ", ""))
    return ' '.join(a+b for a,b in zip(t, t))

def string_to_asii(string: str) -> str:
    """

    Args:
        string:

    Returns:

    """
    converted_string = ''
    for a in string:
        converted_string = converted_string + hex(ord(a)).replace('0x', '')
    return space_separated_string(converted_string)

def clear_folder_or_files(file):
    """Function to delete all the logs"""
    if os.path.isfile(file) or os.path.islink(file):
        os.remove(file)  # remove the file
    elif os.path.isdir(file):
        shutil.rmtree(file)  # remove dir and all contains

def service_check(list_of_service):
    service_result = dict()
    service_expected = dict()
    for service in list_of_service:
        service_expected[service] = True
    for service in list_of_service:
        service_status = status_service_systemctl_in_loop(service, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service, service_status))
        # if service is not running capturing the systemctl status of the service
        service_result[service] = service_status
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service)
            logger.debug("Status of the service: \n%s", status_text)
    # validation all the service is running or not
    assert service_result == service_expected,set(service_result.items()) ^ set(service_expected.items())


if __name__== "__main__":
    print(get_service_list('telephony','ONLY_BOOTLOADER'))