from interface.dbus.Dbus_interface import dbus_function_verification, \
    signal_call_async, get_async_result, dbus_function_verification_async
import pytest
from gta_release.tmbu.utils import update_modem
from utility.Telephony.TelephonyUtility import *
from interface.utils import connection_wait_in_loop
from interface.AllureReport.AllureInterface import allure_test_link
from config import stability,ETH_CONNECTION_TIMEOUT

TCU_SIM_1 = "'{}'".format(board.get('TCU_Number', 'board_number'))
TCU_SIM_2 = "'{}'".format(board.get('TCU_Number', 'board_number_2'))
Mobile_SIM_1 = "'{}'".format(peripherals.get('Mobile', 'MobileNumber_1'))
Mobile_SIM_2 = "'{}'".format(peripherals.get('Mobile', 'MobileNumber_2'))
id1 = peripherals.get('Mobile', 'id1')
id2 = peripherals.get('Mobile', 'id2')
Valid_Network_state = ['registered', 'roaming']
SIM_object_list = eval(config.get('SIM_Operator', 'SIM_object_list'))
RAT_ALL = eval(config.get(Operator_name, 'RAT'))
TCU_Number = 0
ussd_codes = eval(config.get(Operator_name, 'USSDCodes'))
USSDCodes_response = eval(config.get(Operator_name, 'USSDCodes_responce'))


@pytest.fixture(scope="module", params=SIM_object_list)
def sim_object(request):
    connection_wait_in_loop(TCU_IP, ETH_CONNECTION_TIMEOUT)
    global TCU_Number
    ril_object = request.param
    if not API_OVER_DBUS:
        status = status_service_systemctl_in_loop("grpc-server", timeout=20)
        logger.debug("GRPC server status -- {}".format(status))
        logger.debug("Update the mode binary to {}".format(ril_object))
        update_modem(ril_object)
    logger.debug("Current SIM card is {}".format(ril_object))
    if ril_object == object_path_ril_0:
        service_name = 'cp-boot'
        TCU_Number = TCU_SIM_1
    else:
        service_name = 'cp-boot-consumer'
        TCU_Number = TCU_SIM_2
    status = status_service_systemctl_in_loop(service_name, timeout=20)
    at_status = get_modem_status_by_at(ril_object)
    logger.debug("AT status is %s", at_status)
    assert status,"{} service is not running".format(service_name)
    status = status_service_systemctl_in_loop('ofono', timeout=5)
    assert status, "ofono service is not running"
    modem_restart_if_not_online(ril_object)

    for i in range(0, 5):
        try:
            sm_status = sim_status(ril_object)[0]
            if sm_status:
                break
            time.sleep(1)
        except Exception as e:
            logger.error("Exception -- {} in reading SIM property try count -- {}".format(e,i))
            pass
    assert sm_status,"{} card is not present".format(ril_object)
    network_status = wait_for_registration(ril_object, Valid_Network_state, 20)
    if not network_status:
        logger.error("Network is not resisted in first boot-up {}".format(ril_object))
        modem_restart(ril_object=ril_object)
        time.sleep(2)
        network_status = wait_for_registration(ril_object, Valid_Network_state, 30)
        assert network_status, "Network is not registered after OFFLINE/ONLINE as well {}".format(ril_object)
    return request.param

@pytest.fixture(scope="module", params=RAT_ALL)
def rat(request, sim_object):
    switch_rat(sim_object, request.param)
    return request.param

@allure.suite("Telephony")
class TestTelephony(object):

    @L1
    def test_registration(self,sim_object):
        try:
            alm_id = {object_path_ril_0: "63007",
                      object_path_ril_1: "",
                      }
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Network registration is working on {}".format(sim_object))
        logger.info("Network registration is working on -- {}".format(sim_object))

    @L3
    def test_registration(self,sim_object,rat):
        try:
            alm_id = {object_path_ril_0: {"4G_PREF": "63007","2G":"63211"},
                      object_path_ril_1: {},
                      }
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Network registration is working on {}".format(rat))
        logger.info("Network registration is working on -- {}".format(rat))

    @L1
    def test_switching(self,sim_object):
        try:
            alm_id = {object_path_ril_0: "63142",
                      object_path_ril_1: "",
                      }
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: switch different RAT {}".format(sim_object))
            for rat_value in RAT_ALL:
                switch_rat(sim_object,rat_value)

    @L2
    @stability
    def test_mo_sms(self, sim_object, rat):
        try:
            alm_id = {object_path_ril_0: {"2G": "63196", "3G": "63197","4G_PREF": "63198",
                                          "NO_CHANGE": "63013: Verify MO SMS on default RAT"},
                      object_path_ril_1: {"2G": "", "3G": "", "4G_PREF": ""}
                      }
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Send a SMS from TCU to Mobile on {}".format(rat))
        send_sms_from_tcu(Mobile_SIM_1, ril_object=sim_object)

    @L1
    def test_mo_sms_default_rat(self, sim_object):
        try:
            alm_id = {object_path_ril_0: "63013",
                      object_path_ril_1: ""
                      }
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Send a SMS from TCU to Mobile on {}".format(sim_object))
        send_sms_from_tcu(Mobile_SIM_1, ril_object=sim_object)

    @L1
    def test_mo_call_default_rat(self, sim_object):
        try:
            alm_id = {object_path_ril_0: "63009",
                      object_path_ril_1: ""}
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Make a call from TCU to Mobile on default RAT ril -- {}".format(sim_object))
        mo_call_answer_and_hangup(sim_object, Mobile_SIM_1, id1)

    @stability
    @L2
    def test_mo_call(self, sim_object, rat):
        try:
            alm_id = {object_path_ril_0: {"2G": "63147", "3G": "63148",
                                          "4G_PREF": "63151"},
                      object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Make a call from TCU to Mobile on {}".format(rat))
        mo_call_answer_and_hangup(sim_object, Mobile_SIM_1, id1)

    @L1
    def test_mt_call_default_rat(self, sim_object):
        try:
            alm_id = {object_path_ril_0: "63011",
                      object_path_ril_1: ""}
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Make a call from Mobile to TCU on default rat {}".format(sim_object))
        mt_call_answer_and_hangup(sim_object, TCU_Number, id1, hangup_side="TCU")

    @stability
    @L2
    def test_mt_call(self, sim_object, rat):
        try:
            alm_id = {object_path_ril_0: {"2G": "63152","3G": "","4G_PREF": "63155",},
                      object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Make a call from Mobile to TCU and answer on {}".format(sim_object))
        mt_call_answer_and_hangup(sim_object, TCU_Number, id1, hangup_side="TCU")

    @L2
    def test_mt_call_reject(self, sim_object, rat):
        try:
            alm_id = {
                object_path_ril_0: {"2G": "63327", "3G": "63331","4G_PREF": "63335"},
                object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: MT call Reject without Answer on {}".format(rat))

        call_object = mt_call_to_tcu(TCU_Number, id1, sim_object)
        if API_OVER_DBUS:
            call_removed = signal_call_async(busname_ofono, sim_object, interface_VoiceCallManager, 'CallRemoved', 6)
            dbus_function_verification(busname_ofono, call_object, interface_VoiceCall, 'Hangup', None, None)
            assert get_async_result(call_removed, timeout=10) is not None, "CallRemoved broadcast is not received"
        else:
            call_removed = VoiceCallManager.CallRemoved(80)
            VoiceCall.Hangup(call_object)
            get_broadcast_responses(call_removed)
        time.sleep(1)
        end_call(id1)

    @L2
    def test_mt_call_hangup(self, sim_object, rat):
        try:
            alm_id = {object_path_ril_0: {"2G": "","3G": "","4G_PREF": "",},
                      object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: Make a call from Mobile to TCU and hangup on {}".format(sim_object))
        mt_call_answer_and_hangup(sim_object, TCU_Number, id1, hangup_side="TCU")

    @L1
    def test_mt_sms_default_rat(self, sim_object):
        try:
            alm_id = {object_path_ril_0: "63014",
                      object_path_ril_1: ""}
            allure_test_link(alm_id[sim_object])
        except:
            logger.error("Exception in fetching ALM Id")
            allure_test_link("NA: send SMS from Mobile to TCU on default RAT ril -- {}".format(sim_object))
        send_sms_to_tcu(TCU_Number, id1, ril_object=sim_object)

    @stability
    @L2
    def test_mt_sms(self, sim_object, rat):
        try:
            alm_id = {object_path_ril_0: {"2G": "63199", "3G": "63201","4G_PREF": "63200",},
                      object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.debug("Exception in fetching ALM Id")
            allure_test_link("NA: send SMS from Mobile to TCU on {}".format(rat))
        send_sms_to_tcu(TCU_Number, id1, ril_object=sim_object)

    @L2
    def test_activate_data_on_default_rat(self):
        try:
            alm_id = {
                object_path_ril_0: "63206",
                object_path_ril_1: ""}
            allure_test_link(alm_id[sim_object])
        except:
            logger.debug("Exception in fetching ALM Id")
            allure_test_link("NA: Activate Data connection on default RAT {}".format(sim_object))
        interface = data_turn_on(ril_object=sim_object)["Interface"]
        assert interface is not None
        ping_test('8.8.8.8', interface, 10)

    @L2
    def test_activate_data_connection(self, rat, sim_object):
        try:
            alm_id = {
                object_path_ril_0: {"2G": "63207", "3G": "63208","4G_PREF": "63209"},
                object_path_ril_1: {}}
            allure_test_link(alm_id[sim_object][rat])
        except:
            logger.debug("Exception in fetching ALM Id")
            allure_test_link("NA: Activate Data connection on {}".format(rat))

        interface = data_turn_on(ril_object=sim_object)["Interface"]
        assert interface is not None
        ping_test('8.8.8.8', interface, 10)

    @pytest.fixture(scope="function", autouse=True)
    def clear_calls(self,request,sim_object):
        def clear_calls_t():
            logger.debug("teardown method to perform cleanup")
            if current_call_status(sim_object):
                if API_OVER_DBUS:
                    dbus_function_verification(busname_ofono, sim_object, interface_VoiceCallManager, 'HangupAll', None,None)
                else:
                    VoiceCallManager.HangupAll()
            end_call(id1)  # TODO this one is just a temp fix. need to check why adb hang some time.
        request.addfinalizer(clear_calls_t)

