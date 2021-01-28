import allure
import pytest
from config import interfaces, config,stability,L1,ETH_CONNECTION_TIMEOUT,logger
from interface.SSH.SSHInterface import status_service_systemctl_in_loop, status_service_systemctl,\
    async_reboot_over_ssh, systemctl_service_restart
from interface.utils import connection_wait_in_loop,get_service_list,service_check
from interface.AllureReport.AllureInterface import allure_test_link
from utility.SoftwareUpdate.SoftwareUpdateUtility import switch_to_active_partition
from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition
SOCKET_ADDRESS = interfaces.get('DOIP', 'SOCKET_ADDRESS')

TCU_IP = interfaces.get('ssh', 'ip')
COMMON_SERVICE_LIST = eval(config.get('services', 'COMMON_SERVICE_LIST'))
ONLY_APP_ROOTFS_SERVICE_LIST = eval(config.get('services', 'ONLY_APP_ROOTFS_SERVICE_LIST'))
ONLY_BOOTLOADER_SERVICE_LIST = eval(config.get('services', 'ONLY_BOOTLOADER_SERVICE_LIST'))
APP_ROOTFS_SERVICE_LIST = COMMON_SERVICE_LIST + ONLY_APP_ROOTFS_SERVICE_LIST
BOOTLOADER_SERVICE_LIST = COMMON_SERVICE_LIST + ONLY_BOOTLOADER_SERVICE_LIST


def setup_module(module):
    ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
    logger.debug("========== Setup module completed =============")


@allure.sub_suite("BOOTLOADER")
@L1
class TestBTLDKERNEL(object):
    """Switch partition and Verify the service"""

    @pytest.fixture(scope="class", autouse=True)
    def switch_to_active_bootloader(self,request,sock_connection):
        """switch to active BOOTLOADER"""
        switch_to_active_partition(Software_Partition.BOOTLOADER)

    @pytest.mark.parametrize("service_name", get_service_list('infrastructure','ONLY_BOOTLOADER'))
    @allure.suite("Infrastructure")
    def test_infrastructure_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('diagnostics','ONLY_BOOTLOADER'))
    @allure.suite("Diagnostics")
    def test_diagnostics_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('software_update','ONLY_BOOTLOADER'))
    @allure.suite("Software Update")
    def test_swdl_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    # @pytest.mark.parametrize("service_name", get_service_list('telephony','ONLY_BOOTLOADER'))
    # @allure.suite("Telephony")
    # def test_telephony_service(self, service_name):
    #     """Verify the services"""
    #     allure.dynamic.title("Verify {} is running".format(service_name))
    #     # Function call from Interface to check the service status
    #     service_status = status_service_systemctl_in_loop(service_name, timeout=1)
    #     # log message to update in allure logs
    #     logger.debug("current service status {} --> {}".format(service_name, service_status))
    #     # if service is not running capturing the systemctl status of the service
    #     if not service_status:
    #         # Function call from Interface to check the systemctl status
    #         status_text = status_service_systemctl(service_name)
    #         logger.debug("Status of the service: \n%s", status_text)
    #     # validation service is running or not
    #     assert service_status == True, "{} is not running".format(service_name)
    #
    # @pytest.mark.parametrize("service_name", get_service_list('data_routing','ONLY_BOOTLOADER'))
    # @allure.suite("Data Routing")
    # def test_data_routing_service(self, service_name):
    #     """Verify the services"""
    #     allure.dynamic.title("Verify {} is running".format(service_name))
    #     # Function call from Interface to check the service status
    #     service_status = status_service_systemctl_in_loop(service_name, timeout=1)
    #     # log message to update in allure logs
    #     logger.debug("current service status {} --> {}".format(service_name, service_status))
    #     # if service is not running capturing the systemctl status of the service
    #     if not service_status:
    #         # Function call from Interface to check the systemctl status
    #         status_text = status_service_systemctl(service_name)
    #         logger.debug("Status of the service: \n%s", status_text)
    #     # validation service is running or not
    #     assert service_status == True, "{} is not running".format(service_name)


@allure.sub_suite("APPLICATION")
@L1
class TestAPPKERNEL(object):
    """Switch partition and Verify the service"""

    @pytest.fixture(scope="class", autouse=True)
    def switch_to_app(request):
        """switch to active APPLICATION"""
        switch_to_active_partition(Software_Partition.APPLICATION)

    @pytest.mark.parametrize("service_name", get_service_list('infrastructure','ONLY_APP'))
    @allure.suite("Infrastructure")
    def test_infrastructure_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name,alm_id", [("nodestatemanager.service","67695")])
    @allure.suite("Infrastructure")
    def test_infrastructure_service_restart(self, service_name,alm_id):
        allure_test_link(alm_id)
        restart_status = systemctl_service_restart(service_name)
        assert restart_status ==0,"Fail to restart the {} exit status is {}".format(service_name,restart_status)
        service_status = status_service_systemctl_in_loop(service_name, timeout=5)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('diagnostics','ONLY_APP'))
    @allure.suite("Diagnostics")
    def test_diagnostics_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('software_update','ONLY_APP'))
    @allure.suite("Software Update")
    def test_swdl_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('telephony','ONLY_APP'))
    @allure.suite("Telephony")
    def test_telephony_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)

    @pytest.mark.parametrize("service_name", get_service_list('data_routing','ONLY_APP'))
    @allure.suite("Data Routing")
    def test_data_routing_service(self, service_name):
        """Verify the services"""
        allure.dynamic.title("Verify {} is running".format(service_name))
        # Function call from Interface to check the service status
        service_status = status_service_systemctl_in_loop(service_name, timeout=1)
        # log message to update in allure logs
        logger.debug("current service status {} --> {}".format(service_name, service_status))
        # if service is not running capturing the systemctl status of the service
        if not service_status:
            # Function call from Interface to check the systemctl status
            status_text = status_service_systemctl(service_name)
            logger.debug("Status of the service: \n%s", status_text)
        # validation service is running or not
        assert service_status == True, "{} is not running".format(service_name)


@allure.parent_suite("Services Check")
@allure.suite("373: Stability Test")
@stability
class TestBootloaderStability(object):
    """Switch partition and Verify the service"""
    @pytest.fixture(scope="class", autouse=True)
    def switch_to_active_bootloader(self,request,sock_connection):
        """switch to active BOOTLOADER"""
        switch_to_active_partition(Software_Partition.BOOTLOADER)

    def test_service(self):
        """Verify the services"""
        allure_test_link("61848")
        # TODO reboot should be change to power supply, for now setup doesn't have PPS
        async_reboot_over_ssh()
        setup_module(TestBootloaderStability)
        service_check(BOOTLOADER_SERVICE_LIST)


@allure.parent_suite("Services Check")
@allure.suite("373: Stability Test")
@stability
class TestApplicationStability(object):
    """Switch partition and Verify the service"""
    @classmethod
    def setup_class(cls):
        """switch to active APPLICATION"""
        switch_to_active_partition(Software_Partition.APPLICATION)

    def test_service(self):
        """Verify the services"""
        allure_test_link("61665")
        # To-Do reboot should be change to power supply, for now setup doesn't have PPS
        async_reboot_over_ssh()
        setup_module(TestApplicationStability)
        service_check(APP_ROOTFS_SERVICE_LIST)
