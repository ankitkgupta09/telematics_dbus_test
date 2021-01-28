"""
Diagnostics helper functions
"""
from doip_client.doip import AddressEnum,send_command_and_get_response,connect_uds_server
import allure
from interface.AllureReport.AllureInterface import allure_test_link
from utility.SoftwareUpdate.SoftwareUpdateUtility import get_software_part_number
from interface.utils import assertion,connection_wait_in_loop,TCU_IP
from time import sleep
from config import interfaces,logger,ETH_CONNECTION_TIMEOUT

SOCKET_ADDRESS = interfaces.get('DOIP', 'SOCKET_ADDRESS')

WAIT_FOR_UDS = ['11 01','10 02','10 01','11 81','10 82']
WAIT_FOR_ETH_DURING_UDS = ETH_CONNECTION_TIMEOUT

# <editor-fold desc="STEPS">
incorrect_DLC_SID_10 = ('10 81 01', '7F 10 13'),('10 82 01', '7F 10 13'),('10 83 00', '7F 10 13'),('10', '7F 10 13'),
incorrect_sub_function_SID_10 = ('10 00','7F 10 12'),('10 04','7F 10 12'),('10 7F','7F 10 12'),('10 84','7F 10 12'),('10 FF','7F 10 12'),
Enter_into_default_session_sub_function_10_01 = SID_10_01 = ('10 01','50 01 00 32 01 F4'),
SID_10_01_no_response = ('10 01', None),
Enter_default_session_with_incorrect_DLC_correct_sub_function = SID_10_01_81 = ('10 01 81', '7F 10 13'),
Enter_default_session_with_correct_DLC_incorrect_sub_function = SID_10_04 = ('10 04', '7F 10 12'),
Enter_programing_session_with_incorrect_DLC_correct_sub_function = SID_10_02_82 = ('10 02 82', '7F 10 13'),
# Enter_programing_session_with_correct_DLC_incorrect_sub_function = SID_10_04 = ('10 04','7F 10 12') ,
# P2 Server Timer value need to be updated to 00 32 later
Enter_into_programing_session_sub_function_10_02 = SID_10_02 = ('10 02', '50 02 00 28 01 F4'),
SID_10_02_no_response = ('10 02', None),
Enter_into_extended_session_sub_function_10_03 = SID_10_03 = ('10 03', '50 03 00 32 01 F4'),
SID_10_03_no_response = ('10 03', None),
Enter_into_extended_session_sub_function_10_03_negative = SID_10_03_negative = ('10 03', '7F 10 22'),
Enter_into_default_session_sub_function_10_81 = SID_10_81 = ('10 81', None),
Enter_into_programing_session_sub_function_10_82 = SID_10_82 = ('10 82', None),
Enter_extended_session_with_incorrect_DLC_correct_sub_function = SID_10_03_83 = ('10 03 83', '7F 10 13'),
Enter_into_extended_session_sub_function_10_83 = SID_10_83 = ('10 83', None),
check_default_session = ('22 F1 86', '62 F1 86 01'),
check_programming_session = ('22 F1 86', '62 F1 86 02'),
check_extended_session = ('22 F1 86', '62 F1 86 03'),
current_session_negative = ('22 F1 86', '7F 23 11'),
current_session_no_response= ('22 F1 86', None),
SID_10_83_negative = ('10 83','7F 10 22'),

# <editor-fold desc="Tester Present">
Tester_present = ('3E 80',None),
Tester_present_00 = ('3E 00','7E 00'),
Tester_present_00_No_Response = ('3E 00', None),
incorrect_DLC_0x3E_NRC_13 = ('3E 00 00','7F 3E 13'),('3E 80 00','7F 3E 13'),('3E','7F 3E 13'),
Tester_present_incorrect_sub_function_NRC_12 = ('3E 02','7F 3E 12'),('3E 82','7F 3E 12'),('3E 7F','7F 3E 12'),('3E FF','7F 3E 12'),
Tester_present_incorrect_service_ID = ('E3 00','7F E3 11'),('E3 80','7F E3 11'),
# </editor-fold desc">

read_part_number_20 = ('22 F1 20', '62 F1 20 32 33 40 68 20 41 43'),
read_part_number_21 = ('22 F1 21', '62 F1 21 32 31 99 46 20 41 43'),
read_part_number_21_negative = ('22 F1 21', '7F 22 31'),
read_part_number_25 = ('22 F1 25', '62 F1 25 '+get_software_part_number("SWBP")),
read_part_number_25_negative = ('22 F1 25', '7F 22 31'),
read_part_number_20_NRC_31 = ('22 F1 20', '7F 22 31'),
read_ECU_core_assembly_part = ('22 F1 2A', '62 F1 2A 50 99 07 61 20 41 41'),
read_sw_part_number = ('22 F1 2E', '62 F1 2E 03 ' + get_software_part_number("SWLM") + ' ' + get_software_part_number("SWL2") + ' ' + get_software_part_number("SWP1")),
read_sw_part_number_NRC_31 = ('22 F1 2E', '7F 22 31'),
read_part_number_1C =('22 D0 1C','7F 22 31'),
read_public_key_checksum_send_diag_request = ('22 D0 1C','62 D0 1C 55 00 00 00 01 00 00 00 00 00 00 00 00 61 E1 22 E3 03 F1 08 00 00 00 00 00 00 00 00 00 00 00 00'),

# <editor-fold desc="Read 0xD01C">
incorrect_DLC_and_correct_DID_C1 = ('22 D0 1C C1','7F 22 13'),
incorrect_DLC_and_correct_DID_D0 = ('22 D0','7F 22 13'),
incorrect_DLC_and_correct_DID_31 = ('22 D0 C1','7F 22 31'),
incorrect_SID = ('62 D0 1C','7F 62 11'),
# </editor-fold">

incorrect_service_but_correct_DLC_and_DID_20 = ('23 F1 20','7F 23 11'),
incorrect_service_but_correct_DLC_and_DID_2A = ('23 F1 2A','7F 23 11'),
incorrect_service_but_correct_DLC_and_DID_2E = ('23 F1 2E','7F 23 11'),
incorrect_service_but_correct_DLC_and_DID_25 = ('23 F1 25','7F 23 11'),
incorrect_service_but_correct_DLC_and_DID_86 = ('23 F1 86','7F 23 11'),
incorrect_service_but_correct_DLC_and_DID_21 = DID_62_F1_21 = ('62 F1 21','7F 62 11'),

# <editor-fold desc="Complete & Compatible Routine">
RID_0205 = ('31 01 02 05','71 01 02 05 10 00 00 00 00'),
RID_0205_No_Response = ('31 01 02 05', None),
RID_0205_NRC_31 = ('31 01 02 05','7F 31 31'),
RID_0205_NRC_33 = ('31 01 02 05','7F 31 33'),
RID_0205_NRC_13 = ('31 01 02','7F 31 13'),
incorrect_sub_function_RID_0205 = ('31 00 02 05','7F 31 12'),('31 04 02 05','7F 31 12'),('31 7F 02 05','7F 31 12'),('31 FF 02 05','7F 31 12'),
RID_0205_NRC_11 = ('51 01 02 05','7F 51 11'),
incorrect_RID_NRC_31 = ('31 01 03 01','7F 31 31'),
RID_0205_Status = ('31 03 02 05','71 03 02 05 10 00 00 00 00'),
# </editor-fold>

# <editor-fold desc="Programming Pre-Condition Check Routine">
RID_0206_True = ('31 01 02 06','71 01 02 06 10 01'),
RID_0206_False = ('31 01 02 06','71 01 02 06 10 02'),
RID_0206_NRC_31 = ('31 01 02 06','7F 31 31'),
RID_0206_No_Response = ('31 01 02 06', None),
RID_0206_NRC_13 = ('31 01 02','7F 31 13'),
incorrect_sub_function_RID_0206 = ('31 00 02 06', '7F 31 12'), ('31 04 02 06', '7F 31 12'), ('31 7F 02 06', '7F 31 12'), ('31 FF 02 06', '7F 31 12'),
RID_0206_NRC_11 = ('61 01 02 06','7F 61 11'),
RID_0206_Status = ('31 03 02 06','71 03 02 06 10 01'),
# </editor-fold>

# <editor-fold desc="Check Memory Routine">
RID_0212 = ('31 01 02 12', '71 01 02 12 10 06'),
RID_0212_No_Response = ('31 01 02 12', None),
RID_0212_NRC_31 = ('31 01 02 12', '7F 31 31'),
RID_0212_NRC_13 = ('31 01 02', '7F 31 13'),
incorrect_sub_function_RID_0212 = ('31 00 02 12', '7F 31 12'), ('31 04 02 12', '7F 31 12'), ('31 7F 02 12', '7F 31 12'), ('31 FF 02 12', '7F 31 12'),
RID_0212_NRC_11 = ('61 01 02 12','7F 61 11'),
RID_0212_NRC_33 = ('31 01 02 12','7F 31 33'),
RID_0212_Status = ('31 03 02 12', '71 03 02 12 10 06'),
# </editor-fold>

# <editor-fold desc="Security Service">
SID_27_01 = ('27 01','67 01 FF FF FF FF FF'),
SID_27_01_No_response = ('27 01', None),
calculated_key = ('27 02 FF FF FF','67 02'),
calculated_key_No_response = ('27 02 FF FF FF',None),
security_access_27_01 = SID_27_01 + calculated_key
security_access_27_01_NRC = ('27 01','7F 27 7F'), ('27 02 FF FF FF', '7F 27 7F'),
security_access_27_01_NRC_22 = ('27 01','7F 27 22'), ('27 02 FF FF FF', '7F 27 22'),
request_for_seed_NRC_13 = ('27 01 02','7F 27 13'),
request_for_seed_incorrect_service_id = ('47 01', '7F 47 11'),
request_for_key_NRC_13 = ('27 02 01','7F 27 13'),
request_for_key_incorrect_service_id = ('57 02', '7F 57 11'),
incorrect_key_length_NRC_13 = ('27 02 FF FF FF FF', '7F 27 13'),
request_key_before_seed = ('27 02 FF FF FF', '7F 27 24'),
SID_27_NRC_13 = ('27', '7F 27 13'),
incorrect_sub_function_00_SID_27 = ('27 00','7F 27 12'),('27 00 FF FF FF','7F 27 12'),
incorrect_sub_function_FF_SID_27 = ('27 FF','7F 27 12'),('27 FF FF FF FF','7F 27 12'),
# </editor-fold>

# <editor-fold desc="Request Download Service">
REQUEST_DOWNLOAD = ('34 00 44 00 00 10 00 00 00 00 A4', '74 20 FF FF'),
REQUEST_DOWNLOAD_NO_RESPONSE = ('34', None),
REQUEST_DOWNLOAD_WITH_WRONG_DATA = ('34 00 45 10 00 00 00 00 B3 F5 8E 00','7F 34 31'),
REQUEST_DOWNLOAD_NRC_33 = ('34 00 44 10 00 00 00 00 B3 F5 8E','7F 34 33'),
REQUEST_DOWNLOAD_NRC_22 = ('34 00 44 10 00 00 00 00 B3 F5 8E','7F 34 22'),
# </editor-fold>

# <editor-fold desc="ECU Reset Service">
ECU_RESET_01 = ('11 01','51 01'),
ECU_RESET_01_No_Response = ('11 01', None),
ECU_RESET_81 = ('11 81', None),
Remote_Vehicle_Data_Collection_data_No_Response= ('22 EA 00', None),
Remote_Vehicle_Data_Collection_data = ('22 EA 00', '62 EA 00 F1 2E 03 ' + get_software_part_number("SWLM") + ' ' + get_software_part_number("SWL2") + ' ' + get_software_part_number("SWP1")+
                                       " F1 2A 50 99 07 61 20 41 41 F1 8C 00 00 00 00 "
                                       "F1 90 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00"),
RVDC_data_positive_response = ('22 EA 00', '62 EA 00 F1 2E 03 ' + get_software_part_number("SWLM") + ' ' + get_software_part_number("SWL2") + ' ' + get_software_part_number("SWP1")+
                              "F1 2A 50 99 07 61 20 41 41 F1 8C 00 00 00 00 "
                              "F1 90 41 42 30 31 34 38 43 45 35 36 33 34 45 42 31 31 31"),
incorrect_DLC_NRC13 = ('22 EA', '7F 22 13'),
incorrect_DLC_nrc31 = ('22 EA 00', '7F 22 31'),
incorrect_DLC1_NRC13 = ('22 EA 00 EA', '7F 22 13'),
incorrect_DLC2_NRC13 = ('22', '7F 22 13'),
incorrect_DLC_NRC31 = ('22 00 EA', '7F 22 31'),
incorrect_DLC1_NRC31 = ('22 EA EA 00', '7F 22 31'),
incorrect_DLC_NRC11 = ('23 EA 00', '7F 23 11'),

incorrect_data_length_01 = ('11 01 01', '7F 11 13'),
incorrect_data_length_81 = ('11 81 01', '7F 11 13'),
incorrect_sub_function_SID_11 = ('11 00', '7F 11 12'),('11 02','7F 11 12'),('11 03','7F 11 12'),('11 04','7F 11 12'),('11 82','7F 11 12'),
incorrect_service_identifier_51_01 = ('51 01','7F 51 11'),
incorrect_service_identifier_12_81 = ('12 81','7F 12 11'),
# </editor-fold>

# <editor-fold desc="Read DTC Service with sub-function 0x02">
Read_DTC_02 = ('19 02 FF','59 02 FF'),
Read_DTC_02_No_Response = ('19 02 FF', None),
Read_DTC_82 = ('19 82 FF',None),
Read_DTC_in_programming_mode = ('19 02 FF','7F 19 11'), ('19 82 FF','7F 19 11'),
Read_DTC_02_NRC_13 = ('19 02 FF', '7F 19 31'),
Read_DTC_02_FF_00_NRC_13 = ('19 02 FF 00','7F 19 13'),
incorrect_sub_function_SID_1902 = ('19 00 FF', '7F 19 12'), ('19 01 FF', '7F 19 12'), ('19 05 FF', '7F 19 12'), ('19 7F FF', '7F 19 12'), ('19 FF FF', '7F 19 12'),
incorrect_DLC_SID_1902 = ('19 02 FF FF','7F 19 13'),('19 82 FF FF','7F 19 13'),('19 02','7F 19 13'),('19 82','7F 19 13'),('19','7F 19 13'),
incorrect_service_id_SID_1902 = ('29 02 FF','7F 29 11'),
# </editor-fold>

# <editor-fold desc="Read DTC Information Service - 0x19">
Read_DTC_19 = ('19 06 91 6F 09 FF','59 06 91 6F 09 00'), ('19 86 91 6F 09 FF',None),
diagnostic_request_to_read_DTC_information_19 = ('19 06 91 6F 09 FF','7F 19 7F'), ('19 86 91 6F 09 FF','7F 19 7F'),
request_to_read_DTC_information_19 = ('19 04 91 6F 09 FF','59 04 91 6F 09 00'),('19 84 91 6F 09 FF',None),
Send_DTC_info_19 = ('19 04 91 6F 09 FF','7F 19 7F'),('19 04 91 6F 09 FF','7F 19 7F'),
Send_DTC_Snapshot_request_19 = ('19 03','59 03'),('19 83', None),
Send_DTC_Snapshot_info_19 = ('19 02 FF','19 82 FF'),('7F 19 7F','7F 19 7F')
# </editor-fold>

# <editor-fold desc="Read DTC Service with sub-function 0x03">
Read_DTC_03_NRC_13 = ('19 03 FF','7F 19 13'),('19 83 FF','7F 19 13'),
incorrect_sub_function_SID_1903 = ('19 43','7F 19 12'),('19 F3','7F 19 12'),
incorrect_service_ID_SID_1903 = ('29 03','7F 29 11'),('29 83','7F 29 11'),
# </editor-fold>

# <editor-fold desc="Read DTC Service with sub-function 0x04">
Read_DTC_04_NRC_13 = ('19 04','7F 19 13'),('19 04 91 6F 09','7F 19 13'),('19 04 91 6F 09 FF 2F','7F 19 13'),('19 84','7F 19 13'),('19 84 91 6F 09','7F 19 13'),('19 84 91 6F 09 FF 2F','7F 19 13'),
incorrect_sub_function_SID_1904 = ('19 44 91 6F 09 FF','7F 19 12'),('19 F4 91 6F 09 FF','7F 19 12'),
incorrect_service_ID_SID_1904 = ('29 04 91 6F 09 FF','7F 29 11'),('29 84 91 6F 09 FF','7F 29 11'),
Read_DTC_04_NRC_31 = ('19 04 91 6F 90 FF','7F 19 31'),('19 84 91 6F 90 FF','7F 19 31'),('19 04 91 6F 09 00','7F 19 31'),('19 04 91 6F 09 10','7F 19 31'),('19 84 91 6F 09 10','7F 19 31'),
# </editor-fold>

# <editor-fold desc="Read DTC Service with sub-function 0x06">
Read_DTC_06_NRC_13 = ('19 06','7F 19 13'),('19 06 91 6F 09','7F 19 13'),('19 06 91 6F 09 FF 2F','7F 19 13'),('19 86','7F 19 13'),('19 86 91 6F 09','7F 19 13'),('19 86 91 6F 09 FF 2F','7F 19 13'),
incorrect_sub_function_SID_1906 = ('19 56 91 6F 09 FF','7F 19 12'),('19 F6 91 6F 09 FF','7F 19 12'),
incorrect_service_ID_SID_1906 = ('29 06 91 6F 09 FF','7F 29 11'),('29 86 91 6F 09 FF','7F 29 11'),
Read_DTC_06_NRC_31 = ('19 06 91 6F 90 FF','7F 19 31'),('19 86 91 6F 90 FF','7F 19 31'),('19 06 91 6F 09 31','7F 19 31'),('19 86 91 6F 09 31','7F 19 31'),('19 06 91 6F 09 00','7F 19 31'),('19 06 91 6F 09 07','7F 19 31'),
# </editor-fold>

# <editor-fold desc="Read DTC Service by sub-function 0x06 in different sessions for DTC 0x916F09">
Read_DTC_information_possitive = ('19 06 91 6F 09 FF','59 06 91 6F 09 00'),('19 86 91 6F 09 FF', None),
Read_DTC_information_negative = ('19 06 91 6F 09 FF','7F 19 7F'),('19 86 91 6F 09 FF','7F 19 7F'),
Enter_into_extended_diagnostic_session_with_tester_present = SID_10_81 + SID_10_03 + Tester_present_00
Enter_into_programing_session_without_security_access = SID_10_81 + SID_10_02
# </editor-fold>

# <editor-fold desc="Read DTC Snapshot Record by DTC number (sub-function 0x04) in different sessions for DTC 0x916F09">
Read_DTC_information_possitive_04 = ('19 04 91 6F 09 FF', '59 04 91 6F 09 00'),('19 84 91 6F 09 FF',None),
Read_DTC_information_negative_04 = ('19 04 91 6F 09 FF', '7F 19 7F'),
# <editor-fold>

# <editor-fold desc=" Read DTC Snapshot Identification (sub-function 0x03) request in different sessions">
Read_DTC_Snapshot_Identification_Possitive = ('19 03', '59 03'), ('19 83', None)
Read_DTC_Snapshot_Identification_Negative = ('19 02 FF', '7F 19 7F')
# <editor-fold>
# <editor-fold desc="Clear Diagnostic Information">
clear_diagnostic_information = ('14 FF FF FF','54'),
clear_diagnostic_information_no_response = ('14 FF FF FF', None),
CDI_incorrect_session_NRC_11 = ('14 FF FF FF', '7F 14 11'),
CDI_incorrect_short_message_length_NRC_13 = ('14 FF FF','7F 14 13'),
CDI_incorrect_very_short_message_length_NRC_13 = ('14 FF','7F 14 13'),
CDI_incorrect_long_message_length_NRC_13 = ('14 FF FF FF FF','7F 14 13'),
CDI_incorrect_DTC_group_number = ('14 FF 00 AA','7F 14 31'),
# </editor-fold>

# <editor-fold desc="Write Data By Identifier">
DATA = '2E D0 1C AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 ' \
       '61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD ' \
       '28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 ' \
       'D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 ' \
       '3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 ' \
       '5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A ' \
       '8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E ' \
       '57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 ' \
       'E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 8E 35 19 56 '
incorrect_length_write_DID_D01C_NRC13 = ('2E D0','7F 2E 13'), ('2E D0 1C','7F 2E 13'), ('2E D0 1C 00','7F 2E 13'),
incorrect_session_D01C_NRC31 = ('2E D0 1C 00','7F 2E 31'),
write_DID_D01C_NRC33 = (DATA,'7F 2E 33'),
write_DID_D01C_positive_response = (DATA,'6E D0 1C'),
incorrect_length_long_AB_NRC13 = (DATA+'AB','7F 2E 13'),
incorrect_write_DIDF186_NRC31 = ('2E F1 86 02','7F 2E 31'),
incorrect_write_DID_D01C_NRC31 = ('2E D0 C1 1C','7F 2E 31'),
incorrect_DLC_D01C_NRC13 = ('2E D0 1C','7F 2E 13'), ('2E D0 1C 1C','7F 2E 13'),
incorrect_DLC_D01C_NRC13_functional = ('2E D0 1C','7F 2E 13'), ('2E D0 1C 00','7F 2E 13'),
Data_no_response =  ('2E D0 1C', None),
# </editor-fold>

public_key = '2E D0 1C AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F ' \
             '86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 ' \
             '49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED ' \
             'CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F ' \
             '49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E 57 87 E5 ' \
             'B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E 2A 8C 2E ' \
             '57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 3A 15 5E ' \
             '2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 17 D1 62 ' \
             '3A 15 5E 2A 8C 2E 57 87 E5 B0 DC 6F 49 1B ED CD 18 D5 49 77 0F 86 EE 20 06 62 61 AD 28 ' \
             '17 D1 55 00 00 00 01 00 00 00 00 00 00 00 00 61 E1 22 E3 03 F1 08 00 00 00 00 00 00 00 ' \
             '00 00 00 00 00'
write_public_key = (public_key,'6E D0 1C'),
# </editor-fold>

# <editor-fold desc="Transfer Data Service - 0x36 ">
Transfer_Data_01 = '36 01 00 00 00 04 00 00 20 00 00 00 00 A7 FA 46 E4 2D C3 E6 28 94 5B 21 FC A7 '\
                '3C 76 A5 7F 14 C8 8C 43 99 67 F6 BA 15 FC 19 51 9B 16 C4 B0 E0 00 00 00 00 CD '\
                '0A F2 3A 47 BE AA 87 4B 76 47 98 FE 5D 57 79 54 F2 E2 87 AE 4D F3 A9 3B 31 F3 '\
                '1E 52 53 60 AC 58 89 7A F0 00 00 00 0E D7 C0 00 4C AB 03 21 D5 01 3D 4C 8A 51 '\
                '99 EE 2D 8A 5B 7E FA 5E 02 41 C5 68 E0 BC 67 CB FC B5 0B 4B 7A 65 D0 00 00 00 '\
                '00 03 A6 19 4A ED 83 EC 3C 32 8F 2F 3E BC 31 F5 F9 7A 26 8D 82 71 42 38 2C E6 '\
                '58 84 8D 0E 6B C3 24 22 69 E7'
request_transfer_data_01 = (Transfer_Data_01, '76 01'),

Transfer_Data_00 = '36 00 00 00 00 04 00 00 20 00 00 00 00 A7 FA 46 E4 2D C3 E6 28 94 5B 21 FC A7 '\
                '3C 76 A5 7F 14 C8 8C 43 99 67 F6 BA 15 FC 19 51 9B 16 C4 B0 E0 00 00 00 00 CD '\
                '0A F2 3A 47 BE AA 87 4B 76 47 98 FE 5D 57 79 54 F2 E2 87 AE 4D F3 A9 3B 31 F3 '\
                '1E 52 53 60 AC 58 89 7A F0 00 00 00 0E D7 C0 00 4C AB 03 21 D5 01 3D 4C 8A 51 '\
                '99 EE 2D 8A 5B 7E FA 5E 02 41 C5 68 E0 BC 67 CB FC B5 0B 4B 7A 65 D0 00 00 00 '\
                '00 03 A6 19 4A ED 83 EC 3C 32 8F 2F 3E BC 31 F5 F9 7A 26 8D 82 71 42 38 2C E6 '\
                '58 84 8D 0E 6B C3 24 22 69 E7'
request_transfer_data_00 = (Transfer_Data_00, '76 00'),

Transfer_Data_02 = '36 02 00 00 00 04 00 00 20 00 00 00 00 A7 FA 46 E4 2D C3 E6 28 94 5B 21 FC A7 '\
                '3C 76 A5 7F 14 C8 8C 43 99 67 F6 BA 15 FC 19 51 9B 16 C4 B0 E0 00 00 00 00 CD '\
                '0A F2 3A 47 BE AA 87 4B 76 47 98 FE 5D 57 79 54 F2 E2 87 AE 4D F3 A9 3B 31 F3 '\
                '1E 52 53 60 AC 58 89 7A F0 00 00 00 0E D7 C0 00 4C AB 03 21 D5 01 3D 4C 8A 51 '\
                '99 EE 2D 8A 5B 7E FA 5E 02 41 C5 68 E0 BC 67 CB FC B5 0B 4B 7A 65 D0 00 00 00 '\
                '00 03 A6 19 4A ED 83 EC 3C 32 8F 2F 3E BC 31 F5 F9 7A 26 8D 82 71 42 38 2C E6 '\
                '58 84 8D 0E 6B C3 24 22 69 E7'

Transfer_Data_09 = '36 09 00 00 00 04 00 00 20 00 00 00 00 A7 FA 46 E4 2D C3 E6 28 94 5B 21 FC A7 '\
                '3C 76 A5 7F 14 C8 8C 43 99 67 F6 BA 15 FC 19 51 9B 16 C4 B0 E0 00 00 00 00 CD '\
                '0A F2 3A 47 BE AA 87 4B 76 47 98 FE 5D 57 79 54 F2 E2 87 AE 4D F3 A9 3B 31 F3 '\
                '1E 52 53 60 AC 58 89 7A F0 00 00 00 0E D7 C0 00 4C AB 03 21 D5 01 3D 4C 8A 51 '\
                '99 EE 2D 8A 5B 7E FA 5E 02 41 C5 68 E0 BC 67 CB FC B5 0B 4B 7A 65 D0 00 00 00 '\
                '00 03 A6 19 4A ED 83 EC 3C 32 8F 2F 3E BC 31 F5 F9 7A 26 8D 82 71 42 38 2C E6 '\
                '58 84 8D 0E 6B C3 24 22 69 E7'

transfer_data_incorrect_dlc = '36 01 00 00 00 04 00 00 20 00 00 00 00 A7 FA 46 E4 2D C3 E6 28 94 5B 21 FC A7 '\
                              '3C 76 A5 7F 14 C8 8C 43 99 67 F6 BA 15 FC 19 51 9B 16 C4 B0 E0 00 00 00 00 CD '\
                              '0A F2 3A 47 BE AA 87 4B 76 47 98 FE 5D 57 79 54 F2 E2 87 AE 4D F3 A9 3B 31 F3 '\
                              '1E 52 53 60 AC 58 89 7A F0 00 00 00 0E D7 C0 00 4C AB 03 21 D5 01 3D 4C 8A 51 '\
                              '99 EE 2D 8A 5B 7E FA 5E 02 41 C5 68 E0 BC 67 CB FC B5 0B 4B 7A 65 D0 00 00 00 '\
                              '00 03 A6 19 4A ED 83 EC 3C 32 8F 2F 3E BC 31 F5 F9 7A 26 8D 82 71 42 38 2C E6 '\
                              '58 84 8D 0E 6B C3 24 22 69'

incorrect_request_transfer_data_NRC11 = (Transfer_Data_01, '7F 36 11'),
incorrect_request_transfer_data_NRC24 = (Transfer_Data_01,'7F 36 24'),
incorrect_request_transfer_data_NRC13 = ('36','7F 36 13'),
Transfer_data_no_response = ('36', None),
incorrect_request_transfer_data_1_NRC71 = (Transfer_Data_01 + 'AA 00', '7F 36 71'),
incorrect_transfer_data_request_NRC71 = (transfer_data_incorrect_dlc,'7F 36 71'),
incorrect_request_transfer_data_NRC73 = (Transfer_Data_00,'76 00'),(Transfer_Data_02,'7F 36 73'),
incorrect_transfer_data_request_NRC73 = (Transfer_Data_09,'7F 36 73'),
incorrect_DLC_transfer_data_NRC13 = ('36 01','7F 36 13'),
incorrect_request_transfer_data_2_NRC71 = ('36 01 00','7F 36 71'),
incorrect_transfer_data_request_NRC24 = (Transfer_Data_01, '76 01'),(Transfer_Data_02,'7F 36 24'),

# </editor-fold>

# <editor-fold desc="Transfer Exit Service - 0x37 ">
request_transfer_exit = ('37','77'),
request_transfer_no_response = ('37', None),
incorrect_transfer_exit_request_NRC11 = ('37','7F 37 11'),
incorrect_transfer_exit_request_NRC24 = ('37','7F 37 24'),
incorrect_transfer_exit_request_NRC13 = ('37 01','7F 37 13'),('37 FF','7F 37 13'),('37 00','7F 37 13'),
# </editor-fold>

# <editor-fold desc="KEYWORDS">
Enter_in_Default_Session = SID_10_01
Enter_Extended_Session_with_Tester_Present = ('10 81', None), ('10 03', '50 03 00 32 01 F4'), ('3E 00', '7E 00'),
# P2 Server Timer value need to be updated to 00 32 later
Enter_into_Programming_Session_without_Security_Access = ('10 81', None), ('10 02', '50 02 00 28 01 F4')
Programming_session_with_security_access = Enter_into_Programming_Session_without_Security_Access + check_programming_session + \
                                           Tester_present + security_access_27_01
# P2 Server Timer value need to be updated to 00 32 later
Enter_into_Active_Bootloader_Partition = ('10 81',None),('10 02','50 02 00 28 01 F4'),
F120_Incorrect_DLC = ('22 F1 20 01', '7F 22 13'),
F12A_Incorrect_DLC = ('22 F1 2A 01','7F 22 13'),
F12E_Incorrect_DLC = ('22 F1 2E 01','7F 22 13'),
F186_Incorrect_DLC = ('22 F1 86 01','7F 22 13'),
F125_Incorrect_DLC = ('22 F1 25 00','7F 22 13'),
F121_Incorrect_DLC = ('22 F1 21 00','7F 22 13'),('22 F1','7F 22 13')
F34_Incorrect_DLC = ('34 00 44 90 00 00 00 10 00 00','7F 34 13'),('34 00 44 90 00 00 00 10 00 00 00 00','7F 34 13')
F120_Incorrect_DID = ('22 51 20','7F 22 31'),
F12A_Incorrect_DID = ('22 51 2A','7F 22 31'),
F12E_Incorrect_DID = ('22 51 2E','7F 22 31'),
F186_Incorrect_DID = ('22 51 86','7F 22 31'),
F125_Incorrect_DID = ('22 F6 25','7F 22 31'),
F121_Incorrect_DID = ('22 51 21','7F 22 31'),
F34_Incorrect_SID = ('64 00 44 90 00 00 00 10 00 00 00','7F 64 11'),
Exit_Programming_Session = ECU_RESET_01
Exit_Programming_Session_by_Default_Session = SID_10_01
# Check_primary_bootloader_diagnostic_db_part_number_in_programming_session = read_part_number_21
Send_request_download_request_in_programming_session_during_software_downloading = REQUEST_DOWNLOAD_NRC_22

Write_Public_Key_Data_Record = SID_10_81 + SID_10_02 + Tester_present + security_access_27_01 + write_public_key+ SID_10_81

# My own keywords
Enter_and_verify_default_session = SID_10_01 + check_default_session
Enter_into_Extended_Diagnostic_Session_and_verify = Enter_Extended_Session_with_Tester_Present + check_extended_session
Enter_into_Programming_Diagnostic_Session_and_verify = Enter_into_Programming_Session_without_Security_Access + check_programming_session
Enter_Extended_Session = ('10 81', None), ('10 03', '50 03 00 32 01 F4')


# </editor-fold>

def sock_connection():
    logger.debug("GRPC UDS connection using connect_uds_server function")
    # print("GRPC UDS connection using connect_uds_server function")
    status = connect_uds_server(SOCKET_ADDRESS)
    assert status, "GRPC UDS connection is not connected."

def validate_diagnostics_requests(diag_request_tuple: tuple, address: AddressEnum = AddressEnum.TARGET_ADDRESS):
    """
    assert the tuple of Diagnostics request and response given. if you want to update the test case title in allure report
    pass the alm test case name in the last index of the tuple.
    Args:
        diag_request_tuple: Tuple with diagnostics request and response if any request not have a response pass as None
        address: To switch between the Target address and Functional address Byu default Target address
    Examples:
        if you want to update Name in allure report
        validate_diagnostics_requests((('10 00','7F 10 12'),('22 F1 86' ,'62 F1 86 01'),"ALM ID: ALM Name"))

        if you don't want to update test case name in report
        validate_diagnostics_requests((('10 00','7F 10 12'),('22 F1 86' ,'62 F1 86 01'),None))

    Returns: None

    """
    # update test case title if last value of tuple is not None
    if diag_request_tuple[-1] is not None:
        allure_test_link(diag_request_tuple[-1])
    # loop the complete list of request pass to the function
    for test_case_value in diag_request_tuple[:-1]:
        if len(test_case_value) == 2:
            (message,expected_response_message) = test_case_value
            wait_time = 0
        else:
            (message, expected_response_message,wait_time) = test_case_value
        with allure.step("Send the doip request --> {}".format(message)):
            did_response = send_command_and_get_response(message,set_address=address)
            logger.debug("DID --> {}, Response --> {}".format(message, did_response))
        if expected_response_message is not None:
            with allure.step("Validating the Doip response --> {}".format(did_response['rawResponse'])):
                assert did_response[
                           'rawResponse'] is not None, "No response from DOIP , status --> {} , DID --> {}, Expected Response --> {}".format(
                    did_response['response'], message,expected_response_message)
                assertion(did_response['rawResponse'].strip(), '==', expected_response_message.upper(),
                          "Expected response --> {} is not found in DOIP response --> {}".format(
                              expected_response_message.upper(), did_response['rawResponse'].strip()))
        sleep(wait_time)
        if message in WAIT_FOR_UDS:
            logger.debug("Waiting for SSH connection after TCAM2 reboot")
            sleep(2)
            ip_connection = connection_wait_in_loop(TCU_IP, WAIT_FOR_ETH_DURING_UDS)
            assert ip_connection < WAIT_FOR_ETH_DURING_UDS, "NO ETH connection to TCU after --> {} sec".format(ip_connection)


def with_delay(req: tuple, delay: float = 5) -> tuple:
    """
    To add timeout/delay after any diagnostics request
    Args:
        req: Type is Tuple which contain request and response
        delay: Type is float Delay need to be added after request and response
    Examples:
        ``updated_sid = with_delay(SID_10_01_81,10)``

    Returns: Tuple diagnostics request added with delay

    """
    return req[0]+(delay,),

def with_timing(req: tuple, time_limite: float) -> tuple:
    """
    Add the required timing limit for a diagnostics request
    Args:
        req: diagnostics request and response in a tuple.
        time_limite: Timing limit

    Returns: req Tuple appended with timing parameter

    """
    return with_delay(req,time_limite)

def validate_timing_parameter(diag_request_tuple: tuple, address: AddressEnum = AddressEnum.TARGET_ADDRESS):
    """
    assert the tuple of Diagnostics request and response given. if you want to update the test case title in allure report
    pass the alm test case name in the last index of the tuple.
    Args:
        diag_request_tuple: Tuple with diagnostics request and response if any request not have a response pass as None
        address: To switch between the Target address and Functional address Byu default Target address
    Examples:
        if you want to update Name in allure report
        validate_diagnostics_requests((('10 00','7F 10 12'),('22 F1 86' ,'62 F1 86 01'),"ALM ID: ALM Name"))

        if you don't want to update test case name in report
        validate_diagnostics_requests((('10 00','7F 10 12'),('22 F1 86' ,'62 F1 86 01'),None))

    Returns: None

    """
    # update test case title if last value of tuple is not None
    required_timing = dict()

    if diag_request_tuple[-1] is not None:
        allure_test_link(diag_request_tuple[-1])
    # loop the complete list of request pass to the function
    for test_case_value in diag_request_tuple[:-1]:
        if len(test_case_value) == 2:
            (message,expected_response_message) = test_case_value
            timing_limit = 50
        else:
            (message, expected_response_message,timing_limit) = test_case_value
        with allure.step("Send the doip request --> {}".format(message)):
            did_response = send_command_and_get_response(message,set_address=address)
            logger.debug("DID --> {}, Response --> {}".format(message, did_response))
        response_time = int(did_response['responseTime'].strip()[:-2])
        with allure.step("Validating response time {} ms is less than {} ms".format(response_time,timing_limit)):
            assertion(response_time,'<=',timing_limit,"Response time {} should be less {}".format(response_time,timing_limit))
        if expected_response_message is not None:
            assert did_response['rawResponse'] is not None, "No response from DOIP , status --> {} , DID --> {}".format(did_response['response'],message)
            with allure.step("Validating the Doip response --> {}".format(did_response['rawResponse'])):
                assertion(did_response['rawResponse'].strip(), '==', expected_response_message.upper(),
                          "Expected response --> {} is not found in DOIP response --> {}".format(
                              expected_response_message.upper(), did_response['rawResponse'].strip()))

        if message not in required_timing.keys():
            required_timing[message] = response_time
        else:
            if isinstance(required_timing[message],list):
                required_timing[message].append(response_time)
            else:
                required_timing[message] = [required_timing[message],response_time]

        if message in WAIT_FOR_UDS:
            logger.debug("Waiting for SSH connection after TCAM2 reboot")
            sleep(2)
            ip_connection = connection_wait_in_loop(TCU_IP, WAIT_FOR_ETH_DURING_UDS)
            assert ip_connection < WAIT_FOR_ETH_DURING_UDS, "NO ETH connection to TCU after --> {} sec".format(ip_connection)
    return required_timing

if __name__ == "__main__":
    print(with_delay(SID_10_01_81))
