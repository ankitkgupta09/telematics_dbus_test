import pytest
import allure
from interface.utils import connection_wait_in_loop, TCU_IP
from interface.AllureReport.AllureInterface import allure_test_link
from interface.SSH.SSHInterface import execute_command_and_return_console_output, \
    execute_command_and_return_value, execute_command_on_active_shell_and_return_console_output, close_shell
from config import ETH_CONNECTION_TIMEOUT, logger,L3,under_development
from utility.Infrastructure.InfraUtility import open_application_get_items,press_option_in_open_application


def setup_module(module):
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)


@allure.suite("Infrastructure")
@L3
class TestInfrastructure(object):
    """collection of Infrastructure test cases"""

    Test_Case_ID_62510 = ("strace", "62510")
    Test_Case_ID_63485 = ("systemd-analyze", "63485")
    Test_Case_ID_63057 = ("valgrind", "63057")
    test_case_list = [Test_Case_ID_62510, Test_Case_ID_63485,Test_Case_ID_63057]

    @pytest.mark.parametrize("utility,alm_id", test_case_list)
    def test_check_strace_is_present(self,utility,alm_id):
        """Check /usr/bin space for binary availability"""
        allure_test_link(alm_id)
        is_present = execute_command_and_return_console_output("ls /usr/bin/ | grep {}".format(utility))
        logger.debug("Is present status --> {}".format(is_present))
        assert utility in is_present, "{} is not present in /usr/bin/".format(utility)

    def test_strace_functionality_check(self):
        """Check strace binary functionality"""
        allure_test_link("62511")
        exist_status = execute_command_and_return_value("strace -o demo.out ls")
        logger.debug("strace cmd exist status --> {}".format(exist_status))
        assert exist_status == 0, "strace cmd is not run properly exist status is --> {}".format(exist_status)
        demo_file_content = execute_command_and_return_console_output("cat demo.out")
        logger.debug("Demo file contain --> {}".format(demo_file_content))
        assert demo_file_content is not "", "demo.out file is empty"

    def test_valgrind_functionality_check(self):
        """Check valgrind binary functionality"""
        allure_test_link("63058")
        exist_status = execute_command_and_return_value("valgrind ls")
        logger.debug("strace cmd exist status --> {}".format(exist_status))
        assert exist_status == 0, "valgrind cmd is not run properly exist status is --> {}".format(exist_status)
        valgrind_output = execute_command_and_return_console_output("valgrind ls")
        logger.debug("valgrind ls output --> {}".format(valgrind_output))
        assert valgrind_output is not "", "valgrind ls output is empty"

    Test_Case_ID_63487 = ("blame", "63487")
    Test_Case_ID_63486 = ("time", "63486")
    test_case_list = [Test_Case_ID_63487, Test_Case_ID_63486]

    @pytest.mark.parametrize("utility,alm_id", test_case_list)
    def test_check_systemd_analyze_functionality(self,utility,alm_id):
        """Check systemd analyze functionality"""
        allure_test_link(alm_id)
        analyze_output = execute_command_and_return_console_output("systemd-analyze {}".format(utility))
        logger.debug("systemd-analyze output --> {}".format(analyze_output))
        # assert utility in analyze_output, "{} is not present in /usr/bin/".format(utility)


@under_development
@allure.suite("Infrastructure")
class TestNSMRegularClient(object):

    @pytest.fixture(scope="function")
    def open_nsm_application(self,request):
        """Open nsm Application"""
        option =  open_application_get_items("NSMRegularClient",".")

        def close_nsm_application():
            execute_command_on_active_shell_and_return_console_output("13")
            execute_command_on_active_shell_and_return_console_output("\x03", timeout=2)
            close_shell()

        request.addfinalizer(close_nsm_application)
        return option

    test_case_67694 = ([("Get node state","Node state is fullyOperational")],"67694")
    test_case_67703 = ([("Get interface Version","The version is :")],"67703")
    test_case_67698 = ([("Get Application mode","Application ID is :")],"67698")
    test_case_67696 = ([("Set Session State"," ")],"67696")
    test_case_67697 = ([("Get session state"," ")],"67697")
    test_case_67702 = ([("Unregister session"," ")],"67702")
    test_case_67701 = ([("Register Session"," ")],"67701")
    test_case_67700 = ([("Unregister shutdown client"," ")],"67700")
    # test_case_67699 = ([("Register shutdown client","")],"67699")

    test_case_list = [test_case_67694,test_case_67703,test_case_67698,test_case_67696,
                      test_case_67697,test_case_67702,test_case_67701,test_case_67700]

    @pytest.mark.parametrize("ops,alm_id", test_case_list)
    def test_nsm_regular_client(self,ops,alm_id,open_nsm_application):
        allure_test_link(alm_id)
        logger.debug("Testing option is -- {}".format(ops))
        press_option_in_open_application(open_nsm_application,ops)

