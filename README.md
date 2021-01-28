**First time user?**
1. Software Prerequisite -
   - Install python 3(64-bit) any latest version from --> https://www.python.org/downloads/
   - Include python in environment variable if not done at the time of installation.
   - Install required python packages using
     - `pip install -r requirements.txt`
   - DOIP package need to be install using Whl [file](https://transfer.harman.com/message/D1Pv6Ub3L8UVmtbvBHheGd).
     - `pip install *.whl`
   - To enable dlt logging you should have dlt path added in the environment path variable.
   - To enable IP logging you should have Wireshark installed and added to environment path variable.
   
2. Hardware Prerequisite -
    - PPS (programable power supply)
      - supported 2 models 
        - [SIGLENT](https://siglentna.com/power-supplies/)
        - TMI - Local manufacture in India
    - 4 channel USB relay
    - Relay
    - DUT (Board,FHE,OABR,Harness and other connecting cables)
    
3. Third party licensed software used
   - [VSPE](http://www.eterlogic.com/Products.VSPE.html) - Used in serial log capture

2. Update the config -
   - All the local setup configuration are kept under config folder for Ex- IP address, Power supply IP and port, Relay ID and PIN etc..

**How to Run the test?**
- You can call Run_Test.bat bat file run the test
  - Run_Test.bat test marker module
- For Example -
  - To Run only the L1 Test
    - ### `Run_Test.bat -m L1`
  - To Run only the L1 Test of Diagnostics
    - ### `Run_Test.bat -m L1 -k diagnostics`

**For any project documentation please refer**
- [interface](./doc/interface/index.html)
- [config](./doc/config/index.html)
- [utility](./doc/utility/index.html)
