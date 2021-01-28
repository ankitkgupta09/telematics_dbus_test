import allure
import pytest
import time
import os
from pathlib import Path

from interface.utils import connection_wait_in_loop, service_check, TCU_IP, get_configuration_from_file
from interface.AllureReport.AllureInterface import allure_test_link
from interface.SSH.SSHInterface import execute_command_and_return_console_output, status_service_systemctl_in_loop
from config import interfaces, L1,L2,config,ETH_CONNECTION_TIMEOUT,logger, LOGPATH,under_development,stability
import utility.SoftwareUpdate.SoftwareUpdateUtility as swupdateutility
from interface.wireshark.wireshark_Interface import ip_logs
from interface.vbf.vbf import vbf
from utility.Diagnostics.DiagnosticsUtility import *
from doip_client.doip import *
from interface.AllureReport.AllureInterface import update_kpi_in_allure

# <editor-fold desc="Service list">
COMMON_SERVICE_LIST = eval(config.get('services', 'COMMON_SERVICE_LIST'))
ONLY_APP_ROOTFS_SERVICE_LIST = eval(config.get('services', 'ONLY_APP_ROOTFS_SERVICE_LIST'))
ONLY_BOOTLOADER_SERVICE_LIST = eval(config.get('services', 'ONLY_BOOTLOADER_SERVICE_LIST'))
SERVICE_LIST_APP = COMMON_SERVICE_LIST + ONLY_APP_ROOTFS_SERVICE_LIST
SERVICE_LIST_BOOT = COMMON_SERVICE_LIST + ONLY_BOOTLOADER_SERVICE_LIST
# </editor-fold>

wireshark_interface = interfaces.get('logging', 'wireshark_interface')

swdl = pytest.mark.SWDL

CONFIG_FILE_PATH = '/etc/platform.conf.in'

BOOTCONFIG_VALUES = [0, 128, 130, 15]
BOOTCONFIG_ALM_IDS = ["52483", "52481", "52479", "52482"]

@pytest.fixture(scope='module', autouse=True)
def doip_connect(request,sock_connection):
    logger.info("just a fixture call start of this module")

@pytest.fixture(scope='module', autouse=True)
def ip_logging(request):
    logger.debug("Starting IP log capturing")
    ip_log_object = ip_logs(wireshark_interface, request.node.name)
    ip_log_object.start_ip_capture_async()
    time.sleep(6)

    def stop_test():
        logger.debug("Stop the IP log capture")
        ip_log_object.stop_ip_logs()
    request.addfinalizer(stop_test)


@pytest.fixture(scope="class")
def bootconfig_record(request):
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    logger.debug("{}".format(swupdateutility.return_current_partition()))
    ret_val = swupdateutility.imageSelection_getbootconfig()
    def return_to_old_boot_config():
        connection_wait_in_loop(TCU_IP)
        swupdateutility.imageSelection_setbootconfig(ret_val)
        swupdateutility.reset_tcu(1)
        logger.debug("{}".format(swupdateutility.return_current_partition()))
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    request.addfinalizer(return_to_old_boot_config)


@allure.suite("Software Update")
@pytest.mark.usefixtures("bootconfig_record")
class TestBasicSoftwareDetails(object):
    """

    """
    Test_Case_ID_52501 = (swupdateutility.Software_Partition.APPLICATION, SERVICE_LIST_APP,"52501")
    Test_Case_ID_52502 = (swupdateutility.Software_Partition.BOOTLOADER, SERVICE_LIST_BOOT,"52502")

    test_case_list = [Test_Case_ID_52502]

    @pytest.mark.parametrize("partition,service_list,alm_id", test_case_list)
    @under_development
    def test_software_details(self, partition, service_list, alm_id):
        """Verify basic software build details, verify service is running or not"""
        allure_test_link(alm_id)
        swupdateutility.switch_to_active_partition(partition)
        build_details = execute_command_and_return_console_output("cat /etc/nets-build-details")
        logger.debug("Build details of {0} -->{1}".format(partition, build_details))
        service_check(service_list)

    test_case_list = [("/mnt/data/persistency/public/file/","psap","drwxr-xr-x","67524")]

    @L2
    @pytest.mark.parametrize("file_path,file,permission,alm_id", test_case_list)
    def test_verify_files(self,file_path,file,permission,alm_id):
        allure_test_link(alm_id)
        file_path_content = execute_command_and_return_console_output("ls -l {}".format(file_path))
        assert file in file_path_content,"{} is not found in {}, present content is {}".format(file,file_path,file_path_content)
        for l in file_path_content.split('\n'):
            if file in l:
                assert permission == l.split(" ")[0],"File permission is {}, not eq to {}".format(l,permission)

mount_partitions_dict = {
    0 : {
        "rootfs" : "/dev/mmcblk0p3 on /",
        "local-config" : "/dev/mmcblk0p8 on /mnt/config",
        "modem" : "/dev/mmcblk0p4 on /mnt/radio0",
    },
    128 : {
        "rootfs" : "/dev/mmcblk0p7 on /",
    },
    130 : {
        "rootfs" : "/dev/mmcblk0p14 on /",
    },
    15 : {
        "rootfs": "/dev/mmcblk0p10 on /",
        "local-config": "/dev/mmcblk0p15 on /mnt/config",
        "modem": "/dev/mmcblk0p11 on /mnt/radio0",
    }
}

@allure.suite("Software Update")
@pytest.mark.usefixtures("bootconfig_record")
class TestImageSelection(object):
    @under_development
    @pytest.mark.parametrize("bootconfig, bootconfigalmids", zip(BOOTCONFIG_VALUES, BOOTCONFIG_ALM_IDS))
    def test_check_mount_points_after_switch(self, bootconfig, bootconfigalmids):
        allure_test_link(bootconfigalmids)
        swupdateutility.imageSelection_setbootconfig(bootconfig)
        swupdateutility.reset_tcu(1)
        connection_wait_in_loop(interfaces.get("ssh", "ip"))
        bootconfig = swupdateutility.imageSelection_getbootconfig()
        mount_output = execute_command_and_return_console_output("mount")
        # logger.debug("Mount output is {}".format(mount_output))
        number_of_mount_points = len(mount_partitions_dict[bootconfig])
        count = 0
        logger.debug("Number of mount points is {}".format(number_of_mount_points))
        error_output_string = ""
        for i in mount_partitions_dict[bootconfig]:
            if mount_partitions_dict[bootconfig][i] in mount_output:
                count += 1
                logger.debug("{} found in mount output".format(mount_partitions_dict[bootconfig][i]))
            else:
                error_output_string += "{} {} not found amoong the list of mount points".format(i, mount_partitions_dict[bootconfig][i])
        assert count == number_of_mount_points, "All expected mount points NOT present in mount output \n{}".format(error_output_string)

file_name_regexp = {
    "SWLM" : "*32334387*",
    "SWL2" : "*32334427*",
    "SWP1" : "*32334389*",
    "SWBP" : "*32334428*"
}

vbf_file_map = dict()

block_number_map = {
    "1000" : ("VBT", "Verification Block Table"),
    "2000" : ("CBT", "Compatibility Block Table"),
    "10000000" : ("app_boot.img", "Application Kernel"),
    "20000000" : ("app_rootfs.ext4", "Application RootFS"),
    "30000000" : ("tz.img", "TEE Image"),
    "50000000" : ("tcam_ioc.bin", "IOC"),
    "60000000" : ("tcam_wuc.s19uc", "WUC"),
    "E0000000" : ("btld_boot.img", "Bootloader kernel"),
    "F0000000" : ("btld_rootfs.ext4", "Bootloader RootFS"),
    "D0000000" : ("lk.img", "Little Kernel"),
    "70000000" : ("radio0.ext4", "Modem binary"),
    "90000000" : ("localcfg.ext4", "Local Config")
}

def get_paths():
    # path = os.path.join("..", "Log", "Build")
    path = os.path.join(LOGPATH, "Build")
    p_path = Path(path)
    list_of_files = list(p_path.glob('*.vbf'))
    list_of_paths = []
    for i in list_of_files:
        absolute_path = str(i.absolute())
        list_of_paths.append(absolute_path)
        for j in file_name_regexp:
            if i.match(file_name_regexp[j]):
                vbf_file_map[j] = absolute_path
    return list_of_paths

def enter_programming():
    enter_prog = ('10 02', None),
    command = enter_prog + ("59477: enter programming session",)
    validate_diagnostics_requests(command)
    ip_connection = connection_wait_in_loop(TCU_IP, 4)

def hash_check(metadata):
    # check_memory_command = ('22 d0 1c', '62 d0 1c' + metadata['Block1']['Hash']),
    check_memory_command = ('22 d0 1c', None),
    command = check_memory_command + (None,)
    # timing = validate_timing_parameter(command)
    try:
        validate_diagnostics_requests(command)
    except Exception as e:
        logger.debug("{}".format(e))
    # return timing[check_memory_command[0]]
    return 0

def check_memory_command(head_data):
    # Read data by identifier for verification of sw_signature_dev
    check_memory_command_with_sig = ('31 01 02 12 ' + str(head_data['sw_signature_dev']), '71 01 02 12 10 00'),
    command = check_memory_command_with_sig + (None,)
    timing = validate_timing_parameter(command)
    logger.debug("Timing is dictionary {}".format(timing))
    for i in timing.values():
        return i

def complete_and_compatible_command():
    c_and_c_command = ('31 01 02 05 ', '71 01 02 05 10 00 00 00 00'),
    command = c_and_c_command + (None,)
    timing = validate_timing_parameter(command)
    # return timing[c_and_c_command[0]]
    for i in timing.values():
        return i

def ecu_reset_command():
    ecu_reset_command = ('11 81', None),
    v_reset = ecu_reset_command + (None,)
    validate_diagnostics_requests(v_reset)

vbf_name_map = {
    swupdateutility.BootConfigBits.Persistence.name : "SWP1",
    swupdateutility.BootConfigBits.Bootloader.name : "SWBP",
    swupdateutility.BootConfigBits.Application.name : "SWLM",
    swupdateutility.BootConfigBits.Modem.name : "SWL2",
}

def swdl_wrapper(path):
    vbf_obj = vbf()
    head_data, metadata = vbf_obj.return_header_and_metadata(path)
    logger.debug("Head Data is %s", head_data)
    logger.debug("Metadata is %s", metadata)
    response_dl = software_download(path)
    logger.debug("Response is %s", response_dl)
    logger.debug("Type of Response is %s", type(response_dl))
    assert len(response_dl) != 0, "Response was empty"
    assert response_dl["status"] == "Success", "Status was not success"
    total_time_taken = 0
    for j in response_dl["blocks"]:
        logger.info("time taken to transfer {} is {}".format(block_number_map[j][1], response_dl["blocks"][j]))
        total_time_taken += int(response_dl["blocks"][j])
    logger.info("Total Time taken to transfer is {}".format(total_time_taken))
    hash_check_time = hash_check(metadata)
    logger.info("Time for hash check is {}".format(hash_check_time))
    total_time_taken += hash_check_time
    check_memory_time = check_memory_command(head_data)
    logger.info("Time for check memory is {}".format(check_memory_time))
    total_time_taken += check_memory_time
    result = "Time for hash check is {} \r\n " \
             "Time for check memory is {} \r\n " \
             "Total Time taken to transfer is {}\n".format(check_memory_time, hash_check_time, total_time_taken)
    update_kpi_in_allure(result)
    return total_time_taken


total_time = 0
@allure.suite("Software Update")
class TestFlashVBF(object):
    @pytest.fixture(scope="class", autouse=True)
    def pre_version_check(self, request):
        swupdateutility.version_check()
        enter_programming()
        initial_boot_config = swupdateutility.return_current_partition()
        def post_version_check():
            global total_time
            logger.info("Total time for swdl_wrapper is {}".format(total_time))
            candc_time = complete_and_compatible_command()
            logger.info("Time for complete and compatible is {}".format(candc_time))
            update_kpi_in_allure("Time for complete and compatible is {}".format(candc_time))
            total_seconds = (total_time + candc_time) / 1000
            logger.info("Total time taken for Software Update is {} seconds".format(total_seconds))
            update_kpi_in_allure("Total time taken for Software Update is {} seconds".format(total_seconds))
            ecu_reset_command()
            swupdateutility.version_check()
            final_boot_config = swupdateutility.return_current_partition()
            for i in initial_boot_config:
                if i == swupdateutility.BootConfigBits.Partition.name:
                    if final_boot_config[i] == swupdateutility.BootConfigBits.Application.name:
                        logger.debug("In Application Partition")
                    else:
                        logger.debug("In Bootloader Partition")
                else:
                    if final_boot_config[i] == swupdateutility.mirror[initial_boot_config[i]]:
                        logger.debug("{} {}".format(i, final_boot_config[i]))
                    else:
                        logger.debug("{} {}".format(i, final_boot_config[i]))
        request.addfinalizer(post_version_check)

    """
    59477 - Two different versions of VBF files 3 times in succession
    58475 - Update same software 3 times in succession
    47385 - Trigger Software Update using VBF files
    59476 - VBF update to different version once
    59601 - Update old files
    """
    @swdl
    @pytest.mark.parametrize("vbf_name", get_paths())
    def test_flash_vbf(self, vbf_name):
        allure.dynamic.title("Flashing {}".format(vbf_name.split(os.sep)[-1]))
        global total_time
        total_time += swdl_wrapper(vbf_name)

"""
The following ALM IDS will be covered
59471 - SWLM - 3 times in succession
59474 - SWBP - 3 times in succession
59473 - SWP1 - 3 times in succession
59472 - SWL2 - 3 times in succession
"""
@allure.suite("Software Update")
class TestFlashVBFNTimes(object):
    @under_development
    @pytest.mark.parametrize("vbf_details", vbf_name_map.keys())
    def test_vbf_four_times(self, vbf_details):
        swupdateutility.version_check()
        enter_programming()
        current = swupdateutility.return_current_partition()[vbf_details]
        swdl_wrapper(vbf_file_map[vbf_name_map[vbf_details]])
        complete_and_compatible_command()
        ecu_reset_command()
        swupdateutility.version_check()
        next = swupdateutility.return_current_partition()[vbf_details]
        assert swupdateutility.mirror[current] == next

@allure.suite("Software Update")
class TestVBFHeaderSection(object):
    @under_development
    @pytest.mark.parametrize("vbf_name", get_paths())
    def test_vbf_header_section(self, vbf_name):
        allure_test_link("46538")
        list_of_fields = [
            "description",
            "sw_part_number",
            "sw_version",
            "sw_part_type",
            "ecu_address",
            "data_format_identifier",
            "verification_block_start",
            "verification_block_length",
            "verification_block_root_hash",
            "sw_signature_dev",
            "file_checksum",
        ]
        vbf_obj = vbf()
        count = 0
        exception_string = []
        head_data = vbf_obj.return_header_and_metadata(vbf_name)[0]
        for i in list_of_fields:
            try:
                assert i in head_data
                count += 1
                logger.debug("Field is {} Value is {}".format(i, head_data[i]))
            except:
                exception_string.append(i)
        assert count == len(list_of_fields), "Missing fields are {}".format(' '.join(exception_string))