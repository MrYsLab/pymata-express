

<div style="text-align:center;color:#990033; font-family:times, serif; font-size:3.5em"><i>pymata-express</i></div>
<div style="text-align:center;color:#990033; font-family:times, serif; font-size:2em"><i>A User's Guide</i></div>

<br>

# What is pymata-express? 

[Pymata-Express](https://github.com/MrYsLab/pymata-express) is a Python 3 compatible
 (Version 3.7 or above)  [Firmata Protocol](https://github.com/firmata/protocol) 
client.  When used in conjunction with an Arduino Firmata sketch, it permits you to control and monitor Arduino hardware
remotely over a serial link.

Like its conventional sibling [pymata4,](https://mryslab.github.io/pymata4/) *pymata-express* allows you to take
advantage of the advanced feature set of 
the [FirmataExpress](https://github.com/MrYsLab/FirmataExpress) (recommended) or StandardFirmata 
Arduino server sketches. However, unlike its conventional sibling, pymata-expresses implements its API
utilizing the 
[Python asyncio package](https://docs.python.org/3/library/asyncio.html).


## *Pymata-Express* Major Features:

* Applications are programmed using the Python 3 asyncio package.
* Data change events may be associated with a callback function for asynchronous notification, 
or polling may be used when a synchronous approach is desired.
* Each data change event is time-stamped and stored.
* [API Reference Documentation](https://htmlpreview.github.com/?https://github.com/MrYsLab/pymata-express/blob/master/html/pymata_express/index.html) 
 is available online.
* A full set of working examples
are available for download [online.](https://github.com/MrYsLab/pymata-express/tree/master/examples)
* Supports StandardFirmataWiFi.

## Why Use Asyncio?

You may be wondering why you might consider using pymata-express instead of 
pymata4. Pymata-express tends to execute more quickly than pymata4 and at a lower
CPU utilization rate. 

If you run the 
stress_test.py examples available in both packages, pymata-express completes the task approximately 10% faster
than pymata4 and at a significantly lower CPU utilization rate.

That being said, if you are not already familiar with asyncio, you may find the asyncio learning curve is
rather steep (but worth it, in my opinion). If you are more comfortable with
*traditional* Python programming, then pymata4 may be the better choice.

Both packages have similar APIs, and the set of examples provided in each package parallels the other.
Compare examples to get an understanding of the differences

No matter which package you pick, since the APIs between the two packages are so similar, converting an
application from one API to another should be straight forward. 
 

## Advantages of Using The FirmataExpress Sketch Over StandardFirmata:

* The data link runs at 115200, twice the speed of StandardFirmata.
* Advanced Arduino auto-discovery support is provided.
* Additional hardware support is provided for:
    * HC-SR04 ultrasonic distance sensors.
    * DHT Humidity/Temperature sensors (in collaboration with Martyn Wheeler).
    * Stepper motors.
    * Tone generation for piezo devices.
    

## An Intuitive And Easy To use API

For example, to receive asynchronous digital pin state data change notifications, you simply do the following:

1. Set a pin mode for the pin and register a callback function.
2. Have your application sit in a loop waiting for notifications.
    
When pymata-express executes your callback method, the data parameter will contain
a list of items that describe the change event, including a time-stamp.

Here is an example demonstrating using a callback to monitor
the state changes of a digital input pin.

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


## What You Will Find In This Document

* A discussion of the API methods, including links to working examples.
* A discussion about the asyncio concurrency model.
* Installation and system requirements:
    * [Verifying The Python 3 Version.](../python_3_verify/#how-to-verify-the-python-3-version-installed) 
    * [Python 3 Installation Instructions.](../python_install/#installing-python-37-or-greater)
    * [Installing _pymata-express_.](../install_pymata_express/#before-you-install)
    * [Installing FirmataExpress On Your Arduino.](../firmata_express/#installation-instructions)


<br>
<br>

Copyright (C) 2020 Alan Yorinks. All Rights Reserved.

**Last updated 3 July 2020 For Release v1.18**
