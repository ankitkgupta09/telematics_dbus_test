import pytest
import allure
import os
import time
from config import WINDOWS,logger,ETH_CONNECTION_TIMEOUT
from interface.DeviceLogging.log_capture_interface import DeviceLogger
import threading
from config import LOGPATH,interfaces,CURRENT_TIME_STAMP
from doip_client.doip import connect_uds_server,disconnect_uds_server
from interface.SSH.SSHInterface import status_service_systemctl_in_loop
from interface.wireshark.wireshark_Interface import ip_logs

from interface.utils import clear_folder_or_files,connection_wait_in_loop,TCU_IP
from utility.SoftwareUpdate.SoftwareUpdateUtility import switch_to_active_partition
from utility.SoftwareUpdate.SoftwareUpdateEnum import Software_Partition

SOCKET_ADDRESS = interfaces.get('DOIP', 'SOCKET_ADDRESS')
TCU_LOGS = LOGPATH +"TCU_LOGS"
LOGS_UPLOAD = False
wireshark_interface = interfaces.get('logging', 'wireshark_interface')

LOGGING_SCOPE = interfaces.get('logging','LOGGING_SCOPE')
@pytest.fixture(scope=LOGGING_SCOPE, autouse=True)
def logging(request):
    if not os.path.exists(TCU_LOGS):
        os.mkdir(TCU_LOGS)
    print("Node name in request -> {}".format(request.node.name))
    # filename = "{}\\{}_{}".format(TCU_LOGS, request.node.name, CURRENT_TIME_STAMP)
    filename = "{}".format(request.node.name)
    print("Log file name will be --> {}".format(filename))
    logger_object = DeviceLogger.getInstance()
    dlt = threading.Thread(target=logger_object.dltlogcapture, args=(filename,))
    dlt.daemon = False
    dlt.start()

    def stop_test():
        print("Stop the logging")
        logger_object.dlt_close()
        if LOGS_UPLOAD:
            time.sleep(5)
            zip_log_folder()
            file_to_upload = TCU_LOGS+"\\"+"log_file.zip"
            allure.attach.file(file_to_upload,name="logs",extension=".zip")
            clear_folder_or_files(file_to_upload)
    request.addfinalizer(stop_test)

def zip_log_folder():
    """Zip the current logs capture"""
    return os.system("7z a {}\\log_file.zip {}".format(TCU_LOGS,TCU_LOGS))

@pytest.fixture(scope="session")
def sock_connection(request):
    logger.debug("DOIP connection function called")
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    status = status_service_systemctl_in_loop('uds_diagnostic_server.service', timeout=10)
    assert status, "uds_diagnostic_server.service service is not running"
    logger.debug("GRPC UDS connection using connect_uds_server function")
    status = connect_uds_server(SOCKET_ADDRESS)
    assert status, "GRPC UDS connection is not connected."

    def close_sock():
        switch_to_active_partition(Software_Partition.APPLICATION)
        logger.debug("Closing the connection")
        uds_disconnect = disconnect_uds_server()
        logger.debug("uds connection status --> {}".format(uds_disconnect))

    request.addfinalizer(close_sock)

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

@pytest.fixture(scope="module",autouse=True)
def switch_to_app(request):
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    switch_to_active_partition(Software_Partition.APPLICATION)

def pytest_addoption(parser):
    parser.addoption("--url", action="store", default=None)
