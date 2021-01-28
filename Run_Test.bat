RD /S /Q %WORKSPACE%\allure-result
set PYTHONPATH=%PYTHONPATH%;%cd%;
REM call python .\precondition\Precondition.py
call pytest --alluredir=%WORKSPACE%\allure-result .\TestCase\Report.py
cd %cd%\TestCase
call pytest --alluredir=%WORKSPACE%\allure-result -v %*
IF %ERRORLEVEL% NEQ 0 (
call python -c "from interface.utils import *;restart()"
call pytest --alluredir=%WORKSPACE%\allure-result --last-failed -v %*
)