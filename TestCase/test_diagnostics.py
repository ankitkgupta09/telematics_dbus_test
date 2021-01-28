from datetime import time

import pytest
from doip_client.doip import *
from interface.SSH.SSHInterface import status_service_systemctl_in_loop, async_reboot_over_ssh, \
    execute_command_and_return_console_output, status_service_systemctl_return_value
from interface.utils import connection_wait_in_loop, get_configuration_from_file, restart
from interface.AllureReport.AllureInterface import allure_test_link, update_kpi_in_allure
from utility.SoftwareUpdate.SoftwareUpdateUtility import get_current_partition, switch_to_active_partition, \
    async_reset_tcu
from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition
from config import interfaces, L1, L2, L3, stability, KPI, peripherals, ETH_CONNECTION_TIMEOUT, logger
from utility.Diagnostics.DiagnosticsUtility import *
from gta_release.generic_libs.interfaces.dlt import DltLib

under_development = pytest.mark.under_development
SOCKET_ADDRESS = interfaces.get('DOIP', 'SOCKET_ADDRESS')

POWER_SUPPLY_TYPE = peripherals.get('powersupply', 'type')

CONFIG_FILE_PATH = '/etc/platform.conf.in'


@pytest.fixture(scope='module', autouse=True)
def doip_connect(request, sock_connection):
    logger.info("just a fixture call start of this module")

def setup_module(module):
    ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
    time.sleep(1)
    status = status_service_systemctl_in_loop('uds_diagnostic_server.service', timeout=20)
    assert status, "uds_diagnostic_server.service service is not running"
    ip_used_in_tcu = get_configuration_from_file("uds_tester_handler_ip_address:", CONFIG_FILE_PATH)
    port_used_in_tcu = get_configuration_from_file("uds_tester_handler_port:", CONFIG_FILE_PATH)
    logger.debug("Current UDS IP set in TCU --> {}".format(ip_used_in_tcu))
    logger.debug("Current UDS PORT set in TCU --> {}".format(port_used_in_tcu))
    # assert wait_for_uds_server(), "uds service is not connected"


@pytest.fixture(scope="function")
def switch_to_app(request):
    """Verify that we are starting from app partition only"""
    switch_to_active_partition(Software_Partition.APPLICATION)

# @pytest.fixture(scope="module", autouse=True)
# def sock_connection(request):
#     connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
#     logger.debug("GRPC UDS connection using connect_uds_server function")
#     status = connect_uds_server(SOCKET_ADDRESS)
#     assert status, "GRPC UDS connection is not connected."
#
#     def close_sock():
#         switch_to_active_partition(Software_Partition.APPLICATION)
#         logger.debug("Closing the connection")
#         uds_disconnect = disconnect_uds_server()
#         logger.debug("uds connection status --> {}".format(uds_disconnect))
#
#     request.addfinalizer(close_sock)


# noinspection PyPep8Naming,PyPep8Naming
@allure.parent_suite("Diagnostics")
@allure.suite("333: Sanity Test")
@allure.sub_suite("APPKERNEL1 PARTITION")
@pytest.mark.usefixtures("switch_to_app")
class Test_DID(object):

    # <editor-fold desc="Test Case List">
    Test_Case_ID_47757 = SID_10_01 + check_default_session + SID_10_03 + check_extended_session + SID_10_01 + \
                         check_default_session + SID_10_81 + check_default_session + SID_10_83 + \
                         check_extended_session + SID_10_81 + check_default_session + ("47757",)

    Test_Case_ID_60991 = SID_10_01 + check_default_session + SID_10_03 + check_extended_session + SID_10_81 + \
                         check_default_session + SID_10_83 + check_extended_session + SID_10_01 + \
                         check_default_session + ("60991",)

    Test_Case_ID_60993 = SID_10_81 + check_default_session + read_part_number_20 + ("60993",)

    Test_Case_ID_60994 = SID_10_81 + check_default_session + read_ECU_core_assembly_part + ("60994",)

    Test_Case_ID_60995 = SID_10_81 + check_default_session + read_sw_part_number + ("60995",)

    Test_Case_ID_61003 = SID_10_82 + check_programming_session + read_part_number_21 + ("61003",)

    Test_Case_ID_61004 = SID_10_82 + check_programming_session + read_part_number_25 + ("61004",)

    # </editor-fold>

    DOIP_REQUEST = [Test_Case_ID_47757, Test_Case_ID_60991, Test_Case_ID_60993,
                    Test_Case_ID_60994, Test_Case_ID_60995, Test_Case_ID_61003,
                    Test_Case_ID_61004
                    ]

    @pytest.mark.parametrize("test_set", DOIP_REQUEST)
    @L1
    def test_did_in_app(self, test_set):
        """Verify the response of Given DID in app mode"""
        validate_diagnostics_requests(test_set)

    @L1
    @stability
    def test_switch_to_bootloader(self):
        """The intend is to switch to bootloader from application partition"""
        switch_to_active_partition(Software_Partition.APPLICATION)
        # Stability test case ID 61951: Check Switch to Bootloader Partition using 0x1002 request
        test_set = SID_10_02 + check_programming_session + ("61002",)
        validate_diagnostics_requests(test_set)
        setup_module(Test_DID)
        current_partition = get_current_partition()
        logger.debug("Current partition after running the DID --> {}".format(current_partition))
        assertion(current_partition[0], '==', Software_Partition.BOOTLOADER, "Partition is not switch to Bootloader")


# noinspection PyPep8Naming
@allure.parent_suite("Diagnostics")
@allure.suite("281: Diagnostic: Session Control 0x10")
class Test_diagnostic_session_control(object):
    # <editor-fold desc="Test Case List">
    Test_Case_ID_47049 = SID_10_01 + SID_10_81 + check_default_session + Enter_into_Programming_Session_without_Security_Access + SID_10_01 + \
                         Enter_into_Programming_Session_without_Security_Access + SID_10_81 + check_default_session + Enter_Extended_Session + \
                         SID_10_01 + Enter_Extended_Session + SID_10_81 + check_default_session + ("47049",)

    Test_Case_ID_47110 = SID_10_01 + SID_10_02 + SID_10_01 + SID_10_82 + check_programming_session + \
                         SID_10_02 + SID_10_02 + SID_10_82 + check_programming_session + SID_10_01 + \
                         Enter_Extended_Session + SID_10_02 + SID_10_01 + Enter_Extended_Session + \
                         SID_10_82 + check_programming_session + Exit_Programming_Session_by_Default_Session + ("47110",)

    Test_Case_ID_47118 = SID_10_01 + SID_10_03 + SID_10_01 + SID_10_83 + check_extended_session \
                         + Enter_into_Programming_Session_without_Security_Access + \
                         SID_10_03_negative + check_programming_session + \
                         SID_10_83_negative + check_programming_session + SID_10_01 + SID_10_03 + SID_10_83 + \
                         check_extended_session + SID_10_03 + ("47118",)

    Test_Case_ID_59580 = SID_10_01_81 + SID_10_02_82 + SID_10_03_83 + incorrect_DLC_SID_10 + \
                         Enter_into_Programming_Session_without_Security_Access + Tester_present + SID_10_03_negative + \
                         Exit_Programming_Session_by_Default_Session + incorrect_sub_function_SID_10 + ("59580",)

    # </editor-fold>

    doip_session_control_test_case = [pytest.param(Test_Case_ID_47049, marks=L2),
                                      pytest.param(Test_Case_ID_47110, marks=L2),
                                      pytest.param(Test_Case_ID_47118, marks=L2),
                                      pytest.param(Test_Case_ID_59580, marks=L2),]

    @pytest.mark.parametrize("test_set", doip_session_control_test_case)
    def test_DID_session_control(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_61498 = SID_10_01 + SID_10_81 + SID_10_03 + SID_10_81 + SID_10_02 + SID_10_01 + ("61498",)

    test_case_list = [Test_Case_ID_61498]

    @L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_session_control_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67197 = SID_10_01_no_response + SID_10_02_no_response + SID_10_03_no_response + ("67197",)
    test_case_list = [Test_Case_ID_67197]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_session_control_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)

    Test_Case_ID_47120 = with_timing(SID_10_01, 50) + ("47120",)

    Test_Case_ID_62319 = with_timing(SID_10_03, 50) + SID_10_01 + ("62319",)

    Test_Case_ID_62320 = SID_10_01 + with_timing(SID_10_02, 40) + Exit_Programming_Session_by_Default_Session + ("62320",)

    test_case_list = [Test_Case_ID_47120,Test_Case_ID_62319,Test_Case_ID_62320]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_time_parameter(self, test_set):
        validate_timing_parameter(test_set)


@allure.parent_suite("Diagnostics")
@allure.suite("214: Diagnostic: Read Data By Identifier - Service Identifier 0x22")
@pytest.mark.usefixtures("switch_to_app")
class TestDiagnosticReadDataByIdentifier(object):

    # <editor-fold desc="Test case List">
    Test_Case_ID_45860 = SID_10_01 + read_part_number_20 + ("45860",)

    Test_Case_ID_45862 = Enter_Extended_Session_with_Tester_Present + read_part_number_20 + ("45862",)

    Test_Case_ID_45867 = Enter_into_Programming_Session_without_Security_Access + read_part_number_20_NRC_31 + \
                         Exit_Programming_Session_by_Default_Session+ ("45867",)

    Test_Case_ID_45868 = F120_Incorrect_DLC + F120_Incorrect_DID + incorrect_service_but_correct_DLC_and_DID_20 + ("45868",)

    Test_Case_ID_45921 = SID_10_01 + read_ECU_core_assembly_part + ("45921",)

    Test_Case_ID_45923 = Enter_Extended_Session_with_Tester_Present + read_ECU_core_assembly_part + ("45923",)

    Test_Case_ID_45925 = Enter_into_Programming_Session_without_Security_Access + read_ECU_core_assembly_part +\
                         Exit_Programming_Session_by_Default_Session+ ("45925",)

    Test_Case_ID_45926 = F12A_Incorrect_DLC + incorrect_service_but_correct_DLC_and_DID_2A + F12A_Incorrect_DID + ("45926",)

    Test_Case_ID_45935 = SID_10_01 + read_sw_part_number + ("45935",)

    Test_Case_ID_45943 = Enter_Extended_Session_with_Tester_Present + read_sw_part_number + ("45943",)

    Test_Case_ID_45947 = Enter_into_Programming_Session_without_Security_Access + read_sw_part_number_NRC_31 +\
                         Exit_Programming_Session_by_Default_Session + ("45947",)

    Test_Case_ID_45952 = F12E_Incorrect_DLC + F12E_Incorrect_DID + incorrect_service_but_correct_DLC_and_DID_2E +\
                         Exit_Programming_Session_by_Default_Session + ("45952",)

    Test_Case_ID_45955 = Enter_and_verify_default_session + ("45955",)

    Test_Case_ID_45959 = Enter_into_Extended_Diagnostic_Session_and_verify + ("45959",)

    Test_Case_ID_45962 = Enter_into_Programming_Diagnostic_Session_and_verify + \
                         Exit_Programming_Session_by_Default_Session+ ("45962",)

    Test_Case_ID_45972 = SID_10_01+ F186_Incorrect_DLC + F186_Incorrect_DID + incorrect_service_but_correct_DLC_and_DID_86 + ("45972",)

    Test_Case_ID_45979 = SID_10_01 + read_part_number_25_negative + ("45979",)

    Test_Case_ID_45983 = Enter_Extended_Session_with_Tester_Present + read_part_number_25_negative + ("45983",)

    Test_Case_ID_45984 = Enter_into_Programming_Session_without_Security_Access + read_part_number_25 + \
                         Exit_Programming_Session_by_Default_Session +("45984",)

    Test_Case_ID_45987 = Enter_into_Programming_Session_without_Security_Access + F125_Incorrect_DLC + \
                         F125_Incorrect_DID + incorrect_service_but_correct_DLC_and_DID_25 +Exit_Programming_Session_by_Default_Session\
                         + ("45987",)

    Test_Case_ID_47601 = SID_10_01 + read_sw_part_number + ("47601",)

    Test_Case_ID_47921 = SID_10_01 + read_part_number_21_negative + Enter_Extended_Session_with_Tester_Present + read_part_number_21_negative + \
                         Enter_into_Programming_Session_without_Security_Access + read_part_number_21 +\
                         Exit_Programming_Session_by_Default_Session+ ("47921",)

    Test_Case_ID_50239 = Enter_into_Programming_Session_without_Security_Access + F121_Incorrect_DLC + \
                         F121_Incorrect_DID + DID_62_F1_21 +\
                         Exit_Programming_Session_by_Default_Session+ ("50239",)

    Test_Case_ID_59591 = SID_10_01 + read_ECU_core_assembly_part + ("59591",)

    Test_Case_ID_59590 = Programming_session_with_security_access + read_part_number_25 + \
                         Exit_Programming_Session_by_Default_Session+ ("59590",)

    Test_Case_ID_59589 = SID_10_01 + read_part_number_20 + ("59589",)

    Test_Case_ID_65175 = Write_Public_Key_Data_Record + SID_10_01 + read_part_number_1C + Enter_Extended_Session_with_Tester_Present + \
                         read_part_number_1C + Enter_into_Programming_Session_without_Security_Access + read_public_key_checksum_send_diag_request + \
                         Exit_Programming_Session_by_Default_Session + ("65175",)

    Test_Case_ID_65176 = Enter_into_Programming_Session_without_Security_Access + incorrect_DLC_and_correct_DID_C1 + \
                         incorrect_DLC_and_correct_DID_D0 + incorrect_DLC_and_correct_DID_31 + \
                         incorrect_SID + Exit_Programming_Session_by_Default_Session + ("65176",)

    Test_Case_ID_67489 = check_default_session + incorrect_DLC_NRC13 + incorrect_DLC1_NRC13 + incorrect_DLC2_NRC13 + \
                         incorrect_DLC_NRC31 + incorrect_DLC1_NRC31 + incorrect_DLC_NRC11 + ("67489",)

    Test_Case_ID_67488 = Enter_in_Default_Session + check_default_session + \
                         Remote_Vehicle_Data_Collection_data + Enter_Extended_Session + \
                         check_extended_session + Remote_Vehicle_Data_Collection_data + \
                         Enter_into_Programming_Session_without_Security_Access + \
                         check_programming_session + incorrect_DLC_nrc31 + Exit_Programming_Session_by_Default_Session \
                         + ('67488',)

    Test_Case_ID_67491 = Enter_in_Default_Session + check_default_session + \
                         Remote_Vehicle_Data_Collection_data + ('67491',)
    # </editor-fold>

    # doip_session_control_test_case = [Test_Case_ID_45860, Test_Case_ID_45862, Test_Case_ID_45867, Test_Case_ID_45868,
    #                                   Test_Case_ID_45921, Test_Case_ID_45923, Test_Case_ID_45925, Test_Case_ID_45926,
    #                                   Test_Case_ID_45935, Test_Case_ID_45943, Test_Case_ID_45947, Test_Case_ID_45952,
    #                                   Test_Case_ID_45955, Test_Case_ID_45959, Test_Case_ID_45962, Test_Case_ID_45972,
    #                                   Test_Case_ID_45979, Test_Case_ID_45983, Test_Case_ID_45984, Test_Case_ID_45987,
    #                                   Test_Case_ID_47601, Test_Case_ID_47921, Test_Case_ID_50239, Test_Case_ID_59591,
    #                                   Test_Case_ID_59590, Test_Case_ID_59589, Test_Case_ID_65176, Test_Case_ID_65175,
    #                                   pytest.param(Test_Case_ID_67492, marks=under_development),
    #                                   pytest.param(Test_Case_ID_67489, marks=under_development),]
    doip_session_control_test_case = [pytest.param(Test_Case_ID_45860, marks=L2),
                                      pytest.param(Test_Case_ID_45862, marks=L2),
                                      pytest.param(Test_Case_ID_45867, marks=L2),
                                      pytest.param(Test_Case_ID_45868, marks=L2),
                                      pytest.param(Test_Case_ID_45921, marks=L2),
                                      pytest.param(Test_Case_ID_45923, marks=L2),
                                      pytest.param(Test_Case_ID_45925, marks=L2),
                                      pytest.param(Test_Case_ID_45926, marks=L2),
                                      pytest.param(Test_Case_ID_45935, marks=L2),
                                      pytest.param(Test_Case_ID_45943, marks=L2),
                                      pytest.param(Test_Case_ID_45947, marks=L2),
                                      pytest.param(Test_Case_ID_45952, marks=L2),
                                      pytest.param(Test_Case_ID_45955, marks=L2),
                                      pytest.param(Test_Case_ID_45959, marks=L2),
                                      pytest.param(Test_Case_ID_45962, marks=L2),
                                      pytest.param(Test_Case_ID_45972, marks=L2),
                                      pytest.param(Test_Case_ID_45979, marks=L2),
                                      pytest.param(Test_Case_ID_45983, marks=L2),
                                      pytest.param(Test_Case_ID_45984, marks=L2),
                                      pytest.param(Test_Case_ID_45987, marks=L2),
                                      pytest.param(Test_Case_ID_47601, marks=L2),
                                      pytest.param(Test_Case_ID_47921, marks=L2),
                                      pytest.param(Test_Case_ID_50239, marks=L2),
                                      pytest.param(Test_Case_ID_59591, marks=L2),
                                      pytest.param(Test_Case_ID_59590, marks=L2),
                                      pytest.param(Test_Case_ID_59589, marks=L2),
                                      pytest.param(Test_Case_ID_65176, marks=L2),
                                      pytest.param(Test_Case_ID_65175, marks=L2),
                                      pytest.param(Test_Case_ID_67489, marks=under_development),
                                      pytest.param(Test_Case_ID_67488, marks=L2),
                                      pytest.param(Test_Case_ID_67491, marks=L1)]

    @pytest.mark.parametrize("test_set", doip_session_control_test_case)
    #@L2
    def test_did_read_data_by_identifier(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_46077 = SID_10_01 + with_timing(read_part_number_20, 50) + with_timing(read_ECU_core_assembly_part,
                                                                                        50) + \
                         with_timing(read_sw_part_number, 50) + with_timing(check_default_session, 50) + \
                         with_timing(read_part_number_25_negative, 50) + with_timing(read_part_number_21_negative, 50) + \
                         SID_10_01 + SID_10_02 + Tester_present_00 + security_access_27_01 + \
                         with_timing(read_part_number_20_NRC_31, 40) + with_timing(read_ECU_core_assembly_part, 40) + \
                         with_timing(read_sw_part_number_NRC_31, 40) + with_timing(check_programming_session, 40) + \
                         with_timing(read_part_number_25, 40) + with_timing(read_part_number_21, 40) + \
                         SID_10_01 + SID_10_03 + Tester_present_00 + with_timing(read_part_number_20, 50) + \
                         with_timing(read_ECU_core_assembly_part, 50) + with_timing(read_sw_part_number, 50) + \
                         with_timing(check_extended_session, 50) + \
                         with_timing(read_part_number_25_negative, 50) + with_timing(read_part_number_21_negative, 50) + \
                         ("46077",)

    Test_Case_ID_65177 = Write_Public_Key_Data_Record + Enter_into_Programming_Session_without_Security_Access + \
                         read_public_key_checksum_send_diag_request + Exit_Programming_Session_by_Default_Session + (
                         "65177",)
    Test_Case_ID_67251 = Enter_in_Default_Session + with_timing(read_part_number_20, 200) + \
                         with_timing(read_ECU_core_assembly_part, 200) + with_timing(read_sw_part_number, 200) + \
                         Enter_into_Programming_Session_without_Security_Access + check_programming_session + \
                         with_timing(read_part_number_21, 200) + with_timing(read_part_number_25, 200) + \
                         Exit_Programming_Session_by_Default_Session + ("67251",)

    Test_Case_ID_67492 = check_default_session + with_timing(Remote_Vehicle_Data_Collection_data, 200) + \
                         Enter_Extended_Session + check_extended_session + \
                         with_timing(Remote_Vehicle_Data_Collection_data, 200) + ("67492",)

    timing_parameter_test_case = [pytest.param(Test_Case_ID_46077, marks=L3),
                                  pytest.param(Test_Case_ID_65177, marks=L3),
                                  pytest.param(Test_Case_ID_67251, marks=L3),
                                  pytest.param(Test_Case_ID_67492, marks=under_development),]

    @pytest.mark.parametrize("test_time_set", timing_parameter_test_case)
    @L3
    def test_p2_server_timer(self, test_time_set):
        validate_timing_parameter(test_time_set)

    # <editor-fold desc="Test Case List With Functional address">
    Test_Case_ID_45871 = Enter_in_Default_Session + read_part_number_20 + ("45871",)

    Test_Case_ID_45928 = read_ECU_core_assembly_part + ("45928",)

    Test_Case_ID_45954 = read_sw_part_number + ("45954",)

    Test_Case_ID_45973 = SID_10_81 + SID_10_03 + Tester_present + check_extended_session + ("45973",)

    Test_Case_ID_46023 = SID_10_81 + SID_10_02 + read_part_number_25 + SID_10_01 + ("46023",)

    Test_Case_ID_60646 = SID_10_81 + SID_10_02 + read_part_number_21 + SID_10_01 + ("60646",)

    Test_Case_ID_45954 = Enter_in_Default_Session + read_sw_part_number + ("45954",)

    Test_Case_ID_67490 = Enter_in_Default_Session + check_default_session + \
                         Remote_Vehicle_Data_Collection_data + ('67490',)

    # </editor-fold>

    doip_session_control_with_functional_address = [Test_Case_ID_45871, Test_Case_ID_45928,Test_Case_ID_45954,
                                                    Test_Case_ID_45973, Test_Case_ID_46023, Test_Case_ID_60646,
                                                    Test_Case_ID_45954, Test_Case_ID_67490]

    @pytest.mark.parametrize("test_set", doip_session_control_with_functional_address)
    @L3
    def test_DID_read_data_by_identifier_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, address=AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67199 = current_session_no_response + ("67199",)
    Test_Case_ID_67493 = Remote_Vehicle_Data_Collection_data_No_Response + ("67493",)

    test_case_list = [Test_Case_ID_67199, Test_Case_ID_67493]
    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_DID_read_data_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, address=AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("232: Security Access – Service Identifier 0x27")
@pytest.mark.usefixtures("switch_to_app")
class TestSecurityAccessServiceIdentifier(object):
    """The purpose of this service is to provide a means to access data and/or diagnostic services,
    which have restricted access for security, emissions, or safety reasons.
    The security concept uses a seed and key relationship."""

    # <editor-fold desc="Test Case List">
    Test_Case_ID_46295 = SID_10_01 + security_access_27_01_NRC + ("46295",)

    Test_Case_ID_46296 = Enter_Extended_Session_with_Tester_Present + security_access_27_01_NRC_22 + ("46296",)

    Test_Case_ID_46297 = Enter_into_Programming_Session_without_Security_Access + security_access_27_01 +\
                         Exit_Programming_Session_by_Default_Session+ ("46297",)

    Test_Case_ID_46298 = Enter_into_Programming_Session_without_Security_Access + request_key_before_seed + \
                         request_for_seed_NRC_13 + request_for_key_NRC_13 + incorrect_key_length_NRC_13 + SID_27_NRC_13 + \
                         incorrect_sub_function_00_SID_27 + incorrect_sub_function_FF_SID_27 + \
                         request_for_seed_incorrect_service_id + request_for_key_incorrect_service_id + \
                         Exit_Programming_Session_by_Default_Session+ ("46298",)
    # </editor-fold>

    test_case_list = [Test_Case_ID_46295, Test_Case_ID_46296, Test_Case_ID_46297, Test_Case_ID_46298]

    @pytest.mark.parametrize("test_set", test_case_list)
    @L2
    def test_security_access_service(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_61504 = SID_10_81 + SID_10_02 + security_access_27_01 + \
                         Exit_Programming_Session_by_Default_Session + ("61504",)

    test_case_list = [Test_Case_ID_61504]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_security_access_service_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)
        
    Test_Case_ID_67232 = SID_27_01_No_response + calculated_key_No_response + ("67232",)

    test_case_list = [Test_Case_ID_67232]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_security_access_service_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("319: Diagnostic: Request Download - 0x34")
@pytest.mark.usefixtures("switch_to_app")
class TestRequestDownload(object):
    """The Request Download service is used by the diagnostic tool
    to initiate a data transfer from the diagnostic tool to the ECU (download"""

    # <editor-fold desc="Test Case List">
    Test_Case_ID_47647 = Enter_into_Programming_Session_without_Security_Access + REQUEST_DOWNLOAD_NRC_33 + \
                         Programming_session_with_security_access + REQUEST_DOWNLOAD + \
                         Exit_Programming_Session_by_Default_Session + ("47647",)

    Test_Case_ID_47660 = Programming_session_with_security_access + F34_Incorrect_DLC + F34_Incorrect_SID + \
                         REQUEST_DOWNLOAD_WITH_WRONG_DATA + Enter_into_Programming_Session_without_Security_Access + \
                         REQUEST_DOWNLOAD_NRC_33 + Exit_Programming_Session_by_Default_Session + ("47660",)

    # </editor-fold>

    test_case_list = [Test_Case_ID_47647, Test_Case_ID_47660]

    @pytest.mark.parametrize("test_set", test_case_list)
    @L2
    def test_request_download(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_67249 = Programming_session_with_security_access + check_programming_session + \
                         with_timing(REQUEST_DOWNLOAD, 1000) + Exit_Programming_Session_by_Default_Session + ("67249",)

    test_case_list = [Test_Case_ID_67249]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_download_request_with_time(self, test_set):
        validate_timing_parameter(test_set)

    Test_Case_ID_61502 = SID_10_81 + SID_10_02 + Tester_present + SID_27_01 + calculated_key + \
                         REQUEST_DOWNLOAD + Exit_Programming_Session_by_Default_Session + ("61502",)

    test_case_list = [Test_Case_ID_61502]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_request_download_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67225 = REQUEST_DOWNLOAD_NO_RESPONSE + ("67225",)
    test_case_list = [Test_Case_ID_67225]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_request_download_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("331: Diagnostic: Miscellaneous")
@pytest.mark.usefixtures("switch_to_app")
class TesterAutosarDCM(object):

    Test_Case_ID_59469 = check_default_session + RID_0212_NRC_31 + ("59469",)

    test_case_list = [Test_Case_ID_59469]

    @pytest.mark.parametrize("test_set", test_case_list)
    @L3
    def test_dcm_cofig(self,test_set):
        validate_diagnostics_requests(test_set)


@allure.parent_suite("Diagnostics")
@allure.suite("372: Diagnostic: Tester Present Service - 0x3E")
@pytest.mark.usefixtures("switch_to_app")
class TesterPresent_APP(object):
    """This suite has test cases related to basic check for Tester present service 0x3E"""

    # <editor-fold desc="Test Case List">
    Test_Case_ID_61359 = SID_10_01 + Tester_present_00 + \
                         Tester_present + Enter_Extended_Session + Tester_present_00 + Tester_present + \
                         ("61359: Check the Tester Present response in Application partition",)

    Test_Case_ID_61360 = SID_10_01 + incorrect_DLC_0x3E_NRC_13 + Tester_present_incorrect_sub_function_NRC_12 + \
                         Tester_present_incorrect_service_ID + ("61360: Negative response check for tester present",)
    # </editor-fold>

    test_case_list = [Test_Case_ID_61359, Test_Case_ID_61360]

    @pytest.mark.parametrize("test_set", test_case_list)
    @L2
    def test_tester_present(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_67201 = Tester_present_00_No_Response + Tester_present + ("67201",)

    test_case_list = [Test_Case_ID_67201]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_tester_present_with_invalid_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("372: Diagnostic: Tester Present Service - 0x3E")
@pytest.mark.usefixtures("switch_to_app")
class TesterPresent_BTLD(object):
    """This suite has test cases related to basic check for Tester present service 0x3E"""

    @pytest.fixture(scope="class", autouse=True)
    def tester_present_stop(self,request):
        stop_tester_present()

        def tester_present_start():
            start_tester_present()
        request.addfinalizer(tester_present_start)

    # <editor-fold desc="Test Case List">
    Test_Case_ID_61361 = SID_10_01 + Tester_present_00 + Tester_present + Enter_Extended_Session + Tester_present_00 + \
                         Tester_present + Enter_into_Programming_Session_without_Security_Access + \
                         Tester_present_00 + Tester_present + \
                         ("61361: Check the Tester Present response in Bootloader Partition",)

    Test_Case_ID_61364 = SID_10_01 + SID_10_02 + with_delay(check_programming_session, 3) + \
                         Tester_present + with_delay(check_programming_session, 3) + \
                         Tester_present_00 + with_delay(check_programming_session,6) + \
                         check_default_session + SID_10_01 + SID_10_03 + with_delay(check_extended_session, 3) + \
                         Tester_present + with_delay(check_extended_session, 3) + \
                         Tester_present_00 + with_delay(check_extended_session,6) + \
                         check_default_session + SID_10_01 + \
                         with_delay(check_default_session, 3) + \
                         Tester_present + with_delay(check_default_session, 3) + \
                         Tester_present_00 + check_default_session + \
                         ("61364: Check the implementation of additional server timer (S3_Server) for non-default session",)

    Test_Case_ID_61386 = SID_10_81 + SID_10_02 + with_delay(check_programming_session, 6) + \
                         check_default_session + SID_10_81 + SID_10_03 + \
                         with_delay(check_extended_session, 6) + \
                         check_default_session + \
                         SID_10_01 + \
                         with_delay(check_default_session, 6) + \
                         check_default_session + \
                         ("61386: Check the implementation of S3_Server timer on expiration for non-default session",)
    # </editor-fold>

    test_case_list = [pytest.param(Test_Case_ID_61361, marks=L2),
                      pytest.param(Test_Case_ID_61364, marks=L3),
                      pytest.param(Test_Case_ID_61386, marks=L3)]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_tester_present(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_61505 = Enter_Extended_Session + with_delay(Tester_present_00, 3) + \
                         with_delay(check_extended_session, 3) + \
                         with_delay(Tester_present, 3) + check_extended_session + \
                         ("61505: Check the Tester Present Response with Functional Address",)

    test_case_list = [Test_Case_ID_61505]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_tester_present_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("373: Diagnostic: Stability Test")
@stability
@pytest.mark.usefixtures("switch_to_app")
class TestStabilityApp(object):
    """This suite will have test cases related to stability test for Diagnostic Module"""

    # <editor-fold desc="Test Case List">
    Test_Case_ID_61427 = SID_10_01 + SID_10_02 + SID_10_01 + SID_10_03 + SID_10_81 + check_default_session + SID_10_83 +\
                         check_extended_session + SID_10_02 + check_programming_session + SID_10_81 + check_default_session + \
                         SID_10_82 + check_programming_session + Exit_Programming_Session_by_Default_Session + ("61427",)

    Test_Case_ID_61428 = SID_10_01 + check_default_session + read_part_number_20 + read_part_number_21_negative + read_part_number_25_negative + \
                         read_ECU_core_assembly_part + read_sw_part_number +\
                         ("61428: Read different types of Part numbers in default session",)

    Test_Case_ID_61435 = Enter_Extended_Session + read_part_number_20 + read_part_number_21_negative + read_part_number_25_negative + \
                         read_ECU_core_assembly_part + read_sw_part_number + Enter_into_Active_Bootloader_Partition + \
                         Enter_Extended_Session + read_part_number_20 + read_part_number_21_negative + read_part_number_25_negative + \
                         read_ECU_core_assembly_part + read_sw_part_number + \
                         ("61435: Read different types of Part numbers in extended diagnostic session",)

    Test_Case_ID_61443 = SID_10_81 + SID_10_03 + with_delay(check_extended_session, 2) + with_delay(Tester_present,2) + \
                         with_delay(check_extended_session, 6) + \
                         check_default_session + SID_10_01 + \
                         with_delay(check_default_session, 2) + Tester_present + \
                         with_delay(check_default_session, 6) + \
                         check_default_session + \
                         ("61443: Check the implementation of S3_Server timer",)

    Test_Case_ID_61662 = check_default_session + with_timing(ECU_RESET_01,50) + check_default_session + SID_10_03 + \
                         with_timing(ECU_RESET_01,50) + check_default_session +\
                         ("61662",)

    Test_Case_ID_61533 = ECU_RESET_01 + SID_10_01 + \
                         ("61533",)
    # </editor-fold>

    test_case_list = [Test_Case_ID_61427, Test_Case_ID_61428, Test_Case_ID_61435, Test_Case_ID_61443]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_stability(self, test_set):
        validate_diagnostics_requests(test_set)

    test_case_list = [Test_Case_ID_61662]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_stability_timing(self, test_set):
        validate_timing_parameter(test_set)

    def test_power_cycle_stability(self):
        """The intend is check the behavior of UDS stack with power cycle"""
        # To-Do reboot should be change to power supply, for now setup does't have PPS
        # allure_test_link("61533: Check the behavior of UDS stack with power cycle")
        # async_reboot_over_ssh()
        async_reset_tcu(1)
        setup_module(TestStabilityApp)
        test_set = SID_10_01 + ("61533: Check the behavior of UDS stack with power cycle",)
        validate_diagnostics_requests(test_set)

    def teardown_method(self, test_method):
        """Switch back to APP"""
        switch_to_active_partition(Software_Partition.APPLICATION)


@allure.parent_suite("Diagnostics")
@allure.suite("373: Diagnostic: Stability Test")
@stability
@pytest.mark.usefixtures("switch_to_app")
class TestStabilityBoot(object):
    """This suite will have test cases related to stability test for Diagnostic Module"""

    # <editor-fold desc="Test Case">
    Test_Case_ID_61442 = SID_10_01 + SID_10_02 + SID_10_01 + SID_10_03 + SID_10_81 + check_default_session + SID_10_83 + \
                         check_extended_session + SID_10_82 + check_programming_session + SID_10_81 + check_default_session +\
                         SID_10_82 + check_programming_session + Exit_Programming_Session_by_Default_Session + \
                         ("61442: Enter into different diagnostic sessions continuously using functional address 0x1FFF for 500 cycles",)

    Test_Case_ID_61436 = Enter_into_Programming_Session_without_Security_Access + read_part_number_20_NRC_31 + read_part_number_21 + \
                         read_part_number_25 + read_sw_part_number_NRC_31 + Exit_Programming_Session_by_Default_Session + \
                         ("61436: Read different types of Part numbers in programming session",)

    Test_Case_ID_61429 = SID_10_81 + SID_10_02 + with_delay(check_programming_session, 2) + Tester_present + \
                         with_delay(check_programming_session, 6) + \
                         check_default_session + SID_10_81 + SID_10_03 + \
                         check_extended_session + SID_10_02 + with_delay(check_programming_session, 2) + Tester_present + \
                         with_delay(check_programming_session, 6) + check_default_session + \
                         ("61429: Check the implementation of S3_Server",)

    Test_Case_ID_61483 = SID_10_01 + RID_0206_True + SID_10_02 + check_programming_session + SID_10_81 + SID_10_03 + \
                         RID_0206_True + SID_10_02 + check_programming_session + RID_0206_NRC_31 + \
                         check_programming_session + Exit_Programming_Session_by_Default_Session + \
                         ("61483: Enter into Programming Session by Pre-Condition Check",)

    Test_Case_ID_61663 = check_default_session + SID_10_02 + check_programming_session + with_timing(ECU_RESET_01,40) + \
                         with_timing(check_programming_session,40) + Exit_Programming_Session_by_Default_Session + ("61663",)

    # </editor-fold>

    test_case_list = [Test_Case_ID_61436, Test_Case_ID_61429,Test_Case_ID_61483]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_stability(self, test_set):
        validate_diagnostics_requests(test_set)

    test_case_list = [Test_Case_ID_61663]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_stability_timing(self, test_set):
        validate_timing_parameter(test_set)

    test_case_list = [Test_Case_ID_61442]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_ecu_reset_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    def test_programing_session_switch(self):
        """The intention is to check the behavior of TCAM2 in bootloader while requesting to enter into programming session"""
        test_set = check_default_session + SID_10_82 + check_programming_session + SID_10_02 + check_programming_session + \
                   Exit_Programming_Session_by_Default_Session + ("61952",)
        validate_diagnostics_requests(test_set)


@allure.parent_suite("Diagnostics")
@allure.suite("357: Diagnostic: ECU Reset Service - 0x11")
@L2
@pytest.mark.usefixtures("switch_to_app")
class Test_ECU_Reset(object):
    """The ECU Reset service is used by the client to request a server reset.
    This service requests the server to effectively perform a server reset based on the
    content of the reset Type parameter value embedded in the ECU Reset request message."""

    # <editor-fold desc="Test Case List">
    Test_Case_ID_60707 = SID_10_01 + ECU_RESET_01 + ECU_RESET_81 + \
                         SID_10_81 + SID_10_03 + ECU_RESET_01 + ECU_RESET_81 + \
                         (
                             "60707: Check the response of diagnostic request for ECU Reset in different diagnostic session of Application partition",)

    Test_Case_ID_59947 = SID_10_01+ SID_10_02 + ECU_RESET_01 + SID_10_81 + SID_10_82 + check_programming_session +\
                         ECU_RESET_81 + Exit_Programming_Session_by_Default_Session + ("59947",)

    Test_Case_ID_59948 = incorrect_data_length_01 + incorrect_data_length_81 + incorrect_sub_function_SID_11 + \
                         incorrect_service_identifier_51_01 + incorrect_service_identifier_12_81 + \
                         ("59948: Check negative responses for session control 0x11",)
    # </editor-fold">

    test_case_list = [Test_Case_ID_60707, Test_Case_ID_59947, Test_Case_ID_59948]

    @pytest.mark.parametrize("test_set", test_case_list)
    def test_ecu_reset(self, test_set):
        validate_diagnostics_requests(test_set)

    # <editor-fold desc="Test Case 61506:ECU reset with functional address">
    Test_Case_ID_61506 = SID_10_01 + ECU_RESET_01 + ECU_RESET_81 + \
                         ("61506: Check the response of ECU reset request with functional address",)
    # </editor-fold">

    test_case_list = [Test_Case_ID_61506]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_ecu_reset_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    # <editor-fold desc="Test Case 66431:Maximum response time for ECU Reset">
    Test_Case_ID_66431 = SID_10_01 + with_timing(ECU_RESET_01,50) + SID_10_03 + with_timing(ECU_RESET_01,50) + SID_10_02 + \
                         with_timing(ECU_RESET_01,40) + Exit_Programming_Session_by_Default_Session + \
                         ("66431",)
    # </editor-fold">

    test_case_list = [Test_Case_ID_66431]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_ecu_rest_timing(self, test_set):
        validate_timing_parameter(test_set)

    Test_Case_ID_67198 = ECU_RESET_01_No_Response + ECU_RESET_81 + ("67198",)

    test_case_list = [Test_Case_ID_67198]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_ecu_reset_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("375: Diagnostic: Read DTC Information Service - 0x19")
class Test_Read_DTC(object):
    """This service allows a client to read the status of server resident Diagnostic Trouble Code (DTC) information
        from any server, or group of servers within a vehicle"""

    @pytest.fixture(scope="function", autouse=True)
    def switch_to_app(request):
        """Verify that we are starting from application partition only"""
        setup_module(Test_Read_DTC)
        switch_to_active_partition(Software_Partition.APPLICATION)

    Test_Case_ID_61511 = with_delay(SID_10_01,5) + with_delay(clear_diagnostic_information,5) + Read_DTC_02 + Read_DTC_82 + with_delay(Enter_Extended_Session,5) + Read_DTC_02 + Read_DTC_82 + \
                         Enter_into_Programming_Session_without_Security_Access + Read_DTC_in_programming_mode + \
                         Exit_Programming_Session_by_Default_Session + ("61511",)

    Test_Case_ID_61512 = SID_10_01 + incorrect_sub_function_SID_1902 + incorrect_DLC_SID_1902 + \
                         incorrect_service_id_SID_1902 + ("61512: Check the negative response for 19_02",)

    Test_Case_ID_65734 = SID_10_01 + Read_DTC_03_NRC_13 + incorrect_sub_function_SID_1903 + \
                         incorrect_service_ID_SID_1903 + ("65734",)

    Test_Case_ID_65736 = SID_10_01 + Read_DTC_04_NRC_13 + incorrect_sub_function_SID_1904 + \
                         incorrect_service_ID_SID_1904 + Read_DTC_04_NRC_31 + ("65736",)

    Test_Case_ID_65738 = SID_10_01 + Read_DTC_06_NRC_13 + incorrect_sub_function_SID_1906 + \
                         incorrect_service_ID_SID_1906 + Read_DTC_06_NRC_13 + ("65738",)

    Test_Case_ID_65737 = SID_10_01 + Read_DTC_information_possitive + \
                         Enter_into_extended_diagnostic_session_with_tester_present + \
                         Read_DTC_information_possitive + Enter_into_programing_session_without_security_access + \
                         Read_DTC_information_negative + \
                         SID_10_01 + ("65737",)

    Test_Case_ID_65735 = SID_10_01 + Read_DTC_information_possitive_04 + \
                         Enter_into_extended_diagnostic_session_with_tester_present + \
                         Read_DTC_information_possitive_04 + Enter_into_programing_session_without_security_access + \
                         Read_DTC_information_negative + SID_10_01 + ("65735",)

    Test_Case_ID_65733 = SID_10_01 + Read_DTC_Snapshot_Identification_Possitive + \
                         Enter_into_extended_diagnostic_session_with_tester_present + \
                         Read_DTC_Snapshot_Identification_Possitive + \
                         Enter_into_programing_session_without_security_access + \
                         Read_DTC_Snapshot_Identification_Negative + SID_10_01 + ("65733",)

    # test_case_list = [Test_Case_ID_61511, Test_Case_ID_61512, Test_Case_ID_65734,
    #                   Test_Case_ID_65736, Test_Case_ID_65738, Test_Case_ID_65737,
    #                   Test_Case_ID_65735, Test_Case_ID_65733]
    test_case_list = [pytest.param(Test_Case_ID_61511, marks=L2),
                      pytest.param(Test_Case_ID_61512, marks=L2),
                      pytest.param(Test_Case_ID_65734, marks=L2),
                      pytest.param(Test_Case_ID_65736, marks=L2),
                      pytest.param(Test_Case_ID_65738, marks=L2),
                      pytest.param(Test_Case_ID_65737, marks=under_development),
                      pytest.param(Test_Case_ID_65735, marks=under_development),
                      pytest.param(Test_Case_ID_65733, marks=under_development),]

    #@L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_readDTC(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_61513 = with_delay(SID_10_81,5) + Read_DTC_02 + Read_DTC_82 + (
        "61513: Check the response of Read DTC request with Functional Address",)

    test_case_list = [Test_Case_ID_61513]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_readDTC_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67210 = Read_DTC_02_No_Response + ("67210",)

    test_case_list = [Test_Case_ID_67210]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_readDTC_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)

    @L3
    def test_check_dtc_file(self):
        allure_test_link("65141")
        dtc_file = "/mnt/data/DTCStorage.bin"
        cmd = "ls -l " + dtc_file + "|wc -l|tr -d '\n'"
        logger.debug("cmd {}".format(cmd))
        output = execute_command_and_return_console_output(cmd)
        assert output == '1',"File is present in the path /mnt/data/DTCStorage.bin"

    @L3
    def test_read_dtc_service(self):
        """The intend is to check the communication between DTC Plugin and DTC
        monitor service for  service 0x19"""
        allure_test_link("65141")
        async_reset_tcu(1)
        test_set = SID_10_01 + Read_DTC_02
        validate_diagnostics_requests(test_set)
        assert status_service_systemctl_in_loop("dtc-monitor.service", timeout=1), \
            "dtc-monitor.service not running"
        test_set = Enter_Extended_Session + Read_DTC_02
        validate_diagnostics_requests(test_set)
        assert status_service_systemctl_in_loop("dtc-monitor.service", timeout=1), \
            "dtc-monitor.service not running"


@allure.parent_suite("Diagnostics")
@allure.suite("375: Diagnostic: Read DTC Information Service - 0x19")
class TestReadDTC(object):
    """This service allows a client to read the status of server resident Diagnostic Trouble Code (DTC) information
            from any server, or group of servers within a vehicle"""

    @pytest.fixture(scope="function", autouse=True)
    def switch_to_btl(self,request):
        """Verify that we are starting from application partition only"""
        switch_to_active_partition(Software_Partition.BOOTLOADER)


    @L3
    def test_check_dtc_file_bootloader_partition(self):
        allure_test_link("66801")
        dtc_file = "/mnt/data/DTCStorage.bin"
        cmd = "ls -l " + dtc_file + "|wc -l|tr -d '\n'"
        logger.debug("cmd {}".format(cmd))
        check_dtc_file_output = execute_command_and_return_console_output(cmd)
        assert check_dtc_file_output == '1', "File is present in the path {}".format(dtc_file)

    Test_Case_ID_66796 = ("66796", "dtc-monitor.service")
    Test_Case_ID_66799 = ("66799", "ErrorManager.service")

    test_case_list = [Test_Case_ID_66796, Test_Case_ID_66799]

    @L1
    @pytest.mark.parametrize("alm_id, monitor_service_set", test_case_list)
    def test_check_service_status(self, alm_id, monitor_service_set):
        allure_test_link(alm_id)
        service_status = status_service_systemctl_return_value(monitor_service_set)
        assert service_status == 4, "{} service is running".format(monitor_service_set)


@allure.parent_suite("Diagnostics")
@allure.suite("230: Diagnostic: Routine Control - Service Identifier 0x31")
class TestRID(object):
    """The Routine Control service is used by the diagnostic tool to start a routine,
    stop a routine and request routine results referenced by a 2-byte routine identifier within ECU."""

    @pytest.fixture(scope="function", autouse=True)
    def switch_to_app(request):
        """Verify that we are starting from application partition only"""
        setup_module(TestRID)
        switch_to_active_partition(Software_Partition.APPLICATION)

    # <editor-fold desc="Test Case List">
    Test_Case_ID_47038 = SID_10_01 + RID_0206_True + Enter_Extended_Session + RID_0206_True + \
                         Enter_into_Programming_Session_without_Security_Access + RID_0206_NRC_31 + \
                         Exit_Programming_Session_by_Default_Session+ ("47038",)

    Test_Case_ID_47142 = SID_10_01 + RID_0206_NRC_13 + incorrect_sub_function_RID_0206 + RID_0206_NRC_11 + \
                         incorrect_RID_NRC_31 + ("47142",)

    Test_Case_ID_47153 = SID_10_01 + RID_0212_NRC_31 + Enter_Extended_Session + RID_0212_NRC_31 + \
                         Programming_session_with_security_access + RID_0212 + Exit_Programming_Session_by_Default_Session+ \
                         ("47153",)

    Test_Case_ID_47154 = Enter_into_Programming_Session_without_Security_Access + RID_0212_NRC_33 + \
                         Programming_session_with_security_access + RID_0212_NRC_13 + incorrect_sub_function_RID_0212 \
                         + RID_0212_NRC_11 +Exit_Programming_Session_by_Default_Session+  ("47154",)

    Test_Case_ID_46290 = SID_10_01 + RID_0205_NRC_31 + \
                         ("46290",)

    Test_Case_ID_46291 = Enter_Extended_Session + RID_0205_NRC_31 + \
                         ("46291: Check Complete & Compatible in Extended Diagnotic Session",)

    Test_Case_ID_46294 = Programming_session_with_security_access + RID_0205_NRC_13 + \
                         incorrect_sub_function_RID_0205 + RID_0205_NRC_11 \
                         + incorrect_RID_NRC_31 +Exit_Programming_Session_by_Default_Session+\
                         ("46294",)

    Test_Case_ID_46292 = Enter_into_Programming_Session_without_Security_Access + RID_0205_NRC_33 + \
                         Programming_session_with_security_access + RID_0205 \
                         + Exit_Programming_Session_by_Default_Session + ("46292",)

    test_case_list = [Test_Case_ID_47038, Test_Case_ID_47142, Test_Case_ID_47153, Test_Case_ID_47154,
                      Test_Case_ID_46290,
                      Test_Case_ID_46291, Test_Case_ID_46294, Test_Case_ID_46292]

    # </editor-fold>

    @L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_rid(self, test_set):
        validate_diagnostics_requests(test_set)

    # <editor-fold desc="Test Case List">
    Test_Case_ID_61500 = SID_10_01 + RID_0206_True + RID_0206_Status + Enter_Extended_Session + RID_0206_True + \
                         RID_0206_Status + ("61500: Check Programming Pre-Condition Routine with Functional Address",)

    Test_Case_ID_61501 = SID_10_81 + SID_10_02 + SID_27_01 + calculated_key + RID_0212 + \
                         RID_0212_Status + SID_10_81 + Exit_Programming_Session_by_Default_Session + \
                         ("61501: Check Response of Check Memory Routine with Functional Address",)

    Test_Case_ID_61499 = SID_10_81 + SID_10_02 + SID_27_01 + calculated_key + RID_0205 + \
                         RID_0205_Status + Exit_Programming_Session_by_Default_Session + \
                         Exit_Programming_Session + ("61499: Check C&C Routine with Functional Address",)

    test_case_list = [Test_Case_ID_61500, Test_Case_ID_61501, Test_Case_ID_61499]

    # </editor-fold>

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_rid_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set, AddressEnum.FUNCTIONAL_ADDRESS)

    # <editor-fold desc="Test Case List">
    Test_Case_ID_47158 = Programming_session_with_security_access + with_timing(RID_0205,40) + with_timing(RID_0212,40) + \
                         Exit_Programming_Session_by_Default_Session + SID_10_01 + with_timing(RID_0206_True,50) + \
                         SID_10_03 + with_timing(RID_0206_True,50) + ("47158",)

    test_case_list = [Test_Case_ID_47158]
    # </editor-fold>

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_rid_with_timing(self, test_set):
        validate_timing_parameter(test_set)

    Test_Case_ID_67211 = RID_0206_No_Response + RID_0205_No_Response + RID_0212_No_Response + ("67211",)
    test_case_list = [Test_Case_ID_67211]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_routine_control_request_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("394: KPI Measurement")
@KPI
@pytest.mark.usefixtures("switch_to_app")
class TestKPI(object):
    """This suite will have test case to measure kpi related to TCAM2"""

    def test_switch_to_programing(self):
        """The intention is to record the time to get into programming session"""
        # allure_test_link("62281")

        test_set = with_timing(SID_10_02, 40) + Exit_Programming_Session_by_Default_Session + ("62281",)
        t1_timing = time.time()  # start time
        validate_timing_parameter(test_set)
        t2_timing = time.time()  # timer end
        logger.debug("SWITCH TO PROGRAMING KPI is --> {}".format(t2_timing - t1_timing))
        update_kpi_in_allure("Time taken to enter PROGRAMING mode --> {} sec".format(t2_timing - t1_timing))
        # setup_module(Test_DID)
        # current_partition = get_current_partition()
        # logger.debug("Current partition after running the DID --> {}".format(current_partition))
        # assertion(current_partition[0],'==',Software_Partition.BOOTLOADER,"Partition is not switch to bootloader")

    @KPI
    def test_uds_service_warm_restart(self):
        """The intend is to check the time taken by uds diagnostic service to be in active state after warm start"""
        test_set = ECU_RESET_81 + ("65845",)
        t1_timing = time.time()  # start time
        validate_diagnostics_requests(test_set)
        async_reset_tcu(1)
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        status = status_service_systemctl_in_loop('uds_diagnostic_server.service', timeout=20)
        assert status, "uds_diagnostic_server.service service is not running"
        t2_timing = time.time()  # timer end
        logger.debug("UDS up and running KPI is after warm restart--> {}".format(t2_timing - t1_timing))
        update_kpi_in_allure("Time taken by UDS service to up and running after warm restart--> {} sec".format(t2_timing - t1_timing))

    @KPI
    def test_uds_service_cold_restart(self):
        """The intend is to check the time taken by uds diagnostic service to be in active state after cold restart"""
        allure_test_link("65844")
        t1_timing = time.time()  # start time
        async_reset_tcu(1)
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        status = status_service_systemctl_in_loop('uds_diagnostic_server.service', timeout=20)
        assert status, "uds_diagnostic_server.service service is not running"
        t2_timing = time.time()  # timer end
        logger.debug("UDS up and running KPI is after cold restart--> {}".format(t2_timing - t1_timing))
        update_kpi_in_allure("Time taken by UDS service to up and running after cold restart--> {} sec".format(t2_timing - t1_timing))

    def test_ecu_reset(self):
        """The intend is to check the time taken by TCAM2 board to boot up from sleep"""
        test_set = ECU_RESET_01 + ("59520: Check the time taken by TCAM2 for reset",)
        t1_timing = time.time()  # start timer
        validate_diagnostics_requests(test_set)
        t2_timing = time.time()  # timer end
        logger.debug("RESET KPI is --> {}".format(t2_timing - t1_timing))
        update_kpi_in_allure("Time taken for ECU reset --> {} sec".format(t2_timing - t1_timing))


@allure.parent_suite("Diagnostics")
@allure.suite("394: KPI Measurement")
@KPI
@pytest.mark.usefixtures("switch_to_app")
class Test_KPI(object):
    """This suite will have test case to measure kpi related to TCAM2"""

    @pytest.fixture(scope="class", autouse=True)
    def tester_present_stop(self, request):
        stop_tester_present()

        def tester_present_start():
            start_tester_present()
        request.addfinalizer(tester_present_start)

    @KPI
    def test_first_uds_response_after_warm_restart(self):
        """The intend is to measure the time taken by TCAM2 to send first uds response
        after Warm Start i.e. ECU Reset"""
        # TODO need to enable the PPS code when we have PPS connected to setup
        # restart(ipConnection_Timeout=1,connection_status=False)
        # async_reboot_over_ssh() # added for temporary no PPS connected in setup
        test_set = ECU_RESET_01 + ("59541",)
        t1_timing = time.time()  # start time
        validate_diagnostics_requests(test_set)
        async_reset_tcu(1)
        t0_timing = time.time()  # this will include ETH up time+ first response
        logger.debug("Device rebooted at -> {}".format(time.ctime()))
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        logger.debug("Device SSH is up at -> {}".format(time.ctime()))
        did_response = send_command_and_get_response(Tester_present_00[0][0])
        t2_timing = time.time()
        logger.debug("Device DOIP response at -> {}".format(time.ctime()))
        assert did_response['rawResponse'] is not None, "No response from DOIP,status --> {}," \
                                                        "DID --> {}".format(did_response['response'],
                                                                            check_default_session[0][0])
        response_time = int(did_response['responseTime'].strip()[:-2])
        assertion(response_time, '<=', 25,
                  "Response time {} should be less {}".format(response_time, 25))
        logger.debug("KPI time taken for uds response after ETH is up and warm restart--> "
                     "{}".format(t2_timing - t1_timing))
        logger.debug("KPI time taken for uds response including ETH up time and after "
                     "warm Start--> {}".format(t2_timing - t0_timing))

    @KPI
    def test_uds_service_after_cold_restart(self):
        """the intend is to measure the time taken by TCAM2 to send first uds response after cold start"""
        allure_test_link("59524")
        # TODO need to enable the PPS code when we have PPS connected to setup
        # restart(ipConnection_Timeout=1,connection_status=False)
        # async_reboot_over_ssh() # added for temporary no PPS connected in setup
        async_reset_tcu(1)  # added for temporary no PPS connected in setup. Also, async_reboot_over_ssh() i.e reboot -f no longer a valid command
        t1_timing = time.time()  # start timer
        time.sleep(2)
        did_response = send_command_and_get_response(Tester_present_00[0][0])
        t2_timing = time.time()
        logger.debug("Device DOIP response at -> {}".format(time.ctime()))
        assert did_response['rawResponse'] is not None, "No response from DOIP , status --> {} , DID --> {}".format(
            did_response['response'], check_default_session[0][0])
        response_time = int(did_response['responseTime'].strip()[:-2])
        assertion(response_time, '<=', 25,"Response time {} should be less "
                                          "{}".format(response_time, 25))
        logger.debug("KPI time taken for uds response after cold restart--> "
                     "{}".format(t2_timing - t1_timing))


@allure.parent_suite("Diagnostics")
@allure.suite("511: Clear Diagnostic Information Service - 0x14")
@pytest.mark.usefixtures("switch_to_app")
class TestClearDiagnosticsInformation(object):
    """The Clear Diagnostic Information service is used by the client
     to clear diagnostic information in one or multiple server's memory."""

    # <editor-fold desc="Test Case with Target Address">
    Test_Case_ID_64564 = Enter_in_Default_Session + clear_diagnostic_information + Enter_Extended_Session + \
                         clear_diagnostic_information + Enter_into_Programming_Session_without_Security_Access + \
                         CDI_incorrect_session_NRC_11 + ("64564",)

    Test_Case_ID_64565 = Enter_in_Default_Session+ CDI_incorrect_short_message_length_NRC_13+\
                         CDI_incorrect_long_message_length_NRC_13+ CDI_incorrect_very_short_message_length_NRC_13+\
                         CDI_incorrect_DTC_group_number+("64565",)
    # </editor-fold>

    test_case_list = [Test_Case_ID_64564,Test_Case_ID_64565]

    @L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_clear_diagnostics_request(self, test_set):
        validate_diagnostics_requests(test_set)

    # <editor-fold desc="Test Case with functional address">
    Test_Case_ID_64567 = Enter_in_Default_Session+ clear_diagnostic_information+Enter_Extended_Session+\
                         clear_diagnostic_information+ ("64567",)

    # </editor-fold>

    test_case_list = [Test_Case_ID_64567]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_clear_diagnostics_request_functional_address(self, test_set):
        validate_diagnostics_requests(test_set,AddressEnum.FUNCTIONAL_ADDRESS)

    # <editor-fold desc="Test Case to check the response of clear DTC request with invalid physical address">
    Test_Case_ID_67208 = clear_diagnostic_information_no_response + ("67208",)
    # </editor-fold>

    test_case_list = [Test_Case_ID_67208]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_clear_diagnostics_request_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)

    # <editor-fold desc="Test Case Verify in dlt logs">
    Test_Case_ID_64568 = Enter_in_Default_Session+ clear_diagnostic_information+Enter_Extended_Session+\
                         clear_diagnostic_information+ ("64568",)

    # </editor-fold>

    test_case_list = [Test_Case_ID_64568]

    # @L3
    # @pytest.mark.parametrize("test_set", test_case_list)
    # def test_test_clear_diagnostics_request_verify_dlt(self, test_set):
    #     start_dlt = DltLib(TCU_IP)
    #     # capture the dlt logs with app_id DTCM
    #     logger.debug("start log capture --> {}".format(start_dlt.start_buffering(app_id="DTCM")))
    #     time.sleep(1)
    #     validate_diagnostics_requests(test_set)
    #     dlt_logs = start_dlt.stop_buffering()
    #     logger.debug("Captured dlt logs -- \n{}".format(dlt_logs))
    #     # assert len(dlt_logs) > 0, "No dlt logs with app_id DTCM"
    #     # TODO Need to check the count of each type of message
    #     assert "DTCMonitorStubImpl::clearDTCInformation" in dlt_logs,\
    #         "DTCMonitorStubImpl::clearDTCInformation logs not present in dlt logs"
    #     assert "DTCInformation::ClearDTCInformation" in dlt_logs, \
    #         "DTCInformation::ClearDTCInformation logs not present in dlt logs"


@allure.parent_suite("Diagnostics")
@allure.suite("573: Diagnostic: Write Data By Identifier Service - 0x2E")
@pytest.mark.usefixtures("switch_to_app")
class TestWriteDataByIdentifier(object):

    # <editor-fold desc="Test Case for 0x2E with DID 0xD01C">
    Test_Case_ID_64693 = Enter_into_Programming_Session_without_Security_Access + incorrect_length_write_DID_D01C_NRC13 + \
                         incorrect_length_long_AB_NRC13 + incorrect_write_DIDF186_NRC31 + incorrect_write_DID_D01C_NRC31 + \
                         write_DID_D01C_NRC33 + SID_27_01 + write_DID_D01C_NRC33 + calculated_key + incorrect_DLC_D01C_NRC13 + \
                         incorrect_length_long_AB_NRC13 + Exit_Programming_Session_by_Default_Session + ("64693",)

    Test_Case_ID_64694 = Enter_in_Default_Session + incorrect_session_D01C_NRC31 + Programming_session_with_security_access + \
                         write_DID_D01C_positive_response + Enter_Extended_Session + incorrect_session_D01C_NRC31 + \
                         ("64694",)

    Test_Case_ID_64696 = Enter_into_Programming_Session_without_Security_Access + incorrect_length_write_DID_D01C_NRC13 + \
                         incorrect_length_long_AB_NRC13 + incorrect_write_DIDF186_NRC31 + incorrect_write_DID_D01C_NRC31 + \
                         write_DID_D01C_NRC33 + SID_27_01 + write_DID_D01C_NRC33 + calculated_key + \
                         incorrect_DLC_D01C_NRC13_functional + incorrect_length_long_AB_NRC13 + \
                         Exit_Programming_Session_by_Default_Session + ("64696",)

    # </editor-fold>

    test_case_list = [pytest.param(Test_Case_ID_64693, marks=L2), Test_Case_ID_64694]

    @L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_write_data_by_identifier(self, test_set):
        validate_diagnostics_requests(test_set)

    test_case_list = [Test_Case_ID_64696]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_write_data_by_identifier_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set,AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67231 = Data_no_response + ("67231",)

    test_case_list = [Test_Case_ID_67231]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_write_data_by_DID_request_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("662: Transfer Data (0x36) & Transfer Exit (0x37)")
@pytest.mark.usefixtures("switch_to_app")
class TestTransferDataExit(object):
    '''The Transfer Data service is used by the client to transfer data either from the client to the server (download)
    or from the server to the client (upload).
    The Transfer Exit service is used by the client to terminate a data transfer between client and server (upload or download).'''

    # <editor-fold desc="Test Case for Transfer Data (0x36) & Transfer Exit (0x37)">
    Test_Case_ID_66842 = Enter_into_Programming_Diagnostic_Session_and_verify + incorrect_request_transfer_data_NRC24 + \
                         incorrect_request_transfer_data_NRC13 + security_access_27_01 + REQUEST_DOWNLOAD + \
                         incorrect_DLC_transfer_data_NRC13 + REQUEST_DOWNLOAD + incorrect_request_transfer_data_1_NRC71 + \
                         REQUEST_DOWNLOAD + incorrect_request_transfer_data_2_NRC71 + REQUEST_DOWNLOAD + \
                         incorrect_transfer_data_request_NRC71 + REQUEST_DOWNLOAD + incorrect_transfer_data_request_NRC24 + \
                         REQUEST_DOWNLOAD + incorrect_request_transfer_data_NRC73 + REQUEST_DOWNLOAD + \
                         incorrect_transfer_data_request_NRC73 + Exit_Programming_Session_by_Default_Session + \
                         ("66842",)

    Test_Case_ID_66843 = Enter_into_Programming_Diagnostic_Session_and_verify + incorrect_transfer_exit_request_NRC13 + \
                         incorrect_transfer_exit_request_NRC24 + Exit_Programming_Session_by_Default_Session + \
                         ("66843",)

    Test_Case_ID_66844 = Enter_and_verify_default_session + incorrect_request_transfer_data_NRC11 + \
                         Enter_into_Extended_Diagnostic_Session_and_verify + incorrect_request_transfer_data_NRC11 + \
                         Programming_session_with_security_access + check_programming_session + REQUEST_DOWNLOAD + \
                         request_transfer_data_01 + Exit_Programming_Session_by_Default_Session + ("66844",)

    Test_Case_ID_66845 = Enter_and_verify_default_session + incorrect_transfer_exit_request_NRC11 + \
                         Enter_into_Extended_Diagnostic_Session_and_verify + incorrect_transfer_exit_request_NRC11 + \
                         Programming_session_with_security_access + check_programming_session + REQUEST_DOWNLOAD + \
                         request_transfer_data_01 + request_transfer_exit + \
                         Exit_Programming_Session_by_Default_Session + ("66845",)

    Test_Case_ID_66846 = Enter_and_verify_default_session + incorrect_request_transfer_data_NRC11 + \
                         Enter_into_Extended_Diagnostic_Session_and_verify + incorrect_request_transfer_data_NRC11 + \
                         Programming_session_with_security_access + check_programming_session + REQUEST_DOWNLOAD + \
                         request_transfer_data_00 + request_transfer_data_01 + \
                         Exit_Programming_Session_by_Default_Session + ("66846",)

    Test_Case_ID_66847 = Enter_and_verify_default_session + incorrect_transfer_exit_request_NRC11 + \
                         Enter_into_Extended_Diagnostic_Session_and_verify + incorrect_transfer_exit_request_NRC11 + \
                         Programming_session_with_security_access + check_programming_session + REQUEST_DOWNLOAD + \
                         request_transfer_data_01 + request_transfer_exit + \
                         Exit_Programming_Session_by_Default_Session + ("66847",)

    # </editor-fold>

    test_case_list = [Test_Case_ID_66842, Test_Case_ID_66843, Test_Case_ID_66844,Test_Case_ID_66845]
    @L2
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_transfer_data_exit(self, test_set):
        validate_diagnostics_requests(test_set)

    Test_Case_ID_67248 = Programming_session_with_security_access + check_programming_session + \
                         REQUEST_DOWNLOAD + request_transfer_data_01 + \
                         with_timing(request_transfer_exit, 15000) + \
                         Exit_Programming_Session_by_Default_Session + ("67248",)

    Test_Case_ID_67247 = Programming_session_with_security_access + check_programming_session + \
                         REQUEST_DOWNLOAD + with_timing(request_transfer_data_01, 5000) + \
                         Exit_Programming_Session_by_Default_Session + ("67247",)

    test_case_list = [Test_Case_ID_67247, Test_Case_ID_67248]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_transfer_data_time_parameter(self, test_set):
        validate_timing_parameter(test_set)

    test_case_list = [Test_Case_ID_66846,Test_Case_ID_66847]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_transfer_data_exit_with_functional_address(self, test_set):
        validate_diagnostics_requests(test_set,AddressEnum.FUNCTIONAL_ADDRESS)

    Test_Case_ID_67229 = request_transfer_no_response + ("67229",)
    Test_Case_ID_67227 = Transfer_data_no_response + ("67227",)

    test_case_list = [Test_Case_ID_67229, Test_Case_ID_67227]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_transfer_data_with_invalid_address(self, test_set):
        # TODO verification of TCAM2 set up should not reboot
        validate_diagnostics_requests(test_set, AddressEnum.INVALID_TARGET_ADDRESS)


@allure.parent_suite("Diagnostics")
@allure.suite("662: Transfer Data (0x36) & Transfer Exit (0x37)")
@pytest.mark.usefixtures("switch_to_app")
class Test_Transfer_Data_Exit(object):
    '''The Transfer Data service is used by the client to transfer data either from the client to the server (download)
    or from the server to the client (upload).
    The Transfer Exit service is used by the client to terminate a data transfer between client and server (upload or download).'''

    @pytest.fixture(scope="class", autouse=True)
    def tester_present_stop(self, request):
        stop_tester_present()

        def tester_present_start():
            start_tester_present()

        request.addfinalizer(tester_present_start)

    Test_Case_ID_67244 = Enter_in_Default_Session + with_timing(Tester_present_00, 50) + \
                         Enter_Extended_Session + with_timing(Tester_present_00, 50) + \
                         Enter_into_Programming_Session_without_Security_Access + \
                         with_timing(Tester_present_00, 40) + Exit_Programming_Session_by_Default_Session + ("67244",)

    test_case_list = [Test_Case_ID_67244]

    @L3
    @pytest.mark.parametrize("test_set", test_case_list)
    def test_data_transfer_with_time(self, test_set):
        validate_timing_parameter(test_set)


# @allure.parent_suite("Diagnostics")
# @allure.suite("Diagnostic Test Example")  #Used for by Himadri
# class Test_Example(object):
#     """This suite is used for testing few examples"""

    # #Switch to BTLD
    # @pytest.fixture(scope="function", autouse=True)
    # def switch_to_btlt(request):
    #     """Verify that we are starting from btld partition only"""
    #     switch_to_active_partition(Software_Partition.BOOTLOADER)

    #Switch to APP
    # @pytest.fixture(scope="function", autouse=True)
    # def switch_to_app(request):
    #     """Verify that we are starting from application partition only"""
    #     setup_module(Test_Read_DTC)
    #     switch_to_active_partition(Software_Partition.APPLICATION)

    #Test_Case_Ex_1 = SID_10_01 + SID_10_03 +SID_10_02 + ("Test Case to check new P2 Server Time Change",)
    # Test_Case_Ex_2 = check_default_session + with_delay(SID_10_82,6) + check_default_session + SID_10_02 + check_programming_session + \
    #                  SID_10_01 + check_default_session + ("Test Case to check connection after 5 sec",)
    # Test_Case_Ex_3 = check_default_session + with_delay(SID_10_82,1) + check_programming_session + \
    #                  SID_10_01 + check_default_session + ("Test Case to check connection immediately",)
    #
    # Test_Case_Ex_4 = check_default_session + with_delay(SID_10_82,1) + with_delay(check_programming_session,5) + \
    #                  check_default_session + ("Test Case to check connection immediately",)
    #
    # Test_Case_Ex_5 = check_default_session + with_delay(SID_10_82,1) + check_programming_session + check_programming_session + check_programming_session + \
    #                  with_delay(check_programming_session) + check_default_session + ("Test Case to check TCAM2 enter programming session directly from APP",)
    #
    # Test_Case_Ex_6 = check_default_session + with_delay(SID_10_02,2) + check_programming_session + SID_10_01 + \
    #                  check_default_session + with_delay(SID_10_02,5) + check_programming_session + ("Test Case to check session 3 & 5 sec",)

    # Test_Case_Ex_7 = check_default_session + SID_10_02 + Tester_present_00 + check_programming_session + Tester_present + \
    #                  check_programming_session + SID_10_81 + check_default_session + ("64565",)
    #
    # test_case_list = [Test_Case_Ex_7]
    #
    # @pytest.mark.parametrize("test_set", test_case_list)
    # def test_example(self, test_set):
    #     validate_diagnostics_requests(test_set)

    # Test_Case_ID_61513 = SID_10_81 + Read_DTC_02 + Read_DTC_82 + ("61513: Check the response of Read DTC request with Functional Address",)
    #
    # test_case_list = [Test_Case_ID_61513]
    #
    # @L3
    # @pytest.mark.parametrize("test_set", test_case_list)
    # def test_readDTC_with_functional_address(self, test_set):
    #     validate_diagnostics_requests(test_set,AddressEnum.FUNCTIONAL_ADDRESS)
