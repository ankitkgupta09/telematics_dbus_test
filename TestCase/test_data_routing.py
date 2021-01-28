import pytest
import allure
import time
from interface.utils import connection_wait_in_loop, TCU_IP
from interface.AllureReport.AllureInterface import allure_test_link
from interface.SSH.SSHInterface import execute_command_and_return_console_output, \
    execute_command_on_active_shell_and_return_console_output,execute_command_and_return_value, \
        close_shell
from config import ETH_CONNECTION_TIMEOUT, logger, L2, L1, L3
from utility.Telephony.TelephonyUtility import nad_status, data_turn_on, data_status, \
    object_path_ril_0, busname_ofono, interface_LongTermEvolution, internet_APN
from utility.DataRouting.DataRoutingUtility import set_default_route,enable_tethering,\
    check_tether_ping,wait_modem_state
from interface.utils import restart

under_development = pytest.mark.under_development

ping_address = "8.8.8.8"        


def setup_module(module):
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)


@allure.suite("Data Routing")
class TestDataRouting(object):
    """collection of Infrastructure test cases"""

    Test_Case_ID_63005 = ("at-client", "63005")

    test_case_list = [Test_Case_ID_63005]

    @pytest.mark.parametrize("utility,alm_id", test_case_list)
    @L2
    def test_check_utility_is_present(self, utility, alm_id):
        """Check /usr/bin space for binary availability"""
        allure_test_link(alm_id)
        is_present = execute_command_and_return_console_output("ls /usr/bin/ | grep {}".format(utility))
        logger.debug("Is present status --> {}".format(is_present))
        assert utility in is_present, "{} is not present in /usr/bin/".format(utility)

    Test_Case_ID_63012 = ("AT+CPIN?", "63012")
    Test_Case_ID_63006 = ("AT+CGMR", "63006")
    test_case_list = [Test_Case_ID_63012, Test_Case_ID_63006]

    @under_development
    @pytest.mark.parametrize("at_cmd,alm_id", test_case_list)
    def test_validate_at_command(self, at_cmd, alm_id):
        """Validate AT commands"""
        allure_test_link(alm_id)
        at_port = 225
        cmd = "at-client {} {} {}".format(TCU_IP, at_port, at_cmd)
        at_output = execute_command_on_active_shell_and_return_console_output(cmd, timeout=10)
        time.sleep(1)
        execute_command_on_active_shell_and_return_console_output("\x03", timeout=5)
        logger.debug("AT command output --> {}".format(at_output))
        assert "ok" in at_output.lower(), "AT command -- {} is not run properly".format(at_cmd)

    Test_Case_ID_63318 = ("online", "63318")
    test_case_list = [Test_Case_ID_63318]

    @pytest.mark.parametrize("exp_state,alm_id", test_case_list)
    @L1
    def test_validate_modem_state(self, exp_state, alm_id):
        """Validate Modem state as Active after bootup"""
        allure_test_link(alm_id)
        state = execute_command_and_return_console_output(
            "/bin/cat /sys/devices/platform/cpif/modem_state")
        assert exp_state in state.lower(), "Modem state in not active. current state {}".format(state)
        logger.debug("Modem is currently Active.")

    Test_Case_ID_63003 = ("/usr/bin/at-relay", "63003")
    test_case_list = [Test_Case_ID_63003]

    @pytest.mark.parametrize("service,alm_id", test_case_list)
    @L1
    def test_at_relay_service(self, service, alm_id):
        """Validate Modem state as Active after boot up"""
        allure_test_link(alm_id)
        is_running = execute_command_and_return_console_output("ps|grep at-relay")
        assert service in is_running.lower(), "at-relay curently not running. Outcome {}".format(is_running)
        logger.debug("at-relay running")

    @L1
    def test_modem_up(self):
        """Verify modem Online property after boot up"""
        alm_id = "63759"
        allure_test_link(alm_id)
        logger.debug("Starting test modem up")
        is_online = nad_status(object_path_ril_0)
        assert is_online, "Modem online property is false after boot up. {}".format(is_online)
        logger.debug("Modem is currently up and online. Online: {}".format(is_online))
    
    @L2
    def test_enable_data(self):
        """Enable PDN Connection"""
        allure_test_link("63923")
        logger.debug("Starting test enable data pdn.")
        pdn_info = data_turn_on(internet_APN, object_path_ril_0)
        logger.debug("PDN Info:\n{}".format(pdn_info))
        assert pdn_info["Interface"], "Failed to Activate data PDN. PDN Info: {}".format(pdn_info)
        logger.debug("PDN Information:\n{}".format(pdn_info))
        logger.debug("Internet PDN Enabled successfully")

    @L2
    def test_get_internet_apn(self):
        """will get the interface name for internet apn"""
        allure_test_link("63762")
        logger.debug("Starting test get internet apn.")
        is_active = data_status(object_path_ril_0)["Active"]
        if not is_active:
            data_turn_on(internet_APN, object_path_ril_0)
        pdn_info = data_status(object_path_ril_0)
        logger.debug("PDN Info:\n{}".format(pdn_info))
        assert pdn_info["Interface"], "Failed to Activate data PDN. PDN Info: {}".format(pdn_info)
        logger.debug("PDN Interface name is: {}".format(pdn_info["Interface"]))
        logger.debug("Internet PDN Enabled successfully")

    @L2
    def test_set_default_route(self):
        """Set default gw data pdn"""
        allure_test_link("63918")
        logger.debug("Starting test set default gw as data pdn")
        cmd = "/sbin/route add default gw "
        pdn_info = data_status(object_path_ril_0)
        assert pdn_info["Active"], "No internet pdn available. Response: {}".format(pdn_info)
        logger.debug("Found internet APN. Info:\nInterface name: {0}\nActive State: {1}\nAddress: {2}".format(pdn_info["Interface"], pdn_info["Active"], \
                                          pdn_info["Address"]))
        # set default gw as APN address
        print(cmd+pdn_info["Address"])
        exec_status = execute_command_and_return_value(cmd + pdn_info["Address"])
        assert exec_status is 0, "Failed to set default gw. execution status: {}".format(exec_status)
        logger.debug("Setting default gateway as APN Address is Success")

    @L2
    def test_validate_default_route(self):
        """will validate default route as pdn address"""
        allure_test_link("63762")
        logger.debug("Starting test validate default gw as data pdn")
        pdn_interface = data_status(object_path_ril_0)
        route_dflt = execute_command_and_return_console_output("/sbin/ip route | grep default")
        route_dflt = str(route_dflt).replace("\n","")
        route_dflt = route_dflt.split(" ")
        assert pdn_interface["Address"] in route_dflt[2] and pdn_interface["Interface"] in route_dflt[4],"{0} not found in {1}".format(pdn_interface,route_dflt)
        logger.debug("PDN Interface available as default route.")

    @L2
    def test_validate_default_route_ping(self):
        """will validate ping to 8.8.8.8 via default route"""
        allure_test_link("63763")
        logger.debug("Starting test validate ping over default route")
        is_active = data_status(object_path_ril_0)["Active"]
        if not is_active:
            data_turn_on(internet_APN, object_path_ril_0)
            cmd = "/sbin/route add default gw "
            pdn_info = data_status(object_path_ril_0)
            assert pdn_info["Active"], "Failed to Activate PDN. Response: {}".format(pdn_info)
            # set default gw as APN address
            time.sleep(2)
            logger.debug("Command to execute: %s" % (cmd+pdn_info["Address"]))
            exec_status = execute_command_and_return_value(cmd + pdn_info["Address"])
            assert exec_status is 0, "Failed to Set default gw. execution status: {}".format(exec_status)
            logger.debug("PDN activated and Default route set. ==> Success")
        ping_cmd = "/bin/ping -c 3 {}".format(ping_address)
        ping_data = execute_command_and_return_console_output(ping_cmd)
        assert "3 packets received" in ping_data, "Packet loss when trying to ping. Ping Output:\n{}".format(ping_data)
        logger.debug("Ping from default route validated.\nPing Output:\n{}".format(ping_data))
        
    @L2
    def test_ethernet_tethering(self):
        """will be enabling ethernet tethering and testing it"""
        allure_test_link("63891")
        logger.debug("Starting Test Enable Tethering")
        # check if data is active or not
        is_active = data_status(object_path_ril_0)["Active"]
        if not is_active:
            data_turn_on(internet_APN, object_path_ril_0)
        # adding default route
        is_set = set_default_route(object_path_ril_0)        
        assert is_set,"Failed to set default route"
        # enableing tethering
        assert enable_tethering(object_path_ril_0),"Failed to enable tethering"
        # check tethering ping
        assert check_tether_ping(ping_address),"Failed to ping Address: {}".format(ping_address)
        logger.debug("Ethernet Tethering Completed. ==> PASS")

    @L3
    def test_set_apn_dns_resolution(self):
        """will set apn for dns resolution"""
        allure_test_link("65671")
        logger.debug("Starting Test Set APN for DNS Resolution")
        is_available = execute_command_and_return_value("/bin/grep {0} /opt/hrtp/bin/connectivity/dnsset/connect.sh".format(internet_APN))
        if is_available:
            logger.info("Correct APN not set in connect.sh. Replacing correct APN")
            execute_command_and_return_console_output("/bin/mount -o remount rw, /")
            cur_apn = execute_command_and_return_console_output("/bin/grep -w 'AccessPointName' /opt/hrtp/bin/connectivity/dnsset/connect.sh | cut -d: -f4")
            cur_apn = str(cur_apn).replace('"','')
            cur_apn = cur_apn.replace("\n","")
            logger.debug("Current APN is: {}".format(cur_apn))
            command = r"/bin/sed -i 's/{0}/{1}/' /opt/hrtp/bin/connectivity/dnsset/connect.sh".format(cur_apn,internet_APN)
            print("CMD: %s" % command)
            exec_status = execute_command_and_return_value(command)
            assert exec_status is 0,"Failed to set APN on connect.sh. Current-APN: {0} Replacing-APN: {1} Response: {2}".format(cur_apn,internet_APN,exec_status)
            logger.debug("APN Set Success. Replaced APN: {}".format(internet_APN))
        logger.debug("Set APN for DNS Resolution Completed. ==> PASS")
        
    @L3
    def test_check_dns_resolution(self):
        """will check dns resolution"""
        allure_test_link("65672")
        logger.debug("Starting Test check DNS Resolution")
        # Restart TCU
        restart()
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        assert wait_modem_state(object_path_ril_0,True),"Modem State not True after waiting for 30 sec"
        execute_command_on_active_shell_and_return_console_output("cd /opt/hrtp/bin/connectivity/dnsset/")
        execute_command_on_active_shell_and_return_console_output("./dnsset")
        time.sleep(5)
        exec_outcome = execute_command_on_active_shell_and_return_console_output("")
        assert "method return sender" in exec_outcome.lower(),"Unsuccessful while executing ./dnsset"
        close_shell()
        ping_cmd = "/bin/ping -c 3 www.google.com"
        ping_data = execute_command_and_return_console_output(ping_cmd)
        assert "3 packets received" in ping_data, "Packet loss when trying to ping. Ping Output:\n{}".format(ping_data)
        logger.debug("Set check DNS Resolution Completed. ==> PASS")

    Test_Case_ID_67628 = ("eth0.151", "198.19.36.202", "67628")
    Test_Case_ID_67629 = ("eth0.152", "198.19.40.202", "67629")
    Test_Case_ID_67630 = ("eth0.153", "198.19.44.202", "67629")
    Test_Case_ID_67631 = ("eth0.154", "198.19.48.202", "67631")
    Test_Case_ID_67632 = ("eth0.155", "198.19.52.202", "67632")
    Test_Case_ID_67633 = ("eth0.156", "198.19.56.202", "67633")
    Test_Case_ID_67634 = ("eth0.157", "198.19.60.202", "67634")
    test_case_list = [Test_Case_ID_67628, Test_Case_ID_67629, Test_Case_ID_67630,
                      Test_Case_ID_67631, Test_Case_ID_67632,
                      Test_Case_ID_67633, Test_Case_ID_67634]

    @under_development
    @pytest.mark.parametrize("eth_cmd, eth_ip, alm_id", test_case_list)
    def test_validate_VLAN_eth(self, eth_cmd, eth_ip, alm_id):
        """Validate VLAN eth commands"""
        allure_test_link(alm_id)
        mac_address = "02:00:00:00:20:18"
        mac_address_cmd = '/sbin/ifconfig -a {}|head -n 1|cut -d" " -f7'.format(eth_cmd)
        mac_address_output = execute_command_and_return_console_output(mac_address_cmd)
        logger.debug("MAC address is --> {}".format(mac_address_output))
        assert mac_address_output.strip() == mac_address, "MAC address -- {} is not same " \
                                                  "as {}".format(mac_address_output, mac_address)

        get_ip_cmd = "/sbin/ifconfig -a {}|head -n 2|tail -n 1 |cut -d ':' -f2|cut -d' ' -f1".format(eth_cmd)
        get_ip_output = execute_command_and_return_console_output(get_ip_cmd)
        logger.debug("IP address of the {} --> {}".format(eth_cmd,get_ip_output))
        assert get_ip_output.strip() == eth_ip, "Get IP address --{} is not same as {}".format(get_ip_output, eth_ip)

    Test_Case_ID_68009 = ("198.19.36.202", "68009")
    Test_Case_ID_68010 = ("198.19.40.202", "68010")
    Test_Case_ID_68011 = ("198.19.44.202", "68011")
    Test_Case_ID_68012 = ("198.19.48.202", "68012")
    Test_Case_ID_68013 = ("198.19.52.202", "68013")
    Test_Case_ID_68014 = ("198.19.56.202", "68014")
    Test_Case_ID_68015 = ("198.19.60.202", "68015")
    test_case_list = [Test_Case_ID_68009, Test_Case_ID_68010, Test_Case_ID_68011, Test_Case_ID_68012,
                      Test_Case_ID_68013, Test_Case_ID_68014, Test_Case_ID_68015]

    @under_development
    @pytest.mark.parametrize("eth_ip, alm_id", test_case_list)
    def test_validate_VLAN_eth_ping_command(self, eth_ip, alm_id):
        """Validate VLAN eth ping commands"""
        allure_test_link(alm_id)
        ping_command = "ping -c1 " + eth_ip
        ping_command_output = execute_command_and_return_console_output(ping_command, timeout=5)
        logger.debug("Ping command is --> {}, response is --> {}".format(ping_command,ping_command_output))
        assert 'TTL' in ping_command_output.upper(), "Ping command -- {} is not run successfully ".format(ping_command)


@allure.parent_suite("Data Routing")
class TestLinkMonitoring(object):

    @L2
    def test_check_eth0_TX_Packets(self):
        """
        will check eth0 TX Packets count
        """
        allure_test_link("67443")
        logger.debug("Starting Test check eth0 TX Packets count")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_tx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_packets")
        first_tx_packets = first_tx_packets.replace('\n','')
        # check if return packet is a packet count or number
        assert first_tx_packets.isdigit(),"Returned TX Packets are not numbers"
        time.sleep(2)
        sec_tx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_packets")
        sec_tx_packets = sec_tx_packets.replace('\n','')
        assert sec_tx_packets.isdigit(),"Returned TX Packets are not numbers"
        #check if return packets are not decreasing
        assert int(first_tx_packets) <= int(sec_tx_packets),"Packets Count should not decrease over time"
        logger.debug("Check TX Packets count Completed. ==> PASS")

    @L2
    def test_check_eth0_TX_Bytes(self):
        """
        will check eth0 TX Bytes count
        """
        allure_test_link("67444")
        logger.debug("Starting Test check eth0 TX Packets count")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_count = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_bytes")
        first_count = first_count.replace('\n','')
        # check if return packet is a packet count or number
        assert first_count.isdigit(),"Returned Count is not Number"
        time.sleep(2)
        sec_count = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_bytes")
        sec_count = sec_count.replace('\n','')
        assert sec_count.isdigit(),"Returned Count is not Number"
        #check if return packets are not decreasing
        assert int(first_count) <= int(sec_count),"Bytes Count should not decrease over time"
        logger.debug("Check TX Bytes count Completed. ==> PASS")

    @L2
    def test_check_eth0_RX_Packets(self):
        """
        will check eth0 RX Packets count
        """
        allure_test_link("67445")
        logger.debug("Starting Test check eth0 TX Packets count")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_rx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/rx_packets")
        first_rx_packets = first_rx_packets.replace('\n','')
        # check if return packet is a packet count or number
        assert first_rx_packets.isdigit(),"Returned RX Packets are not numbers"
        time.sleep(2)
        sec_rx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/rx_packets")
        sec_rx_packets = sec_rx_packets.replace('\n','')
        assert sec_rx_packets.isdigit(),"Returned RX Packets are not numbers"
        #check if return packets are not decreasing
        assert int(first_rx_packets) <= int(sec_rx_packets),"Packets Count should not decrease over time"
        logger.debug("Check RX Packets count Completed. ==> PASS")

    @L2
    def test_check_eth0_RX_Bytes(self):
        """
        will check eth0 RX Bytes count
        """
        allure_test_link("67446")
        logger.debug("Starting Test check eth0 TX Packets count")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_rx_bytes = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/rx_bytes")
        first_rx_bytes = first_rx_bytes.replace('\n','')
        # check if return packet is a packet count or number
        assert first_rx_bytes.isdigit(),"Returned RX Bytes are not numbers"
        time.sleep(2)
        sec_rx_bytes = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/rx_bytes")
        sec_rx_bytes = sec_rx_bytes.replace('\n','')
        assert sec_rx_bytes.isdigit(),"Returned RX Bytes are not numbers"
        #check if return packets are not decreasing
        assert int(first_rx_bytes) <= int(sec_rx_bytes),"Bytes Count should not decrease over time"
        logger.debug("Check RX Bytes count Completed. ==> PASS")

    @L2
    def test_check_eth0_TX_Packets_drop(self):
        """
        will check eth0 TX Packets Drop
        """
        allure_test_link("67447")
        logger.debug("Starting Test check eth0 TX Packets Drop")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_tx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_dropped")
        first_tx_packets = first_tx_packets.replace('\n','')
        # check if return packet is a packet count or number
        assert first_tx_packets.isdigit(),"Returned TX Packets Drop is not number"
        logger.debug("Current TX Packets Drop count is: {}".format(first_tx_packets))
        logger.debug("Check TX Packets Drop Completed. ==> PASS")

    @L2
    def test_check_eth0_RX_Packets_drop(self):
        """
        will check eth0 RX Packets Drop
        """
        allure_test_link("67448")
        logger.debug("Starting Test check eth0 RX Packets Drop")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        first_rx_packets = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/rx_dropped")
        first_rx_packets = first_rx_packets.replace('\n','')
        # check if return packet is a packet count or number
        assert first_rx_packets.isdigit(),"Returned RX Packets Drop is not number"
        logger.debug("Current RX Packets Drop count is: {}".format(first_rx_packets))
        logger.debug("Check RX Packets Drop Completed. ==> PASS")
        
    @L2
    def test_check_eth0_transmission_error(self):
        """
        will check eth0 Transmission Error
        """
        allure_test_link("67449")
        logger.debug("Starting Test check eth0 Transmission Error")
        connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
        error_count = execute_command_and_return_console_output("cat /sys/class/net/eth0/statistics/tx_errors")
        error_count = error_count.replace('\n','')
        # check if return packet is a packet count or number
        assert error_count.isdigit(),"Returned Transmission Error is not number"
        logger.debug("Current Transmission Error count is: {}".format(error_count))
        logger.debug("Check Transmission Error Completed. ==> PASS")

    
