import allure
import csv
from config import logger
import os

FILE_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), '.{}Test_Case.csv'.format(os.sep))
try:
    reader = csv.DictReader(open(FILE_PATH))
    alm_test_data = dict()
    for row in reader:
        alm_test_data[row['ID']] = row
except Exception as e:
    logger.error("Fail to read the ALM test cases list -- {}".format(e))


def allure_test_link(alm_id: str) -> None:
    """
    Function will update the test case name and link as per the ALM
    Args:
        alm_id: ALM test case ID

    Returns: None
    Examples:
        `allure_test_link("1234")`

    """
    try:
        test_data = alm_id.split(':')
        if len(test_data)>1:
            logger.debug("Test case name given")
            if test_data[0] != "NA":
                allure.dynamic.testcase("{}".format(alm_test_data[test_data[0]]['URL']), "ALM Test Case Id : {}".format(test_data[0]))
                allure.dynamic.title("{}".format(alm_test_data[test_data[0]]['Name']))
                allure.dynamic.description(alm_test_data[test_data[0]]['Description'])
            else:
                allure.dynamic.title("{}".format(test_data[1]))
        else:
            allure.dynamic.testcase("{}".format(alm_test_data[alm_id]['URL']), "ALM Test Case Id : {}".format(alm_id))
            allure.dynamic.title("{}".format(alm_test_data[alm_id]['Name']))
            allure.dynamic.description(alm_test_data[alm_id]['Description'])
    except Exception as e:
        logger.debug("Fail to get the ALM ID from interface")

def update_kpi_in_allure(kpi_data):
    """
    Create a new file in allure report KPI DATA
    Args:
        kpi_data: Data which need to be added

    Returns: None

    """
    allure.attach(kpi_data,"KPI DATA")