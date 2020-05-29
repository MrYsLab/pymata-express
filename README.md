# pymata-express



### A high performance, Python asyncio client for the Arduino Firmata Protocol.
Pymata-Express is a Firmata client that, like its conventional Python sibling,
 [pymata4,](https://mryslab.github.io/pymata4/)
 allows you to control an Arduino using the high-performance FirmataExpress sketch.
  It uses a conventional Python API for those that do not need or wish to use the asyncio programming paradigm of pymata-express.

### It supports both an enhanced version of StandardaFirmata 2.5.8, called FirmataExpress, as well as StandardFirmata and StandardFimataWiFi. 
* **[FirmataExpress](https://github.com/MrYsLab/FirmataExpress) adds support for:**
     * **HC-SR04 Ultrasonic Distance Sensors using a single pin.**
     * **DHT Humidity/Temperature Sensors.** 
     * **Stepper Motors.**
     * **Piezo Tone Generation.**
     * **Baud rate of 115200**
     
## Special Note For FirmataExpress Users:
### pymata-express now verifies the version of FirmataExpress in use.  You may need to upgrade to the latest version of FirmataExpress using the Arduino IDE Library management tool.
     

     
## Special Note For Users Upgrading To Version 1.11
### The callback data format has changed to be consistent with pymata4.


| Callback | Prior To Version 1.11| Version 1.11 And Above |
|---------------------- |--------------|------|
| analog input	| [pin, current reported value, pin_mode, timestamp]| [pin_mode = 2, pin, current reported value, pin_mode, timestamp] 	|
| digital input |[pin, current reported value, pin_mode, timestamp]| [pin_mode = 0, pin, current reported value, pin_mode, timestamp]|	|
| hc-sr04| [pin, distance]	| [pin_mode=12, trigger pin number, distance, timestamp]|
| i2c | [Device address, data bytes] |[pin_mode=6, i2c device address, data bytes, timestamp]|


<h2><u>Major features</u></h2>

* **Fully documented <a href="https://htmlpreview.github.com/?https://github.com/MrYsLab/pymata-express/blob/master/html/pymata_express/index.html" target="_blank">intuitive API</a>**


* **Python 3.7+ compatible.**

* **Set the pin mode and go!**

* **Data change events may be associated with a callback function, or each pin can be polled for its last event change.**

    * **Each data change event is time-stamped and logged.**

* **[User's Guide](https://mryslab.github.io/pymata-express/), Including Examples.**

* **Implements 100% of the StandardFirmata Protocol (StandardFirmata 2.5.8).**

* **Advanced auto-detection of Arduino devices (when using FirmataExpress).**

Here is an example that monitors data changes on a digital input pin. 

```python
import asyncio
import time
import sys
from pymata_express import pymata_express

"""
Setup a pin for digital input and monitor its changes
using a callback.
"""

# Setup a pin for analog input and monitor its changes
DIGITAL_PIN = 12  # arduino pin number
IDLE_TIME = .001  # number of seconds for idle loop to sleep

# Callback data indices
# Callback data indices
CB_PIN_MODE = 0
CB_PIN = 1
CB_VALUE = 2
CB_TIME = 3


async def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the change occurred

    :param data: [pin, current reported value, pin_mode, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[CB_TIME]))
    print(f'Pin: {data[CB_PIN]} Value: {data[CB_VALUE]} Time Stamp: {date}')


async def digital_in(my_board, pin):
    """
     This function establishes the pin as a
     digital input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a pymata_express instance
     :param pin: Arduino pin number
     """

    # set the pin mode
    await my_board.set_pin_mode_digital_input(pin, callback=the_callback)

    while True:
        try:
            await asyncio.sleep(IDLE_TIME)
        except KeyboardInterrupt:
            await board.shutdown()
            sys.exit(0)

# get the event loop
loop = asyncio.get_event_loop()

# instantiate pymata_express
board = pymata_express.PymataExpress()

try:
    # start the main function
    loop.run_until_complete(digital_in(board, 12))
except (KeyboardInterrupt, RuntimeError) as e:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)

```

Sample console output as input change events occur:
```bash
Pin: 12 Value: 0 Time Stamp: 2020-03-10 13:26:22
Pin: 12 Value: 1 Time Stamp: 2020-03-10 13:26:27
```

This project was developed with [Pycharm](https://www.jetbrains.com/pycharm/?from=pymata-express) ![logo](https://github.com/MrYsLab/python_banyan/blob/master/images/icon_PyCharm.png)

