import logging

import allure

from interface.SSH.SSHInterface import execute_command_and_return_console_output

logger = logging.getLogger("test_logger")


@allure.suite("Infrastructure")
class TestSoftwareVersion(object):

    def test_Version_varification(self, pytestconfig):

        try:
            dir = pytestconfig.option.allure_report_dir
            a = execute_command_and_return_console_output('cat /etc/nets-build-details')
            logger.info("Build details : %s", a)
            a = a.split("\n")
            logger.debug("List {}".format(a))
            get_wuc_version = execute_command_and_return_console_output('/opt/bin/imageSelection GetWucVersion').split('\n')
            for value in get_wuc_version:
                if "Wuc Version:" in value:
                    wuc_version = value.split(':')[-1]
                    logger.debug("Wuc version is -- {}".format(wuc_version))
            f = open(dir + '/' + "environment.properties", "w+")
            f.write('WCU_Version={}\n'.format(wuc_version))
            f.write('Elina_Version ={}\n'.format(a[0]))
            f.write('Build_Tag ={}\n'.format(a[1]))
            f.write('Board ={}\n'.format(a[2]))
            for i in range(3, len(a) - 1):
                report_value = a[i].split('_')
                f.write("{} = {} \n".format(report_value[0],report_value[1]))

            f.close()
        except Exception as e:
            logger.error("Exception while collecting environment %s", str(e))
            pass
