import pytest
import allure
from interface.AllureReport.AllureInterface import allure_test_link
from interface.utils import connection_wait_in_loop,TCU_IP
from interface.SSH.SSHInterface import execute_command_and_return_console_output
from config import interfaces, L1, L2, L3, under_development, KPI, peripherals, ETH_CONNECTION_TIMEOUT, logger
from interface.utils import connection_wait_in_loop, get_configuration_from_file
from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition
from utility.SoftwareUpdate.SoftwareUpdateUtility import async_reset_tcu, get_current_partition, image_selection_help, \
    switch_to_active_partition, lock_partition, wuc_version, wuc_sw_update



def setup_module(module):
    ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
    logger.debug("========== Setup module completed =============")


@allure.suite("PowerManagement")
@allure.sub_suite("382: PowerManagement Test")
class TestPowerManagement(object):
    """Collection of PowerManagement test cases"""

    @L2
    def test_setboot_config(self):
        allure_test_link("63094")
        switch_to_active_partition(Software_Partition.APPLICATION)

    @L1
    def test_getbootconfig(self):
        allure_test_link("62775")
        current_partition = get_current_partition()
        logger.debug("Current partition is --> {}".format(current_partition))
        status=image_selection_help()
        assert status,"Failed to display imageSelection help options"

    @L2
    def test_lockbootconfig(self):
        allure_test_link("63098")
        lock_status=lock_partition(1)
        assert lock_status, "WUC SoftwareUpdate is unsuccessful --> {}".format(lock_status)

    @L2
    def test_reset_tcu(self):
        allure_test_link("63095")
        async_reset_tcu(1)
        ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)

    @under_development
    def test_wuc_sw_update_3(self):
        allure_test_link("63215")
        status=execute_command_and_return_console_output("ls -l /opt/bin/tcam_wuc.s19|wc -l|tr -d '\n'")
        logger.debug("status is {}".format(status))
        if status == "1":
            for i in range(3):
                wuc_stat = wuc_sw_update("/opt/bin/tcam_wuc.s19")
                assert wuc_stat, "WUC SoftwareUpdate is unsuccessful --> {}".format(wuc_stat)
                current_partition = get_current_partition()
                logger.debug("Current partition is --> {}".format(current_partition))
                switch_to_active_partition(Software_Partition.APPLICATION)
                async_reset_tcu(1)
                ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
                assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
                wuc_ver = wuc_version()
                logger.debug("WUC Version is --> {}".format(wuc_ver))
                lock_status=lock_partition(1)
                assert lock_status, "WUC SoftwareUpdate is unsuccessful --> {}".format(lock_status)
        else:
            logger.debug("WUC file not present for updation")
            assert status == "1","WUC file not present for updation"
        
    @under_development
    def test_wuc_sw_update(self):
        allure_test_link("63214")
        status=execute_command_and_return_console_output("ls -l /opt/bin/tcam_wuc.s19|wc -l|tr -d '\n'")
        logger.debug("status is {}".format(status))
        if status == "1":
            wuc_stat = wuc_sw_update("/opt/bin/tcam_wuc.s19")
            assert wuc_stat, "WUC SoftwareUpdate is unsuccessful --> {}".format(wuc_stat)
            current_partition = get_current_partition()
            logger.debug("Current partition is --> {}".format(current_partition))
            switch_to_active_partition(Software_Partition.APPLICATION)
            async_reset_tcu(1)
            ip_connection = connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
            assert ip_connection < ETH_CONNECTION_TIMEOUT, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
            wuc_ver = wuc_version()
            logger.debug("WUC Version is --> {}".format(wuc_ver))
            lock_status=lock_partition(1)
            assert lock_status, "WUC SoftwareUpdate is unsuccessful --> {}".format(lock_status)
        else:
            logger.debug("WUC file not present for updation")
            assert status == "1","WUC file not present for updation"

    def teardown_class(cls):
        """Switch back to APP"""
        switch_to_active_partition(Software_Partition.APPLICATION)

