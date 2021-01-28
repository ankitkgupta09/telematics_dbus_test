import allure
import pytest
import time
import os
from pathlib import Path
from config import WINDOWS
if WINDOWS:
    import win32com.client
from artifactory import ArtifactoryPath

from interface.Relay.RelayInterface import Relay_ON,Relay_OFF
from interface.PowerSupply.PowerSupplyInterface import set_voltage,POWER_SUPPLY_CHANNEL
from interface.utils import restart,bluebox_command,remove_process,RELAY_ID,FHE_RELAY_NUMBER,FASTBOOT_NUMBER,unzip
from interface.Serial.SerialInterface import find_serial_port
from config import LOGPATH,logger
from interface.utils import clear_folder_or_files
from interface.AllureReport.AllureInterface import allure_test_link

process_list = ['putty.exe', 'ttermpro.exe','MobaXTerm.exe','teraterm.exe']
dir_path = os.path.abspath(os.path.dirname(__file__))+os.sep+"UtilityFiles"
build_dir = LOGPATH + os.sep + "Build"
UTILITY = "{}{}UtilityFiles".format(os.path.abspath(os.path.dirname(__file__)),os.sep)

# IMAGE_FOLDER = "C:\\jenkins\\BMW_Wave"
ICO_FLASH_SCRIPT = "D:\\project\\tcam2\\S32K148\\flasher\\"
IMAGE_FOLDER = build_dir
PROJECT = "TCAM"
BMW = [('mmc0boot0', 'MBR_EMMC_BOOT0'), ('mmc0', 'mtk_mbr_emmc'), ('BIOSTEE', 'bios_tz.img'),
                   ('BOOTIMG', 'emrg_boot.img'),
                   ('BL1', 'lk.img'), ('TEE1', 'tz.img'), ('APPKERNEL1', 'app_boot.img'),
                   ('APPROOTFS1', 'app_rootfs.ext4'),
                   ('TEE2', 'tz.img'), ('APPKERNEL2', 'app_boot.img'), ('APPROOTFS2', 'app_rootfs.ext4'),
                   ('RW', 'persist.ext4'),
                   ('SWDL', 'swdl.ext4'), ('PROD', 'prod.ext4'), ('APPPROGFS1', 'progfs.ext4'),
                   ('APPPROGFS2', 'progfs.ext4'),
                   ('RADIO0MODEM1', 'radio0.ext4'), ('RADIO0MODEM2', 'radio0.ext4'), ('BTLDKERNEL1', 'btld_boot.img'),
                   ('BTLDROOTFS1', 'btld_rootfs.ext4'), ('BTLDKERNEL2', 'btld_boot.img'),
                   ('BTLDROOTFS2', 'btld_rootfs.ext4')]

TCAM = [('mmc0boot0','MBR_EMMC_BOOT0'),('mmc0','mtk_mbr_emmc'),('BL1','lk.img'),('APPKERNEL1','app_boot.img'),
        ('APPROOTFS1','app_rootfs.ext4'),('RADIO0MODEM1','radio0.ext4'),('TEE1','tz.img'),
        ('BTLDKERNEL1','btld_boot.img'),('BTLDROOTFS1','btld_rootfs.ext4'),('APPKERNEL2','app_boot.img'),
        ('APPROOTFS2','app_rootfs.ext4'),('RADIO0MODEM2','radio0.ext4'),('TEE2','tz.img'),
        ('BTLDKERNEL2','btld_boot.img'),('BTLDROOTFS2','btld_rootfs.ext4'),('RW1','persist.ext4'),
        ('RW2','persist.ext4'),('SWDL','swdl.ext4'),('PROD','prod.ext4'),('CFG1','localcfg.ext4'),('CFG2','localcfg.ext4')]


artifact_user = 'svc_ink_bot'
artifact_password = 'CGe2+W3e'

flash_file_dict = {"BMW" : BMW, "TCAM" : TCAM}
flash_file_list = flash_file_dict[PROJECT]
def VerifyFastbootMode(retry=3):
    """Function to validate fastboot mode is switch properly
    """
    while retry > 0:
        cmd_status = os.popen("fastboot devices").read()
        fastboot_id = cmd_status.split("\t")[0]
        logger.debug("fastboot devices output is --> {}".format(cmd_status))
        if len(fastboot_id) > 17:
            logger.debug("Fastboot is detected in correct mode")
            return True
        set_voltage(POWER_SUPPLY_CHANNEL, 0)
        time.sleep(5)
        set_voltage(POWER_SUPPLY_CHANNEL,12)
        time.sleep(2)
        retry = retry -1
    return False

@pytest.fixture()
def url(pytestconfig):
    return pytestconfig.getoption("url")

def download_build(url,build_local_path=build_dir):
    """
    Download the build from artifactory to local PC
    Args:
        url: Artifactory URL
        build_local_path: local PC path to download the build

    Returns: None

    """
    # download the 7zip file using request
    # current_dir = os.getcwd()
    # if not os.path.exists(build_local_path):
    #     os.mkdir(build_local_path)
    # clear_folder_or_files(build_local_path)
    # logger.debug("current working DIR is -- {}".format(os.getcwd()))
    build_name = url.split('/')[-1]
    path = ArtifactoryPath(
        url,
        auth=(artifact_user, artifact_password))
    logger.debug("Path --> {}".format(path))
    with path.open() as fd:
        temp_var = build_local_path+os.sep+build_name
        with open(temp_var, "wb") as out:
            out.write(fd.read())
    # Extract the 7zip file
    unzip(temp_var)
    # os.chdir(current_dir)


@allure.suite("Copy Software To local")
class TestDownloadBuild(object):
    
    """Copy Build from Artifact"""
    @classmethod
    def setup_class(cls):
        """Setup for Download Build"""
        remove_process(process_list)
        clear_folder_or_files(build_dir)
        time.sleep(2)
        cls.current_dir = os.getcwd()
        if not os.path.exists(build_dir):
            os.mkdir(build_dir)
        os.chdir(build_dir)

    def test_download(self,url):
        """Download build"""
        download_build(url)

    # def test_verify_build_files(self):
    #     """Verify all the required files are present in build or not"""
    #     expected_file_list = [a_tuple[1] for a_tuple in flash_file_list]
    #     logger.debug("Validating {} are present or not".format(expected_file_list))
    #     actual_file_list = os.listdir(build_dir)
    #     logger.debug("Files download are --> {}".format(actual_file_list))
    #     for file in expected_file_list:
    #         assert file in actual_file_list,"{} file is not found in Build".format(file)

    def test_vbf_files(self):
        """Verify the vbf file size"""
        allure_test_link("47848")
        p_path = Path(build_dir)
        list_of_files = list(p_path.glob('*.vbf'))
        assert len(list_of_files) == 4, "The VBFs present are {}".format(list_of_files)
        vbfs = [(str(x.name) + '\n').encode() for x in list_of_files]

        with open('tcam2.vbs', 'wb') as outfile:
            outfile.writelines(vbfs)
        # os.system("cp {}{}tcam2.vbs tcam2.vbs".format(UTILITY,os.sep))
        return list_of_files

    def test_vbf_file_size(self):
        allure_test_link("62253")
        lof = self.test_vbf_files()
        file_size_dict = dict()
        for i in lof:
            file_size_dict[i.name] = i.stat().st_size
        logger.info("File sizes are \n {}".format(file_size_dict))

    @classmethod
    def teardown_class(cls):
        """teardown"""
        os.chdir(cls.current_dir)

@allure.suite("Flash WUC")
class TestWuCFlash(object):
    """WUC flashing"""
    @classmethod
    def setup_class(cls):
        """Setup the flash boot flashing for TCU"""
        remove_process(process_list)
        Relay_OFF(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        # set_voltage(POWER_SUPPLY_CHANNEL, 0)
        time.sleep(10)
        Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        time.sleep(8)
        bluebox_command("0x03")
        restart(POWER_SUPPLY_CHANNEL, ip_connection_timeout=2,connection_status=False)
        time.sleep(10)
        cls.ax8 = win32com.client.Dispatch("Ax8.CoAx8")
        cls.ax8.connect()
        bin_path = dir_path + "\\swipro.bin"
        cls.ax8.Write_SystemLatch(0)
        loaded = cls.ax8.Load_FHE_FPGA(bin_path)
        logger.debug("swipro.bin loading status --> {}".format(loaded))
        assert loaded,"swipro.bin file is not loaded properly"
        time.sleep(1)
        set_voltage(POWER_SUPPLY_CHANNEL, 12)
        time.sleep(1)

    def test_flashWUC(self):
        """Flash WUC"""
        cmd = "ttpmacro.exe {}\\xmodemsend.ttl {} {} ".format(dir_path,find_serial_port(),IMAGE_FOLDER+os.sep+"tcam_wuc.bin")
        logger.debug(cmd)
        os.system(cmd)
        time.sleep(1)

    @classmethod
    def teardown_class(cls):
        "Change the bluebox mode"
        cls.ax8.DisConnect()
        process_list = ['Ax8.exe']
        remove_process(process_list)
        time.sleep(1)
        restart(POWER_SUPPLY_CHANNEL, ip_connection_timeout=0,connection_status=False)
        process_list = ['ttermpro.exe']
        remove_process(process_list)

@allure.suite("Flash Soc")
class TestSoCFlash(object):
    """Flash the SoC"""
    @classmethod
    def setup_class(cls):
        """Setup the flash boot flashing for TCU"""
        Relay_OFF(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        set_voltage(POWER_SUPPLY_CHANNEL, 0)
        time.sleep(10)
        Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        time.sleep(8)
        bluebox_command("0x86")
        restart(POWER_SUPPLY_CHANNEL, ip_connection_timeout=0,connection_status=False)
        assert VerifyFastbootMode(),"Fastboot device is not detected"
        os.system("fastboot.exe flash EMPTY {}".format(IMAGE_FOLDER+os.sep+"lk.img"))
        time.sleep(5)
        os.system("fastboot.exe erase mmc0boot0")
        os.system("fastboot.exe erase mmc0")

    @pytest.mark.parametrize("partition,file",flash_file_list)
    def test_flash(self,partition,file):
        """Flash the individual component"""
        cmd = "fastboot.exe flash {} {}".format(partition,IMAGE_FOLDER+os.sep+file)
        cmd_status = os.system(cmd)
        logger.debug("Flash status is {}".format(cmd_status))
        assert cmd_status == 0,"Fail for flash --> {}".format(file)


    @classmethod
    def teardown_class(cls):
        "Change the Bluebox mode"
        bluebox_command("0x82")
        restart(POWER_SUPPLY_CHANNEL)
        Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)

@allure.suite("Flash IoC")
class TestIoCFlash(object):
    """IoC flashing, flash is required only on IoC release so not the part of automation for now"""

    @classmethod
    def setup_class(cls):
        """Setup the flash boot flashing for TCU"""
        # remove_process(process_list)
        # Relay_OFF(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        # # set_voltage(POWER_SUPPLY_CHANNEL, 0)
        # time.sleep(10)
        # Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)
        # time.sleep(8)
        bluebox_command("0x82")
        restart(POWER_SUPPLY_CHANNEL, ip_connection_timeout=0,connection_status=False)
        time.sleep(10)
        cls.ax8 = win32com.client.Dispatch("Ax8.CoAx8")
        cls.ax8.connect()
        bin_path = dir_path + "\\bluebox_s32k_0109.bin"
        cls.ax8.Write_SystemLatch(8)
        loaded = cls.ax8.Load_FHE_FPGA(bin_path)
        logger.debug("bin loading status --> {}".format(loaded))
        assert loaded,"bin file is not loaded properly"
        time.sleep(1)
        cls.ax8.DisConnect()
        process_list = ['Ax8.exe']
        remove_process(process_list)

        set_voltage(POWER_SUPPLY_CHANNEL, 12)
        time.sleep(1)
        cls.current_dir = os.getcwd()
        os.chdir(ICO_FLASH_SCRIPT)

    def test_ioc_flash(self):
        """IOC flash script"""
        cmd = "s32k_flash.bat {} s32k148 chip_erase do_loadflasher {}".format(find_serial_port(),IMAGE_FOLDER+os.sep+"tcam_ioc.bin")
        logger.debug(cmd)
        assert os.system(cmd) ==0,"IOC flash Failed, More detail please look at stderr"
        time.sleep(1)

    @classmethod
    def teardown_class(cls):
        "Change the Bluebox mode"
        time.sleep(1)
        bluebox_command("0x82")
        restart(POWER_SUPPLY_CHANNEL,connection_status=False,ip_connection_timeout=0)
        Relay_ON(RELAY_ID, FHE_RELAY_NUMBER, FASTBOOT_NUMBER)

@allure.suite("VBF Flashing")
class TestVbfFlash(object):
    """Flash software using VBF files"""

    def test_flash_vbf(self):
        os.chdir(UTILITY)

        if WINDOWS:
            cmd = "goofy.exe -f -edgesim -destination localhost:13400 -config cfg.json -wd 50 -v {}/tcam2.vbs".format(build_dir)
        else:
            cmd = "goofy -f -edgesim -destination localhost:13400 -config cfg.json -wd 50 -v {}/tcam2.vbs".format(build_dir)
        flash_response = os.system(cmd)
        assert flash_response == 0,"VBF flashing failed"

if __name__ == "__main__":
    t = TestDownloadBuild()
    print(t.test_vbf_file_size())