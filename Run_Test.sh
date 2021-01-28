export PYTHONPATH=${PWD}
pytest --alluredir=${WORKSPACE}/allure-result --clean-alluredir ./TestCase/Report.py
python3 ./precondition/precondition.py
cd ${PWD}/TestCase
pytest --alluredir=${WORKSPACE}/allure-result -v "$@"
if [ $? -ne 0 ]
then
    pytest --alluredir=${WORKSPACE}/allure-result --last-failed -v "$@"
fi