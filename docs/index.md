

<div style="text-align:center;color:#990033; font-family:times, serif; font-size:3.5em"><i>pymata-express</i></div>
<div style="text-align:center;color:#990033; font-family:times, serif; font-size:2em"><i>A User's Guide</i></div>

<br>

# What is pymata-express? 

[Pymata-Express](https://github.com/MrYsLab/pymata-express) is a Python 3 compatible
 (Version 3.7 or above)  [Firmata Protocol](https://github.com/firmata/protocol) 
client that, in conjunction with an Arduino Firmata sketch, permits you to control and monitor Arduino hardware
remotely over a serial link.

Like its conventional sibling [pymata4,](https://mryslab.github.io/pymata4/) pymata4 allows the user to take
advantage of the advanced feature set of 
the [FirmataExpress](https://github.com/MrYsLab/FirmataExpress) (recommended) or StandardFirmata 
Arduino server sketches. 
Unlike pymata4, pymata-express presents a Python [asyncio API.](https://docs.python.org/3/library/asyncio.html) 


## A summary of pymata4's major features:

* Applications are programmed using the Python 3 asyncio package.
* Data change events may be associated with a callback function for asynchronous notification, 
or polling may be used when a synchronous approach is desired.
* Each data change event is time-stamped and stored.
* [API Reference Documentation](https://htmlpreview.github.com/?https://github.com/MrYsLab/pymata-express/blob/master/html/pymata_express/index.html) 
 is available online.
* A full set of working examples
are available for download [online.](https://github.com/MrYsLab/pymata-express/tree/master/examples)


## Advantages of Using The FirmataExpress Sketch Over StandardFirmata:

* The data link runs at 115200, twice the speed of StandardFirmata.
* Advanced Arduino auto-discovery support is provided.
* Additional hardware support is provided for:
    * HC-SR04 ultrasonic distance sensors.
    * Stepper motors.
    * Tone generation for piezo devices.
    

## An Intuitive And Easy To use API

For example, to receive asynchronous digital pin state data change notifications, you simply do the following:

1. Set a pin mode for the pin and register a callback function.
2. Have your application sit in a loop waiting for notifications.
    
When pymata-express executes your callback method, the data parameter will contain
a list of items that describe the change event, including a time-stamp.

Here is an object-oriented example that monitors digital pin 12 for state changes:

```python
import asyncio
import time
import sys
from pymata_express import pymata_express

"""
Setup a pin for digital input and monitor its changes
via callback.
"""

# Setup a pin for analog input and monitor its changes
DIGITAL_PIN = 12  # arduino pin number
WASTE_TIME = .001  # time for the idle loop

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

    # this is the idle loop waiting for data reports
    while True:
        try:
            await asyncio.sleep(POLL_TIME)
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


## What Your Will Find In This Document

* A discussion of the API methods including links to working examples.
* A discussion about the threading model.
* Installation and system requirements:
    * [Verifying The Python 3 Version.](./python_3_verify/#how-to-verify-the-python-3-version-installed) 
    * [Python 3 Installation Instructions.](./python_install/#installing-python-37-or-greater)
    * [Installing _pymata4_.](./install_pymata4/#before-you-install)
    * [Installing FirmataExpress On Your Arduino.](./firmata_express/#installation-instructions)


<br>
<br>

Copyright (C) 2020 Alan Yorinks. All Rights Reserved.

**Last updated 2 April 2020 For Release v1.01**
