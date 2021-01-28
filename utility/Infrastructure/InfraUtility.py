from interface.SSH.SSHInterface import execute_command_on_active_shell_and_return_console_output, close_shell
from config import logger

def open_application_get_items(app_name,option_sep ="."):
    """
    open the test application
    Args:
        app_name: Appcation
        option_sep:

    Returns:

    """
    option = dict()
    output = execute_command_on_active_shell_and_return_console_output(app_name)
    for op in output.split('\n'):
        if option_sep in op:
            temp = op.split(option_sep)
            option[temp[1].strip()] = temp[0]
    assert len(option) > 1,"Fail to open the application"
    logger.debug("Option in application -- {}".format(output))
    return option

def press_option_in_open_application(options,ops):
    # options = open_application_get_items(app_name,option_sep)
    # ops = options.keys()
    logger.debug("Ops is -- {} type of ops is -- {}".format(ops,type(ops)))
    for op in ops:
        logger.debug("Validating {} option".format(op[0]))
        assert op[0] in options.keys(),"{} not present in the application available options are - {}".format(op[0],options.keys())
        output = execute_command_on_active_shell_and_return_console_output(options[op[0]])
        logger.debug("OUTPUT IS -- {} \n".format(output))
        assert "Call status success" in output,"Call status failed for {}".format(op[0])
        assert op[1] in output,"{} is not found in output".format(op[1])

    # close_shell()

# if __name__ == "__main__":
#     print(press_option_in_open_application("NSMRegularClient",".",[("Get node state","Node state is fullyOperational")]))
