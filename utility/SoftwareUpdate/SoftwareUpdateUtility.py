"""
This module contains Software update helper functions, which can be called inside the test case

"""
# -*- coding: UTF-8 -*-
import allure
import time
from multiprocessing.pool import ThreadPool
from enum import IntEnum

from config import interfaces,config,ETH_CONNECTION_TIMEOUT,logger
from interface.SSH.SSHInterface import execute_command_and_return_value, reboot_over_ssh, \
    execute_command_and_return_console_output,status_service_systemctl_in_loop
from interface.utils import connection_wait_in_loop,TCU_IP,space_separated_string,string_to_asii,is_hex
from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition


def switch_partition(partition: str) -> bool:
    """
    This function is used to switch to the desired partition.
    Args:
        partition: partition Number you want to switch refer software update class Software_Partition
    Examples:
        from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition
        switch_partition(Software_Partition.APPKERNEL1)
    Returns: None
    """
    # partition = PadHexwithLead0s(str(partition))
    current_partition = get_current_partition()
    partition_to_switch = partition_number_to_string_conversion(hex(int(partition)))
    logger.debug("Current partition is --> {}".format(current_partition))
    if current_partition == partition_to_switch:
        logger.debug("already in required partition")
        return True
    cmd = '/opt/bin/imageSelection SetBootConfig {}'.format(partition)
    logger.debug("partition switch cmd used --> {}".format(cmd))
    switch_command_status = execute_command_and_return_value(cmd)
    assert switch_command_status == 0, "Fail to set the bootconfig to --> {}".format(partition)
    time.sleep(2)
    async_reset_tcu(1)
    time.sleep(1)
    current_partition = get_current_partition()
    logger.debug("{} and {}".format(current_partition, partition))
    assert current_partition == partition_to_switch, "current partition is not same as switched partition"

def check_nth_byte(value, n):
    """
    This will check if the nth bit from the left is set
    Args:
        value: Value whose bit field needs to be checked
        n: This will determine which bit field needs to be checked

    Returns: nth bit value 0 or 1

    """
    return (value >> (n - 1)) & 1

def check_left_right_partition(boot_config: int, bit_value: int) -> Software_Partition:
    """

    Args:
        boot_config:
        bit_value:

    Returns:

    """
    bit_status = check_nth_byte(boot_config, bit_value)
    if bit_status == 1:
        return Software_Partition.RIGHT
    elif bit_status == 0:
        return Software_Partition.LEFT

def partition_number_to_string_conversion(partition: str) -> list:
    """
    convert the boot config value to partition list
    Args:
        partition: boot config value for Example -00 ,0d ,80, 8f

    Returns:

    """
    output_decimal = int(partition, 16)
    partition = []
    # APPLICATION - BOOTLOADER check
    eighth_bit_check = check_nth_byte(output_decimal, 8)
    if eighth_bit_check == 1:
        # LEFT - RIGHT partition check
        partition.append(Software_Partition.BOOTLOADER)
        partition.append(check_left_right_partition(output_decimal, 2))
    elif eighth_bit_check == 0:
        # LEFT - RIGHT partition check
        partition.append(Software_Partition.APPLICATION)
        partition.append(check_left_right_partition(output_decimal, 1))
    return partition

def get_bootconfig_value(retry=1):
    """
    Executes "imageSelection GetBootConfig and parses the string output
    :return: hexadecimal string returned by command
    """
    get_boot_mode_value = None
    get_boot_partition_value = None
    get_boot_mode = "/opt/bin/imageSelection GetBootMode"
    get_boot_partition = "/opt/bin/imageSelection GetBootPartition"
    counter = 0
    while retry>0:
        if counter !=0:
            connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        get_boot_mode_value = execute_command_and_return_value(get_boot_mode)
        get_boot_partition_value = execute_command_and_return_value(get_boot_partition)
        counter +=1
        retry -=1

    return get_boot_mode_value, get_boot_partition_value

def get_current_partition() -> list:
    """
        This will return a list containing two elements
        First element will contain if it's APPLICATION or BOOTLOADER
        Second element will contain if it's LEFT or RIGHT

    Returns: List which contain the partitions info ["APPLICATION", "LEFT]

    """
    mode, partition = get_bootconfig_value()
    # assert mode is not None, "Mode is not proper"
    # assert partition is not None, "Partion is not proper"
    # if mode == Software_Partition.APPLICATION
    return [mode,partition]

def reset_tcu(option):
    """

    :param option:
    :return:
    """
    cmd = "/opt/bin/imageSelection ResetTCU {}".format(option)
    reset_response = execute_command_and_return_console_output(cmd)
    logger.debug("RestTCU response -- {}".format(reset_response))
    # assert reset_response == 0,"RestTCU is not successfully"
    return True

@allure.step("RestTCU with option {option}")
def async_reset_tcu(option):
    pool = ThreadPool(processes=1)
    reset_response = pool.apply_async(reset_tcu, (option,))
    eth_down = connection_wait_in_loop(TCU_IP, 10, connection_status=False)
    # assert eth_down < 10,"SSH is working even after ResetTCU"
    eth_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    assert eth_connection < ETH_CONNECTION_TIMEOUT, "No ETH connection after reboot"
    pool.terminate()

def get_software_part_number(part_number: str) -> str:
    """
    Get the software part number from the build
    Args:
        part_number: part number possible values are -SWLM ,SWBP,SWP1,SWL2

    Returns: Software part Number

    """

    try:
        part_number_list = execute_command_and_return_console_output("cat /mnt/data/version").split('\n')
        for part in part_number_list:
            if part_number in part:
                temp = part.split("_")
                required_part_number = space_separated_string(temp[-1][:-2]) + ' 20 ' + string_to_asii(temp[1][-2:])
                # required_part_number = space_separated_string(temp[-2]) + ' 20 ' + string_to_asii(temp[-1])
                return required_part_number
        logger.debug("No part number found in the version list")
    except Exception as e:
        logger.debug("exception while fetching part number --> {}".format(e))
        pass
    return config.get('DOIP_SOFTWARE_PART_NUMBER',part_number)

def switch_to_active_partition(partition):
    """
    Switch to active partition only
    :param partition: partition you want to switch Software_Partition.APPLICATION or Software_Partition.BOOTLOADER
    :return: Bool
    """
    current_partition = get_current_partition()
    logger.debug("Current partition is {} Type is --> {}".format(current_partition, type(current_partition)))
    if current_partition[0] != partition:
        cmd = '/opt/bin/imageSelection SetBootMode {}'.format(partition)
        logger.debug("partition switch cmd used --> {}".format(cmd))
        switch_command_status = execute_command_and_return_value(cmd)
        assert switch_command_status == 0, "Fail to set the bootconfig to --> {}".format(partition)
        time.sleep(2)
        async_reset_tcu(1)
        time.sleep(1)
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    else:
        logger.debug("TCU already in required partition")
        return True
    return True


def image_selection_help():
    """
    List's the help option for imageSelection
    :return: Returns Bool Value
    """
    status = execute_command_and_return_console_output("/opt/bin/imageSelection --help|grep Example|wc -l|tr -d '\n'")
    cmd = "/opt/bin/imageSelection --help"
    if status == "1":
        output = execute_command_and_return_console_output(cmd)
        logger.debug("List's the help option for imageSelection --> {}".format(output))
        return True
    else:
        return False

def lock_partition(option):
    """
    Locks the partition
    :param option: 1/0
    :return:Returns true on success.
    """
    cmd = "/opt/bin/imageSelection LockBootConfig {}| grep 'New boot configuration saved for future boot.'|wc -l|tr -d '\n'".format(option)
    output = execute_command_and_return_console_output(cmd)
    if output == "1":
        logger.debug("Status of the  LockBootConfig --> {} --".format(output))
        return True
    else:
        return False       

def wuc_version():
    """
    Gets you the current WUC Version
    :return: Returns wuc version.
    """
    cmd = "/opt/bin/imageSelection GetWucVersion|cut -d ' ' -f3"
    wuc_value = execute_command_and_return_console_output(cmd)
    logger.debug("{}".format(wuc_value))
    return wuc_value

def wuc_sw_update(path):
    """
    Updates the software that has been passed
    :param path:Need to mention the path in which software is present.
    :return:Returns true on success.
    """
    cmd = "/opt/bin/wucSwUpdateUtility {}|grep 'Software Update Completed.'|wc -l|tr -d '\n'".format(path)
    output = execute_command_and_return_console_output(cmd)
    if output == "1":
        logger.debug("List's the help option for imageSelection --> {}".format(output))
        return True
    else:
        return False

def imageSelection_setbootconfig(value):
    cmd = '/opt/bin/imageSelection SetBootConfig {}'.format(value)
    logger.debug("partition switch cmd used --> {}".format(cmd))
    switch_command_status = execute_command_and_return_value(cmd)
    assert switch_command_status == 0, "Fail to set the bootconfig to --> {}".format(value)

def imageSelection_getbootconfig(retry=5):
    output, parsed_output = get_bootconfig_value()
    assert is_hex(parsed_output), "GetBootConfig Failed with error {}".format(output)
    return int(parsed_output, 16)

class BootConfigBits(IntEnum):
    Partition = 0
    Persistence = 1
    Modem = 2
    Bootloader = 3
    Application = 4
    Left = 5
    Right = 6

bitmap_order = [
    BootConfigBits.Partition,
    BootConfigBits.Persistence,
    BootConfigBits.Modem,
    BootConfigBits.Bootloader,
    BootConfigBits.Application,
]
bits = [8,4,3,2,1]
bitmap = dict(zip(bitmap_order, bits))

mirror = {
    BootConfigBits.Left.name : BootConfigBits.Right.name,
    BootConfigBits.Right.name : BootConfigBits.Left.name,
}

def return_boot_config(bootconfig):
    bootconfig_dict = dict()
    for i in bitmap_order:
        if i == BootConfigBits.Partition:
            if check_nth_byte(bootconfig, bitmap[i]):
                bootconfig_dict[BootConfigBits.Partition.name] = BootConfigBits.Bootloader.name
            else:
                bootconfig_dict[BootConfigBits.Partition.name] = BootConfigBits.Application.name
        if i == BootConfigBits.Persistence:
            if check_nth_byte(bootconfig, bitmap[i]):
                bootconfig_dict[BootConfigBits.Persistence.name] = BootConfigBits.Right.name
            else:
                bootconfig_dict[BootConfigBits.Persistence.name] = BootConfigBits.Left.name
        if i == BootConfigBits.Modem:
            if check_nth_byte(bootconfig, bitmap[i]):
                bootconfig_dict[BootConfigBits.Modem.name] = BootConfigBits.Right.name
            else:
                bootconfig_dict[BootConfigBits.Modem.name] = BootConfigBits.Left.name
        if i == BootConfigBits.Bootloader:
            if check_nth_byte(bootconfig, bitmap[i]):
                bootconfig_dict[BootConfigBits.Bootloader.name] = BootConfigBits.Right.name
            else:
                bootconfig_dict[BootConfigBits.Bootloader.name] = BootConfigBits.Left.name

        if i == BootConfigBits.Application:
            if check_nth_byte(bootconfig, bitmap[i]):
                bootconfig_dict[BootConfigBits.Application.name] = BootConfigBits.Right.name
            else:
                bootconfig_dict[BootConfigBits.Application.name] = BootConfigBits.Left.name
    return bootconfig_dict

def return_current_partition():
    bootconfig = imageSelection_getbootconfig()
    bootconfig_dict = return_boot_config(bootconfig)
    return bootconfig_dict

def version_check():
    commands = ["cat /etc/nets-build-details", "cat /mnt/data/version"]
    for com in commands:
        ret_val = execute_command_and_return_console_output(com)
        logger.debug("output of {} is {}".format(com, ret_val))
    logger.debug("BootConfig is {}".format(return_current_partition()))

if __name__ == "__main__":
    from doip_client.doip import connect_uds_server, disconnect_uds_server
    SOCKET_ADDRESS = interfaces.get('DOIP', 'SOCKET_ADDRESS')

    logger.debug("DOIP connection function called")
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    status = status_service_systemctl_in_loop('uds_diagnostic_server.service', timeout=10)
    assert status, "uds_diagnostic_server.service service is not running"
    logger.debug("GRPC UDS connection using connect_uds_server function")
    status = connect_uds_server(SOCKET_ADDRESS)
    assert status, "GRPC UDS connection is not connected."

    print(get_current_partition())
    print(switch_to_active_partition(Software_Partition.BOOTLOADER))
    print(get_current_partition())
    print(execute_command_and_return_console_output("mount"))

    uds_disconnect = disconnect_uds_server()