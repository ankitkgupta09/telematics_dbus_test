import subprocess
import time
import sys
import os,shutil,glob
from interface.SSH.SSHInterface import execute_command_and_return_console_output
from interface.utils import connection_wait_in_loop,TCU_IP
from config import LOGPATH,logger
from utility.SoftwareUpdate.SoftwareUpdateUtility import async_reset_tcu
dir_path = os.path.dirname(os.path.realpath(__file__))

from config import *

Channal = peripherals.get('powersupply','Channel')

def copy_file():
    p = subprocess.Popen('echo y | pscp -scp ' + dir_path +'/file_to_push/*.* root@' + TCU_IP + ':/tmp/', shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print('precondition files push to tmp location: ', p.stdout.readlines())
    time.sleep(2)

def copy_wuc_file():
    wuc_file_path = LOGPATH + os.sep + "Build" + os.sep
    print(wuc_file_path)
    wuc_file = glob.glob(wuc_file_path + '\*.s19')
    print(wuc_file[0])
    if wuc_file[0]:
        shutil.copy(wuc_file[0], dir_path + '/file_to_push/' )
        logger.debug("wuc_file is present in the path {} for copying to target".format(wuc_file_path))
    else:
        logger.debug("wuc_file is not present in the path {} for copying to target".format(wuc_file_path))


def copy_wuc_tmp2bin():
    status = execute_command_and_return_console_output("ls -l /tmp/tcam_wuc.s19|wc -l|tr -d '\n'")
    logger.debug("status is {}".format(status))
    if status == "1":
        execute_command_and_return_console_output('cp /tmp/*.s19 /opt/bin/')
    else:
        logger.debug("WUC file not present for copying")
        assert status == "1", "WUC file not present for copying"

def mount():
    execute_command_and_return_console_output('mount -o remount, rw /')
    execute_command_and_return_console_output("/bin/sync")
    time.sleep(2)

def dbus_precondition():
    execute_command_and_return_console_output('cp /tmp/system.conf /etc/dbus-1/system.conf')
    time.sleep(2)
    execute_command_and_return_console_output('cp /tmp/system-local.conf /etc/dbus-1/system-local.conf')
    time.sleep(2)
    execute_command_and_return_console_output('cp /tmp/dbus.socket /lib/systemd/system/dbus.socket')
    time.sleep(2)
    execute_command_and_return_console_output("/bin/sync")
    time.sleep(1)
    execute_command_and_return_console_output("/bin/sed -i 's/deny/allow/g' /etc/dbus-1/system-local.conf")
    time.sleep(2)
    execute_command_and_return_console_output("/bin/sed -i 's/deny/allow/g' /etc/dbus-1/system.conf")
    time.sleep(2)
    ret = execute_command_and_return_console_output("/bin/sed -i 's/deny/allow/g' /etc/dbus-1/system.d/ofono.conf")
    time.sleep(4)
    ret = execute_command_and_return_console_output("/bin/sync")
    # restart(Channal,Type="PowerSupply")
    # time.sleep(10)

def gdbus_precondition():
    execute_command_and_return_console_output('cp /tmp/gdbus /usr/bin/gdbus')
    execute_command_and_return_console_output('chmod 777 /usr/bin/gdbus')

if __name__=="__main__":
    try:
        connection_time = connection_wait_in_loop(TCU_IP, 100)
        assert connection_time < 100,"Fail to connected with TCU over SSH interface"
        # copy_wuc_file()
        copy_file()
        mount()
        # gdbus_precondition()
        # AT_Clint()
        # copy_wuc_tmp2bin()
        dbus_precondition()
        # TODO update to PPS reboot
        async_reset_tcu(1)
        sys.exit(0)
    except Exception as e:
        print("Exception in precondition %s",str(e))
        sys.exit(1)

    
