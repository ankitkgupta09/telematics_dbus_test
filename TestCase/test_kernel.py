import allure
import pytest
import time
from interface.utils import connection_wait_in_loop,TCU_IP,restart
from interface.AllureReport.AllureInterface import allure_test_link,update_kpi_in_allure
from interface.SSH.SSHInterface import execute_command_and_return_value,execute_command_and_return_console_output,async_reboot_over_ssh
from config import logger, L1,L2,KPI,ETH_CONNECTION_TIMEOUT

under_development = pytest.mark.under_development

def setup_module(module):
    ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
    logger.debug("========== Setup module completed =============")

@allure.suite("Kernel")
@allure.sub_suite("333: Sanity Test")
class TestKernel(object):
    """Collection of Kernel test cases"""

    @L1
    def test_ping(self):
        """Verify that ping is working fine"""
        allure_test_link("47753")
        ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)

    @L1
    def test_ssh(self):
        """Verify that SSH to TCU is working fine"""
        allure_test_link("47754")
        assert execute_command_and_return_value("ls") == 0,"Fail to Run ls command over SSH"

@allure.suite("System")
@allure.sub_suite("394: KPI Measurement")
class TestKPIMeasurement(object):

    @pytest.fixture(scope="class", autouse=True)
    def check_restart(request):
        """reboot the device before capturing KPI data"""
        # TODO need to enable the PPS code when we have PPS connected to setup
        # restart(ipConnection_Timeout=1,connection_status=False)
        async_reboot_over_ssh()  # added for temporary no PPS connected in setup
        setup_module(TestKPIMeasurement)

    Test_Case_ID_59824 = ("cpu_status", "top -b -n 1 | egrep 'CPU:' |grep -v egrep", "59824")
    Test_Case_ID_59825 = ("ram_status", "free", "59825")
    test_case_list = [Test_Case_ID_59824, Test_Case_ID_59825]

    @pytest.mark.parametrize("process,cmd,alm_id", test_case_list)
    @KPI
    def test_check_system_kpi(self, process, cmd, alm_id):
        """capture the system KPI data"""
        allure_test_link(alm_id)
        kpi_status = execute_command_and_return_console_output(cmd)
        logger.debug("Output of {0} -->{1}".format(process, kpi_status))
        update_kpi_in_allure("KPI data for {0} -->{1}".format(process, kpi_status))
