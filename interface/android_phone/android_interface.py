import subprocess
import time
import platform
import re
import logging
import allure
import sys

import shlex
from subprocess import Popen, PIPE
from threading import Timer
from config import peripherals
id1 = peripherals.get('Mobile', 'id1')
id2 = peripherals.get('Mobile', 'id2')

logger = logging.getLogger('test_logger')

def execute_command_on_cmd_get_the_output(cmd,timeout=5):
    """

    :param cmd:
    :param timeout:
    :return:
    """
    sys.stdout.flush()
    sys.stderr.flush()
    # kill = lambda process: process.kill()
    # cmd_exe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    # my_timer = Timer(timeout, kill, [cmd_exe])
    proc = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    timer = Timer(timeout, proc.kill)
    try:
        timer.start()
        stdout, stderr = proc.communicate()
    except Exception as e:
        logger.error("exception --> {} timer value is --> {}".format(e,timer))
    finally:
        timer.cancel()
    logger.debug("stdout --> {}, stderr --> {}".format(stdout,stderr))
    return stdout.decode('utf8')

@allure.step('Check if Test device is connected to PC')
def check_device_status(phone_id, retry_on_failed=2):
    """
    Verify the android test phone connected to setup
    Args:
        phone_id: device adb id, you can find the same using "adb devices" command
        retry_on_failed: If you want to retry on failure, default is 2 try

    Returns:

    """
    logger.debug("Verify test device is connected with local setup or not")
    cmd = 'adb devices'
    for i in range(0, retry_on_failed):
        try:
            # output = subprocess.check_output(cmd)
            output = execute_command_on_cmd_get_the_output(cmd)
            logger.debug("Device connection status %s",output)
            if phone_id in output:
                return True
        except Exception as e:
            logger.error("Exception while checking the device status %s",str(e))
            pass
    assert phone_id in output,"Test phone is not connected : " + phone_id

def check_call_status(phone_id=id2):
    """
    Check your mobile phone call status
    Args:
        phone_id: adb id

    Returns:
        0       Idle
        1       Ringing
        2       Active

    """

    logger.debug("checking call status in mobile")
    if "Linux" in platform.platform():
        command = "adb -s "+ phone_id+" shell dumpsys telephony.registry | grep mCallState "
        cmdresult = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output, output_state = cmdresult.communicate()
        output = output.decode("utf-8")
        output = output.strip().split("\n")[0]
        output = re.sub('[^ 0-9]', '', output)
        print("output is -- {}".format(output))
        return output
    else:
        command = "adb -s " + phone_id + " shell dumpsys telephony.registry | grep mCallState "
        # command = "adb -s "+ phone_id+" shell dumpsys telephony.registry | findstr mCallState "
    # output = subprocess.check_output(command)
    output = str(execute_command_on_cmd_get_the_output(command))
    output = re.sub('[^ 0-9]', '', output).strip().split("\r\n")
    output = output[0].split(" ")[0]
    return output

@allure.step('Accept phone call on the mobile side')
def accept_call(phone_id = id2):
    """
    Accept a call on Test mobile
    Args:
        phone_id:

    Returns:

    """
    logger.debug("entered function to accept call")
    logger.debug("Triggering accept call")
    accept_call = "adb -s "+ phone_id+" shell input keyevent 5"
    start_time = time.time()
    duration = 0
    status = check_call_status(phone_id)
    while duration < 10 and status != '2':
        status = check_call_status(phone_id)
        logger.debug("Current call status in mobile side %s", status)
        if status != '2':
            logger.debug("Tried once more to accept call")
            trigger_accept_call = subprocess.Popen(accept_call, shell=True, stdout=subprocess.PIPE,
                                                   stderr=subprocess.STDOUT)
        duration += 1
        time.sleep(1)

@allure.step('End phone call,from the mobile side')
def end_call(phone_id = id2):
    """
    End a call on Test Mobile
    Args:
        phone_id: adb Id

    Returns: None

    """
    logger.debug("Triggering end/reject call")
    reject_call = "adb -s "+phone_id+" shell input keyevent 6"
    trigger_reject_call = subprocess.Popen(reject_call, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    time.sleep(1)

@allure.step('Call from Mobile to TCU')
def make_a_call_from_mobile(number, phone_id=id2):
    """
    Make a call from Test phone
    Args:
        number: Number call need to trigger
        phone_id: adb Id of test phone

    Returns: None

    """
    logger.debug("Triggering new call")
    command = "adb -s "+phone_id+" shell am start -a android.intent.action.CALL -d tel:" + str(number)
    logger.debug(command)
    # initiate_call = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    initiate_call = subprocess.check_output(command,shell=True)
    logger.debug("initiate call status %s", initiate_call)
    # time.sleep(2)
    call_status = 0
    for i in range(0,5):
        call_status = check_call_status(phone_id)
        logger.debug("Call status in mobile %s", call_status)
        if call_status == '2':
            break
        time.sleep(1)
    assert call_status == '2',"Call did not start from mobile"


@allure.step('Send SMS from mobile to TCU')
def send_sms(number, text, phone_id = id2):
    """
    Send SMS from test phone
    Args:
        number: SIM card number SMS need to be send
        text: connected of the MSG
        phone_id: Test phone adb Id

    Returns: None

    """
    data=str(text)
    data = data.replace(' ','\ ')
    SMScommand = "adb -s "+phone_id+" shell service call isms 7 i32 0 s16 'com.android.mms.service' s16 " + str(number)+ """ s16 "null" s16 """ + """ " """ + str(data) + """" s16 "null" s16 "null" """
    logger.debug(SMScommand)
    subprocess.Popen(SMScommand, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    logger.debug('SMS Send from mobile')


@allure.step('Receive and disconnect the call on the mobile side')
def check_call_receive_and_disconnect(wait_time, phone_id=id2):
    device_status = check_device_status(phone_id)
    assert device_status == True
    logger.debug('Phone serial number is: %s', phone_id)
    temp = 1
    logger.debug("inside call recieve and disconnect....")
    # waittime = int(waittime)
    while(temp < int(wait_time)):
        status = check_call_status(phone_id)
        logger.debug("status after checking is .. {}".format(status))
        if (status == '1'):
            accept_call(phone_id)
            end_call(phone_id)
            break
        else:
            #logger.debug("Waiting for Recieving Call... Aborting in %d secs" %waittime)
            time.sleep(1)
            temp = temp + 1
            continue
    return status


def wait_for_phone_status_change(wait_time, expected_state):
    """
    Wait for call status change to particular status
    Args:
        wait_time: Wait time for call status to change
        expected_state: expected call status

    Returns: call status

    """
    status = 0
    start_time = time.time()
    max_time_to_wait = start_time+ int(wait_time)
    while time.time() > max_time_to_wait:
        status = check_call_status()
        print ("status after checking is .. {}".format(status))
        if (status == expected_state):
            break
        else:
            time.sleep(1)
            continue
    return status

def check_and_receive_call(wait_time, phone_id=id2):
    """
    Wait for call to come in mobile and accept
    Args:
        wait_time: Wait for call to ring in mobile
        phone_id: adb id

    Returns: call status

    """
    device_status = check_device_status(phone_id)
    assert device_status == True,"Test phone is not connected"
    print('Phone serial number is: ', phone_id)
    temp = 1
    logger.debug("inside call receive and disconnect....")
    wait_time = int(wait_time)
    while(temp <= wait_time):
        status = check_call_status(phone_id)
        logger.debug("status after checking is .. {}".format(status))
        if (status == '1'):
            accept_call(phone_id)
            #end_call(phone_id)
            break
        else:
            #logger.debug("Waiting for Recieving Call... Aborting in %d secs" %waittime)
            time.sleep(1)
            temp = temp + 1
            continue
    return status



if __name__ == "__main__":
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler("{}.txt".format(__name__), mode='w+')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(module)s - %(message)s')
    logger.addHandler(handler)
    handler1 = logging.StreamHandler(sys.stdout)
    formatter1 = logging.Formatter('%(asctime)s - %(funcName)s - %(module)s - %(message)s')
    handler1.setFormatter(formatter1)
    logger.addHandler(handler1)
    for i in range(0,50):
        status = check_call_status(id1)
        print("status -- {} Type is -- {}".format(status,type(status)))
        time.sleep(2)