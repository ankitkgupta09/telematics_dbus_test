"""
All the SSH helper function are exposed from this file.
There function can be exposed directly into the test cases
"""

import time
import allure
import sys
from multiprocessing.pool import ThreadPool
from config import interfaces,logger
from interface.SSH.SSHConnection import SSHConnection

SSH_TIMEOUT = int(interfaces.get('ssh', 'command_timeout'))

@allure.step('Executing a command over SSH and return exit status- "{command}"')
def execute_command_and_return_value(command):
    """
    Function runs the command over the SSH shell and return the SSH console output
    Args:
        command: SSH shell command

    Returns: Exit status of the command

    """
    session = SSHConnection().get_transport_channel()
    session.exec_command(command)
    return session.recv_exit_status()

@allure.step('Executing a command over SSH - "{command}"')
def execute_command_and_return_console_output(command, standard_input=None,timeout=SSH_TIMEOUT):
    """
     Function runs the command over the SSH shell and return the SSH console output
    Args:
        command: command to run over the shell
        standard_input: provide the input to the command after execution
        timeout: Max time to wait for any command to run
    Examples:
        ``list_of_files = execute_command_and_return_console_output("ls")``

    Returns: SSH console output

    """
    session = SSHConnection().get_session()
    stdin, stdout, stderr = session(command, timeout)
    if len(str(standard_input)):
        if isinstance(standard_input, str):
            stdin.write(standard_input)
            stdin.flush()
        if isinstance(standard_input, int):
            stdin.write(str(standard_input))
            stdin.flush()
        elif not isinstance(standard_input, type(None)):
            for i in standard_input:
                stdin.write(str(i))
                stdin.flush()
    cmd_response = stdout.readlines()
    resp = ''.join(cmd_response)
    if not resp:
        cmd_error = stderr.readlines()
        resp = ''.join(cmd_error)
    return resp

@allure.step('Executing a command on Active Shell - "{cmd}"')
def execute_command_on_active_shell_and_return_console_output(cmd, timeout=10):
    """
    Interactive session for SSH
    Args:
        cmd: command which you want to send
        timeout: max time to wait for the response

    Returns: Console output, stdout buffer return

    """
    try:
        start_time = time.time()
        elapsed_time = 0
        channel = SSHConnection().get_shell()
        channel.send(cmd + '\n')
        # logger.debug("Command : %s send on active shell", str(cmd))
        while not channel.recv_ready() and elapsed_time < timeout:
            logger.debug("Waiting for exit status ready")
            elapsed_time = time.time() - start_time
            time.sleep(2)
        if elapsed_time > timeout:
            start_time = time.time()
            elapsed_time = 0
            logger.error("Command:  %s did not exist properly",
                         cmd)  # this code is just a work around we have to apply a proper fix here
            channel = SSHConnection().get_shell()
            channel.send(cmd + '\n')
            while not channel.recv_ready() and elapsed_time < timeout:
                logger.debug("Waiting for exit status ready")
                elapsed_time = time.time() - start_time
                time.sleep(2)
        logger.debug("Reading data from console")
        sys.stdout.flush()
        out = channel.recv(9999999)
        logger.debug("Output is %s", out)
        return out.decode("utf-8")
    except Exception as e:
        logger.debug("Exception during active shell communication %s", str(e))
        close_shell()

def close_shell():
    """
    Function need to be called to close the interactive session
    :return: Not returning any value
    """
    SSHConnection().close_shell()
    logger.debug("SSH Active session closed")


def start_service_systemctl(service_name):
    """
    Starts a systemctl service
    Args:
        service_name: service name

    Returns: Exit status of the command
        For more detail refer link --> https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8

    """
    cmd = 'systemctl start ' + service_name
    logger.debug("Command is %s", cmd)
    return execute_command_and_return_value(cmd)

def stop_service_systemctl(service_name):
    """
    Stops a systemctl service
    Args:
        service_name: service name

    Returns: Exit status of the command
        For more detail refer link --> https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8

    """
    cmd = 'systemctl stop ' + service_name
    logger.debug("Command is %s", cmd)
    return execute_command_and_return_value(cmd)

def status_service_systemctl(service_name):
    """
    Used to check the status of service
    Args:
        service_name: service name

    Returns: service systemctl logs --> str

    """
    cmd = 'systemctl status ' + service_name
    logger.debug("Command is %s", cmd)
    return execute_command_and_return_console_output(cmd)

def status_service_systemctl_return_value(service_name):
    """
    Used to check the status of service and return the status
    Args:
        service_name: service name

    Returns: Exit status of the command
        For more detail refer link --> https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8

    """
    cmd = 'systemctl status ' + service_name
    logger.debug("Command is %s", cmd)
    return execute_command_and_return_value(cmd)

@allure.step('Checking service status of {service_name} for {timeout} sec')
def status_service_systemctl_in_loop(service_name: str, timeout: float) -> bool:
    """
    Function is useful to check the service status for the given amount of time,
    for example you have to wait for the service to up and running
    Args:
        service_name: Name of the service
        timeout: Max time need to check if service is not running

    Returns: Bool status, True if Passed, False in case service is not running

    """
    cmd = 'systemctl status {}'.format(service_name)
    start_time = time.time()
    expected_time = start_time + timeout
    logger.debug("start time -- {} and expected time -- {}".format(start_time,expected_time))
    while expected_time > time.time():
        service_status = execute_command_and_return_value(cmd)
        logger.debug("{} service status is {}".format(service_name,service_status))
        if service_status == 0:
            return True
        time.sleep(1)
    logger.debug("current time -- {} and expected time -- {}".format(time.time(), expected_time))
    service_logs = execute_command_and_return_console_output(cmd)
    logger.error("service is not running --> {}".format(service_logs))
    return False

def remount_device():
    """
    Remount the device to edit any files inside the TCU

    Returns: Exit status of the command

    0   :   success

    1   :   incorrect invocation or permissions

    2   :   system error (out of memory, cannot fork, no more loop devices)

    4   :   internal mount bug

    8   :   user interrupt

    16  :   problems writing or locking /etc/mtab

    32  :   mount failure

    64  :   some mount succeeded

    """
    cmd = 'mount -o remount,rw /'
    logger.debug("Mount command - %s", cmd)
    return execute_command_and_return_value(cmd)

def systemctl_service_restart(service_name):
    """
    Restarts specified service
    Args:
        service_name: Name of the service

    Returns: Int value
    0 : success
    3 : if service is not running
    4 : if service is not exist or active
    refer link --> https://freedesktop.org/software/systemd/man/systemd.exec.html#id-1.20.8
    """
    cmd = 'systemctl restart ' + service_name
    logger.debug("Command is - %s", cmd)
    return execute_command_and_return_value(cmd)

def reboot_over_ssh():
    """
    Reboots TCU over SSH interface
    Returns: None
    """
    status = execute_command_and_return_console_output("/sbin/reboot -f")
    logger.debug("Device reboot status is --> {}".format(status))
    time.sleep(2)

@allure.step("Rebooting TCU over SSH")
def async_reboot_over_ssh():
    """
    Reboots TCU over SSH interface in a different process

    Returns: none

    """
    pool = ThreadPool(processes=1)
    pool.apply_async(reboot_over_ssh, ())
    time.sleep(5)
    logger.debug("Device rebooted")
    pool.terminate()

if __name__ == "__main__":
    print(execute_command_and_return_value("pwd"))