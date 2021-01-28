import allure
from concurrent.futures._base import TimeoutError
from interface.SSH.SSHInterface import execute_command_and_return_console_output,\
    execute_command_and_return_value,status_service_systemctl_in_loop,\
    execute_command_on_active_shell_and_return_console_output,close_shell
from interface.android_phone.android_interface import *
from interface.utils import TCU_IP
from config import *
import time
from interface.dbus.Dbus_interface import dbus_function_verification, \
    signal_call_async, get_async_result, ThreadPool

API_OVER_DBUS = False

logger.debug("API_OVER_DBUS value is {}".format(API_OVER_DBUS))
if not API_OVER_DBUS:
    from gta_release.tmbu.services.telephony import Modem,SimManager,NetworkRegistration,RadioSettings,\
        VoiceCallManager,VoiceCall,MessageManager,ConnectionContext,ConnectionManager
    from gta_release.generic_libs.interfaces.ssh_connection import update_tcu_details
    from gta_release.tmbu.grpc_service_binding import get_broadcast_responses
    update_tcu_details(TCU_IP, 22, 'root')

# <editor-fold desc="Section for defining bus name, Object path and interfaces">
busname_ofono = 'org.ofono'
object_path = '/'
object_path_ril_0 = '/ril_0'
object_path_ril_1 = '/ril_1'
interface_NetworkRegistration = 'org.ofono.NetworkRegistration'
interface_SimManager = 'org.ofono.SimManager'
interface_Modem = 'org.ofono.Modem'
interface_Manager = 'org.ofono.Manager'
interface_MessageManager = 'org.ofono.MessageManager'
interface_VoiceCallManager = 'org.ofono.VoiceCallManager'
interface_ConnectionContext = 'org.ofono.ConnectionContext'
interface_SupplementaryServices = 'org.ofono.SupplementaryServices'
interface_ConnectionManager = 'org.ofono.ConnectionManager'
interface_CallSettings = 'org.ofono.CallSettings'
interface_CallForwarding = 'org.ofono.CallForwarding'
interface_VoiceCall = 'org.ofono.VoiceCall'
interface_LongTermEvolution ='org.ofono.LongTermEvolution'
interfaces_IpMultimediaSystem = 'org.ofono.IpMultimediaSystem'
interface_RadioSettings = 'org.ofono.RadioSettings'
# </editor-fold>

# <editor-fold desc="Constant declaration used in the script">
Operator_name = config.get('SIM_Operator','Name')
internet_APN = config.get(Operator_name, 'Internet_APN')
DEFAULT_APN = config.get(Operator_name, 'DefaultAccessPointName')
mms_APN = config.get(Operator_name, 'MMS_APN')
RAT_exynos = {object_path_ril_0:{"2G": "radiooptions_exynos 18 1 0","3G": "radiooptions_exynos 18 2 0","4G": "radiooptions_exynos 18 11 0","4G_PREF": "radiooptions_exynos 18 10 0"},
       object_path_ril_1:{"2G": "radiooptions_exynos 18 1 1","3G": "radiooptions_exynos 18 2 1","4G": "radiooptions_exynos 18 11 1","4G_PREF": "radiooptions_exynos 18 10 1"}}
RAT_Name = {"2G": ['gsm','edge'], "3G": ['umts','hspa'],"4G": ['lte'],"4G_PREF": ['lte','umts','hspa','gsm','edge'],"NO_CHANGE": ['lte','umts','hspa','gsm','edge']}
RAT = {"2G": "gsm","3G": "umts","4G": "lte","4G_PREF": "any"}
# </editor-fold>

# <editor-fold des="Hard coded values used in the Telephony Test execution">
WAIT_TIME_CALL_CONNECT = 30
RAT_SWITCH_TIME = 20
# </editor-fold>

@allure.step('Checking status of NADs')
def nad_status(sim_object=object_path_ril_0):
    """
    Get the Modem online status
    Args:
        sim_object: ril object ril_0 or ril_1

    Returns: Bool

    """
    if API_OVER_DBUS:
        modem_property = dbus_function_verification(busname_ofono, sim_object, interface_Modem, 'GetProperties', None, None)['Online']
    else:
        modem_property = Modem.GetProperties()['Online'].boolValue
        if modem_property == 'true':
            modem_property = True
    logger.debug("Modem online status is -- {}".format(modem_property))
    return modem_property


@allure.step('Checking "{ril_object}" and Network status')
def sim_status(ril_object=object_path_ril_0):
    """
    Get the SIM card and registration status
    Args:
        ril_object: ril object can be ril_0 or ril_1

    Returns: list [bool<sim present>,network_status,network_technology]

    """
    status = False
    network_status = False
    network_technology = False
    try:
        if API_OVER_DBUS:
            sim_property = dbus_function_verification(busname_ofono, ril_object,interface_SimManager, 'GetProperties', None, None)['Present']
        else:
            sim_property = SimManager.GetProperties()['Present'].isPresent
        if sim_property:
            status = True
            if API_OVER_DBUS:
                nr_property = dbus_function_verification(busname_ofono, ril_object, interface_NetworkRegistration,'GetProperties', None, None)
                network_status = nr_property['Status']
                if network_status != 'unregistered':
                    network_technology = nr_property['Technology']
            else:
                nr_property = NetworkRegistration.GetProperties()
                network_status = nr_property['Status'].stringvalue
                if network_status != 'unregistered':
                    network_technology = nr_property['Technology'].stringvalue
    except Exception as e:
        logger.debug("Exception in status -- {}".format(e))
    finally:
        return [status,network_status,network_technology]


@allure.step('Checking current RAT registered')
def current_rat(ril_object=object_path_ril_0):
    """
    Get current Network technology TCU is registered with.
    Args:
        ril_object: ril object can be ril_0 or ril_1

    Returns: Technology registered

    """
    if API_OVER_DBUS:
        network_property = dbus_function_verification(busname_ofono, ril_object, interface_NetworkRegistration,'GetProperties', None, None)['Technology']
    else:
        network_property = NetworkRegistration.GetProperties()['Technology'].stringvalue
    return network_property


@allure.step('Switching RAT "{rat}" for "{ril_object}"')
def switch_rat(ril_object, rat, switching_type="API"):
    """
    Switch TCU to a particular RAT
    Args:
        ril_object: ril_0 or ril_1
        rat: RAT technology for ex: 2G,3G,4G,4G_PREF
        switching_type: API if you want to switch using DBUS API exynos if you want using exynos cmd

    Returns: None

    """
    network_technology = current_rat(ril_object)
    if network_technology in RAT_Name[rat] and "PREF" not in rat and rat == "NO_CHANGE":
        logger.debug("RAT is already selected")
        return 0
    if switching_type == "API":
        if API_OVER_DBUS:
            dbus_function_verification(busname_ofono, ril_object, interface_RadioSettings, 'SetProperty', "'TechnologyPreference', Variant('s':'" + RAT[rat] + "')", None)
            time.sleep(2)
            dbus_function_verification(busname_ofono, ril_object, interface_RadioSettings, 'GetProperties', None, None)
        else:
            RadioSettings.SetProperty('TechnologyPreference',RAT[rat])
            time.sleep(2)
            logger.debug(RadioSettings.GetProperties())
    else:
        cmd = RAT_exynos[ril_object][rat]
        logger.debug("RAT switch command %s", cmd)
        command_status = execute_command_and_return_value(cmd)
        logger.debug("RAT switch command status :  %s",command_status)
        time.sleep(4)
    assert status_service_systemctl_in_loop('ofono',timeout=10),"ofono server is not running"
    wait_for_network_technology(rat,ril_object)


@allure.step('Making a call to "{number}" with "{ril_object}"')
def mo_call_from_tcu(number, ril_object=object_path_ril_0,call_status='alerting'):
    """
    Make a call from TCU to mobile, and wait for a particular call state
    Args:
        number: Mobile number to make a call
        ril_object: ril object to use ril_0 or ril_1
        call_status: call status to wait

    Returns:

    """
    if API_OVER_DBUS:
        call_added = signal_call_async(busname_ofono, ril_object, interface_VoiceCallManager, 'CallAdded', 6)
        voice_call_object = dbus_function_verification(busname_ofono, ril_object, interface_VoiceCallManager, 'Dial', str(number) + ",'default'", None)
        logger.debug("Voice call object path: %s", voice_call_object)
        assert get_async_result(call_added, timeout=10) is not None, "CallAdded broadcast is not received"
    else:
        call_added = VoiceCallManager.CallAdded(80)
        time.sleep(4)
        voice_call_object = VoiceCallManager.Dial(eval(number))
        assert get_broadcast_responses(call_added),"CallAdded broadcast is not received"

    assert wait_for_call_status(call_status, ril_object, WAIT_TIME_CALL_CONNECT), "call status not change to alerting"
    return voice_call_object


def mt_call_to_tcu(number,phone_adb_id,ril_object):
    """
    Make a call from TCU
    Args:
        number: Mobile number to make a call
        phone_adb_id: android adb id
        ril_object: ril object ril_0 and ril_1

    Returns: Call Object

    """
    if API_OVER_DBUS:
        call_added = signal_call_async(busname_ofono, ril_object, interface_VoiceCallManager, 'CallAdded', 8)
    else:
        call_added = VoiceCallManager.CallAdded(80)
    make_a_call_from_mobile(number,phone_adb_id)
    if API_OVER_DBUS:
        call_added_response = get_async_result(call_added, timeout=30)
        assert call_added_response is not None, "CallAdded broadcast is not received"
        call_object = call_added_response[4][0]
    else:
        call_added_response = get_broadcast_responses(call_added)
        logger.debug("Call added is -- {}".format(call_added_response))
        call_object = call_added_response[0].vcPath
    return call_object


@allure.step('Sending a SMS to "{number}" with "{ril_object}"')
def send_sms_from_tcu(number, msg="Hello Ofono", ril_object=object_path_ril_0):
    """
    Send SMS from TCU to the given mobile number
    Args:
        number: SIM card number SMS need to be send
        msg: message content to be send
        ril_object: ril object ril_0 or ril_1

    Returns: None

    """
    if API_OVER_DBUS:
        message_added = signal_call_async(busname_ofono, ril_object, interface_MessageManager, 'MessageAdded', 10)
        message_removed = signal_call_async(busname_ofono, ril_object, interface_MessageManager, 'MessageRemoved', 12)
        logger.info("Registered for broadcast MessageAdded and MessageRemoved")
        message_send = dbus_function_verification(busname_ofono, ril_object, interface_MessageManager, 'SendMessage', str(number) + ",'" + str(msg) + "'", None)
        logger.info("Message send from TCU -- {}".format(message_send))
        assert ril_object + '/message_' in message_send, "SMS is not send from TCU"
        message_added_result = get_async_result(message_added,timeout=10)
        logger.info("Response of message added -- {}".format(message_added_result))
        assert message_added_result is not None,"MessageAdded event is not received"
        message_removed_result = get_async_result(message_removed,timeout=40)
        logger.info("Response of message removed -- {}".format(message_removed_result))
        assert message_removed_result is not None, "MessageRemoved event is not received"
    else:
        message_added = MessageManager.MessageAdded(80)
        message_removed = MessageManager.MessageRemoved(80)
        message_send = MessageManager.SendMessage(eval(number),msg)
        logger.info("Message send from TCU -- {}".format(message_send))
        assert ril_object + '/message_' in message_send, "SMS is not send from TCU"
        get_broadcast_responses(message_added)
        get_broadcast_responses(message_removed)


def send_sms_to_tcu(number, phone_id,msg="Hello ofono from Mobile", ril_object=object_path_ril_0):
    """
    Send SMS from Mobile to TCU
    Args:
        number: TCU mobile number
        phone_id: Phone android ID
        msg: message to send
        ril_object: ril object to select ril_0 or ril_1

    Returns: None

    """
    if API_OVER_DBUS:
        incoming_msg = signal_call_async(busname_ofono, ril_object, interface_MessageManager, 'IncomingMessage', 8)
    else:
        incoming_msg = MessageManager.IncomingMessage(100)
    send_sms(number,msg,phone_id)
    if API_OVER_DBUS:
        assert get_async_result(incoming_msg,timeout=30) is not None,"IncomingMessage broadcast is not received"
    else:
        assert get_broadcast_responses(incoming_msg) is not [],"IncomingMessage broadcast is not received"


@allure.step('Getting Data Status SIM Object :-"{ril_object}" ')
def data_status(ril_object=object_path_ril_0,apn_type="internet"):
    """
    Get Data Connection Status
    Args:
        ril_object: ril object ril_0 or ril_1
        apn_type:

    Returns: dict with connection values

    """
    activated_context = {'APN': None, 'Active': None, 'Interface': None, 'Address': None, 'DomainNameServers': None}
    if API_OVER_DBUS:
        get_context = dbus_function_verification(busname_ofono, ril_object, interface_ConnectionManager, 'GetContexts', None, None)
        logger.debug(get_context)
        for context in get_context:
            if context[1]['Type'] == apn_type and len(context[1]["AccessPointName"]) > 0:
                activated_context['APN'] = context[1]["AccessPointName"]
                activated_context['Active'] = context[1]["Active"]
                if activated_context['Active']:
                    activated_context["Interface"] = context[1]["Settings"]["Interface"]
                    activated_context['Address'] = context[1]["Settings"]["Address"]
                    activated_context['DomainNameServers'] = [item for item in context[1]["Settings"]["DomainNameServers"]]               
    else:        
        get_context = ConnectionManager.GetContexts()
        for context in get_context:
            if context.contextValues['Type'].stringvalue == apn_type and len(context.contextValues["AccessPointName"].stringvalue) > 0:
                activated_context['APN'] = context.contextValues["AccessPointName"].stringvalue
                activated_context['Active'] = context.contextValues["Active"].isPresent                
                if context.contextValues['Active'].isPresent:
                    activated_context['Interface'] = context.contextValues["Settings"].settingsPropertyList["Interface"].stringvalue
                    activated_context['Address'] = context.contextValues["Settings"].settingsPropertyList["Address"].stringvalue
                    activated_context['DomainNameServers'] = [item for item in context.contextValues["Settings"].settingsPropertyList["DomainNameServers"].stringvalue]

    logger.debug("Data Status: {}".format(activated_context))
    return activated_context

@allure.step('Turing ON the {apn_type} data with APN:-"{apn}" ')
def data_turn_on(apn=internet_APN, ril_object=object_path_ril_0, apn_type='internet'):
    """
    API is developed for Turn on the data connection with internet type,
    apn name is the optional parameter which can be pass to the function if required
    Args:
        apn: (Optional parameter) Which APN need to be to activate the internet connection
        ril_object: ril_0 or ril_1 to activate the data
        apn_type: Type of apn need to be created

    Returns: context dict value

    """
    activated_context = {'Interface': None, 'Address': None, 'DomainNameServers': None}
    if API_OVER_DBUS:
        get_context = dbus_function_verification(busname_ofono, ril_object, interface_ConnectionManager, 'GetContexts', None, None)
        logger.debug(get_context)

        for item in get_context:
            if item[1]['Type'] == apn_type:
                if not item[1]['Active']:
                    logger.info("APN type already present")
                    if item[1]['AccessPointName'] != "'" + apn + "'":
                        dbus_function_verification(busname_ofono, item[0], interface_ConnectionContext, 'SetProperty',"'AccessPointName', Variant('s':'" + apn + "')", None)
                        time.sleep(5)
                    dbus_function_verification(busname_ofono, item[0], interface_ConnectionContext, 'SetProperty',"'Active', Variant('b':True)",None)
                    context = dbus_function_verification(busname_ofono, item[0], interface_ConnectionContext, 'GetProperties', None,None)
                    logger.info("Created context is -- {}".format(context))
                    if len(context) > 0:
                        if context['Active']:
                            activated_context['Interface'] = context["Settings"]["Interface"]
                            activated_context['Address'] = context["Settings"]["Address"]
                            activated_context['DomainNameServers'] = context["Settings"]["DomainNameServers"]
                else:
                    logger.info("Data is already active with internet APN type")
                    activated_context["Interface"] = item[1]["Settings"]["Interface"]
                    activated_context['Address'] = item[1]["Settings"]["Address"]
                    activated_context['DomainNameServers'] = [item for item in item[1]["Settings"]["DomainNameServers"]]
        return activated_context
    else:
        get_context = ConnectionManager.GetContexts()
        logger.debug("current context list is -- {}".format(get_context))
        for item in get_context:
            logger.debug("ITEM is -- {}".format(item))
            if item.contextValues['Type'].stringvalue == apn_type:
                if not item.contextValues['Active'].isPresent:
                    logger.info("APN type already present")
                    if item.contextValues['AccessPointName'].stringvalue != "'" + apn + "'":
                        ConnectionContext.SetProperty(item.contextPath,'AccessPointName',apn)
                        time.sleep(5)
                    ConnectionContext.SetProperty(item.contextPath,'Active',True)
                    context = ConnectionContext.GetProperties(item.contextPath)
                    logger.info("Created context is -- {}".format(context))
                    if len(context) > 0:
                        if context['Active'].isPresent:
                            activated_context['Interface'] = context["Settings"].settingsPropertyList["Interface"].stringvalue
                            activated_context['Address'] = context["Settings"].settingsPropertyList["Address"].stringvalue
                            activated_context['DomainNameServers'] = context["Settings"].settingsPropertyList["DomainNameServers"].stringvalue
                else:
                    logger.info("Data is already active with internet APN type")
                    activated_context["Interface"] = item.contextValues["Settings"].settingsPropertyList["Interface"].stringvalue
                    activated_context['Address'] = item.contextValues["Settings"].settingsPropertyList["Address"].stringvalue
                    activated_context['DomainNameServers'] = [item for item in item.contextValues["Settings"].settingsPropertyList["DomainNameServers"].stringvalue]
        return activated_context




@allure.step('Turing OFF the Internet data')
def data_turn_off(apn_type='internet',ril_object=object_path_ril_0):
    """
    Turn off the data with particular apn type
    Args:
        apn_type: type of APN need to de-activate
        ril_object: ril object ril_0 or ril_1

    Returns: bool

    """
    get_context = dbus_function_verification(busname_ofono, ril_object, interface_ConnectionManager, 'GetContexts', None,None)
    logger.debug("current context is -- {}".format(get_context))
    for item in get_context:
        if item[1]['Type'] == apn_type:
            if not item[1]['Active']:
                logger.debug("Data with {} type is already disable".format(apn_type))
                return True
            else:
                dbus_function_verification(busname_ofono, item[0], interface_ConnectionContext, 'SetProperty',"'Active', Variant('b':False)",None)
                return True
    return False

def get_modem_version():
    """
    API can be used to find the modem version
    Returns: modem_version

    """
    # modem_version = ""
    try:
        get_modems = dbus_function_verification(busname_ofono, object_path, interface_Manager, 'GetModems',None,None)
        logger.debug(get_modems[0][1]['Revision'])
        modem_version = get_modems[0][1]['Revision']
    except Exception as e:
        logger.debug("Exception while collecting the modem information through dbus %s",str(e))
        cmd = "/usr/bin/at-client {} 225 AT+CGMR".format(TCU_IP)
        cmd_output = execute_command_on_active_shell_and_return_console_output(cmd,timeout=10)
        modem_version = cmd_output.split('\n')[5]
        logger.debug(modem_version)
        pass
    return modem_version


@allure.step('get "{ril_object}" modem status by AT')
def get_modem_status_by_at(ril_object, timeout=20):
    """
    Get the modem status by running AT command
    Args:
        ril_object: ril object ril_0 or ril_1
        timeout: max time to wait for modem to come online

    Returns: None

    """
    modem_status = nad_status(ril_object)
    if modem_status is True:
        logger.info("RIL modem for {} is online no need to check the AT status".format(ril_object))
        return True
    start_time = time.time()
    at_status = False
    if ril_object == object_path_ril_0:
        at_port = 225
    else:
        at_port = 226
    close_shell()
    while start_time + timeout > time.time() and not at_status:
        cmd = "/usr/bin/at-client {} {} AT ".format(TCU_IP,at_port)
        cmd_output = execute_command_on_active_shell_and_return_console_output(cmd, timeout=10)
        execute_command_on_active_shell_and_return_console_output("\x03", timeout=5)
        logger.info("AT command status is %s",cmd_output)
        if "ok" in cmd_output.lower():
            at_status = True
        # close_shell()
    assert at_status,"SIM : {} , AT status is not OK after {} sec of wait ".format(ril_object, timeout)
    return at_status

def mo_call_answer_and_hangup(ril_object, number, phone_adb_id, call_duration=2,hangup_side="mobile",rat="Any"):
    """
    Make a call from TCU and answer in mobile and hangup from mobile/TCU
    Args:
        ril_object: ril object ril_0 or ril_1
        number: Mobile number to make a call
        phone_adb_id: android adb phone id
        call_duration: How long you need to make your call in active state
        hangup_side: hangup call from Mobile or TCU side
        rat: Call on particular RAT

    Returns: None

    """
    if rat != "Any":
        switch_rat(ril_object, rat)
    voice_call_object = mo_call_from_tcu(number,ril_object)
    accept_call(phone_adb_id)
    if API_OVER_DBUS:
        call_removed = signal_call_async(busname_ofono, ril_object, interface_VoiceCallManager, 'CallRemoved', 6)
    else:
        call_removed = VoiceCallManager.CallRemoved(70)
    time.sleep(call_duration)
    if hangup_side =="mobile":
        end_call(phone_adb_id)
    else:
        if API_OVER_DBUS:
            dbus_function_verification(busname_ofono, voice_call_object, interface_VoiceCall, 'Hangup', None, None)
        else:
            VoiceCall.Hangup(voice_call_object)
    if API_OVER_DBUS:
        assert get_async_result(call_removed, timeout=10) is not None, "CallRemoved broadcast is not received"
    else:
        assert get_broadcast_responses(call_removed) is not [], "CallRemoved broadcast is not received"


def mt_call_answer_and_hangup(ril_object, number, phone_adb_id, call_duration=2,hangup_side="mobile",rat="Any"):
    """
    make a call from Mobile to TCU
    Args:
        ril_object: Which ril object ril_0 or ril_1
        number: Mobile number to be made a call
        phone_adb_id: android phone id
        call_duration: call duration to keep the call in active state
        hangup_side: hangup call from Mobile or TCU
        rat: Any particular RAT to switch before make a call

    Returns: None

    """
    if rat != "Any":
        switch_rat(ril_object, rat)
    call_object = mt_call_to_tcu(number,phone_adb_id,ril_object)
    logger.info("Call object is -- {}".format(call_object))
    if API_OVER_DBUS:
        dbus_function_verification(busname_ofono, call_object, interface_VoiceCall, 'Answer', None, None)
    else:
        VoiceCall.Answer(call_object)
    logger.debug("Call status is -- {}".format(current_call_status(ril_object)))
    time.sleep(call_duration)
    if API_OVER_DBUS:
        call_removed = signal_call_async(busname_ofono, ril_object, interface_VoiceCallManager, 'CallRemoved', 6)
    else:
        call_removed = VoiceCallManager.CallRemoved(70)
    if hangup_side =="mobile":
        end_call(phone_adb_id)
    else:
        if API_OVER_DBUS:
            dbus_function_verification(busname_ofono, call_object, interface_VoiceCall, 'Hangup', None, None)
        else:
            VoiceCall.Hangup(call_object)
    if API_OVER_DBUS:
        assert get_async_result(call_removed, timeout=10) is not None, "CallRemoved broadcast is not received"
    else:
        assert get_broadcast_responses(call_removed) is not [], "CallRemoved broadcast is not received"

def check_network(ril_object, technology, timeout=10):
    """
    Monitor the network for given amount of time
    Args:
        ril_object: ril object to monitor ril_0 or ril_1
        technology: expected network technology like lte
        timeout: max time to monitor

    Returns: None

    """
    for i in range(0,timeout):
        assert technology == current_rat(ril_object),"network technology is switched from {}".format(technology)
        time.sleep(1)

def check_network_async(ril_object, technology, timeout=10):
    """
    Monitor Network technology without blocking the main process(Async)
    Args:
        ril_object: ril object ril_0 or ril_1
        technology: Expected network technology
        timeout: time to monitor the network

    Returns: list of Async objects

    """
    pool = ThreadPool()
    future = pool.schedule(check_network, args=[ril_object, technology, timeout])
    return [future,pool]

def check_network_async_result(async_object,timeout=2):
    """
    Check results from check_network_async function
    Args:
        async_object: object return by check_network_async
        timeout: time to wait for the result

    Returns: None

    """
    response = None
    try:
        logger.debug("Event subscription function status -- {}".format(async_object[0].running()))
        response = async_object[0].result(timeout=timeout)
        logger.info("Response is --{}".format(response))
    except TimeoutError as e:
        logger.debug("Ignore TimeoutError Exception is -- {}".format(e.__class__))
    finally:
        async_object[0].cancel()
        async_object[1].stop()
    return response


def wait_for_call_status(status, ril_object, timeout=30):
    """
    Wait for particular call state to come
    Args:
        status: expected call status
        ril_object: ril to monitor ril_0 or ril_1
        timeout: max time to wait

    Returns: Bool

    """
    logger.debug("Waiting for call %s status in %s", status, ril_object)
    time.sleep(2)
    for i in range(0, timeout):
        try:
            if current_call_status(ril_object) == status:
                return True
            time.sleep(1)
            # if API_OVER_DBUS:
            #     get_calls = dbus_function_verification(busname_ofono, ril_object, interface_VoiceCallManager, 'GetCalls', None)
            #     nr_property = dbus_function_verification(busname_ofono, ril_object, interface_NetworkRegistration, 'GetProperties', None)
            #     logger.info("last call status is {}, Device is registered on {} registration status: {}".format(get_calls[-1][1]['State'], nr_property['Technology'],nr_property['Status']))
            # else:
            #     get_calls = VoiceCallManager.GetCalls()
            # if len(get_calls) > 0:
            #     if get_calls[-1][1]['State'] == status:
            #         return True
        except Exception as e:
            logger.debug("call state removed without changing to {} Exception was {}".format(status,e))
            return False
    return False


def current_call_status(ril_object=object_path_ril_0):
    """
    Get the last call status
    Args:
        ril_object: ril object ril_0 or ril_1

    Returns: call status

    """
    if API_OVER_DBUS:
        get_calls = dbus_function_verification(busname_ofono, ril_object, interface_VoiceCallManager, 'GetCalls', None)
    else:
        get_calls = VoiceCallManager.GetCalls()
        logger.debug("Get call list is {}".format(get_calls))

    if len(get_calls) > 0:
        if API_OVER_DBUS:
            call_status = get_calls[len(get_calls) - 1][1]['State']
        else:
            call_status = get_calls[-1].VCProperties['State'].stringvalue
        return call_status
    logger.debug("NO Active calls")
    return False


def modem_restart(ril_object):
    """
    modem restart make modem ONLINE/OFFLINE
    Args:
        ril_object: ril object ril_0 or ril_1

    Returns: None

    """
    if API_OVER_DBUS:
        dbus_function_verification(busname_ofono, ril_object, interface_Modem, 'SetProperty', "'Powered', Variant('b':False)", None)
        time.sleep(1)
        dbus_function_verification(busname_ofono, ril_object, interface_Modem, 'SetProperty', "'Powered', Variant('b':True)", None)
        time.sleep(1)
        dbus_function_verification(busname_ofono, ril_object, interface_Modem, 'SetProperty', "'Online', Variant('b':False)", None)
        time.sleep(1)
        dbus_function_verification(busname_ofono, ril_object, interface_Modem, 'SetProperty', "'Online', Variant('b':True)", None)
    else:
        Modem.SetProperty('Powered', False)
        time.sleep(1)
        Modem.SetProperty('Powered', True)
        time.sleep(1)
        Modem.SetProperty('Online', False)
        time.sleep(1)
        Modem.SetProperty('Online', True)


def modem_restart_if_not_online(ril_object):
    """
    Restart the modem if NAD is not online
    Args:
        ril_object: ril object path ril_0 or ril_1

    Returns: None

    """
    if not nad_status(ril_object):
        time.sleep(8)
        modem_restart(ril_object)


def wait_for_registration(ril_object, status_list, timeout=20):
    """
    wait for the Network registration state
    Args:
        ril_object: ril object ril_0 or ril_1
        status_list: list of expected registration states
        timeout: max time to wait for status change

    Returns: bool

    """
    for i in range(0, timeout):
        try:
            nr_status = sim_status()[1]
            if nr_status in status_list:
                return True
            elif nr_status == 'denied':
                logger.debug("Current network status is 'denied' return from this function")
                return False
            time.sleep(1)
        except Exception as e:
            logger.debug("Exception : {} in Network registration GetProperties for RIL : {}".format(e, ril_object))
    logger.info("network is not register for SIM {}".format(ril_object))
    return False


def wait_for_network_technology(rat,ril_object=object_path_ril_0,timeout=RAT_SWITCH_TIME):
    """
    wait for network switch to a particular rat (handover)
    Args:
        rat: RAT to switch
        ril_object: ril object ril_0 or ril_1
        timeout: max time to wait for switching

    Returns:

    """
    for i in range(0, timeout):
        nr_property = sim_status(ril_object)
        if (nr_property[1] == 'registered' or nr_property[1] == 'roaming') and (nr_property[2] in RAT_Name[rat]):
            logger.info("Network switch completed")
            break
        time.sleep(2)
    assert nr_property[1] == 'registered' or nr_property[1] == 'roaming', \
        "switching failed to : {} and current Network status is : {}".format(rat,nr_property[1])
    logger.info("Network technology is %s", nr_property[2])
    assert nr_property[2] in RAT_Name[rat], \
        "switching failed to : {} current network Technology is : {} and Network status is : {}".format(rat,nr_property[2],nr_property[1])


def ping_statics(ping_out):
    """
    Analyze the ping output
    Args:
        ping_out: raw output of ping

    Returns: dict with ping statics

    """
    result = dict()
    for line in ping_out.split('\n'):
        if "packets" in line:
            data = line.split(',')
            result["transmitted"] =  int(re.sub('[^ 0-9]', '', data[0]))
            result["received"] = int(re.sub('[^ 0-9]', '', data[1]))
            result["loss"] = int(re.sub('[^ 0-9]', '', data[2]))
    return result

@allure.step('Verify TCU is able to ping IP: "{ip}" with Interface: "{interface}"')
def ping_test(ip,interface,count):
    """
    ping with given interface
    Args:
        ip: IP address to ping
        interface: Interface to use in ping
        count: number of packet to send

    Returns: None

    """
    ping_command = 'ping -I {} -c {} {} '.format(interface,count,ip)
    data = execute_command_and_return_console_output(ping_command, timeout=count*2)
    logger.debug("Ping Statics is \n {}".format(data))
    assert "{} packets received".format(count) in data, "Data loss when trying to ping from TCU --> {}".format(
        ping_statics(data))

def ims_register(ril_object):
    """
    Register to IMS
    Args:
        ril_object: ril object ril_0 or ril_1

    Returns: None

    """
    switch_rat(ril_object, "4G")
    for i in range(0, 5):
        modem_property = dbus_function_verification(busname_ofono, ril_object, interface_Modem, 'GetProperties', None,
                                                    None)
        if interfaces_IpMultimediaSystem in modem_property['Interfaces']:
            break
        time.sleep(0.5)
    assert interfaces_IpMultimediaSystem in modem_property['Interfaces'], "IMS interface is not up"
    ims_property = dbus_function_verification(busname_ofono, ril_object, interfaces_IpMultimediaSystem, 'GetProperties',
                                              None, None)
    if not ims_property["Registered"]:
        dbus_function_verification(busname_ofono, ril_object, interfaces_IpMultimediaSystem, 'Register', None, None)
        for i in range(0, 5):
            ims_property = dbus_function_verification(busname_ofono, ril_object, interfaces_IpMultimediaSystem,
                                                      'GetProperties', None, None)
            logger.debug("IMS property is -- {}".format(ims_property))
            if ims_property["Registered"]:
                break
            time.sleep(0.5)
        assert ims_property["Registered"], "IMS registration is unsuccessful"

def ims_unregister(ril_object):
    """
    Un-Register from IMS
    Args:
        ril_object: ril object ril_0 or ril_1

    Returns: None

    """
    ims_property = dbus_function_verification(busname_ofono, ril_object, interfaces_IpMultimediaSystem,
                                              'GetProperties', None, None)
    if not ims_property["Registered"]:
        dbus_function_verification(busname_ofono, sim_status, interfaces_IpMultimediaSystem, 'Unregister', None,
                                   None)
        for i in range(0, 5):
            ims_property = dbus_function_verification(busname_ofono, ril_object, interfaces_IpMultimediaSystem,
                                                      'GetProperties', None, None)
            if not ims_property["Registered"]:
                break
            time.sleep(0.5)
    assert not ims_property["Registered"], "IMS Unregister Failed on ril {}".format(ril_object)


if __name__== "__main__":
    print(data_turn_on())
