# The PymataExpress Class

To use the PymataExpress class, you must first import it:

```python
from pymata_express import pymata_express
```

and then instantiate it:

```python
board = pymata_express.PymataExpress()
```

The *board* variable contains a reference to the PymataExpress instance. You use this
reference to access the PymataExpress methods of the instance. 

For example, to cleanly shutdown your PymataExpress application, you might call
the *shutdown* method:

```python
board.shutdown()
```

Of course, you can name the instance variable, anything that is meaningful to you.
There is nothing *magic* about the name *board*.


## Understanding The PymataExpress *\__init__* Parameters
```python
def __init__(self, com_port=None, baud_rate=115200,
                 arduino_instance_id=1, arduino_wait=4,
                 sleep_tune=0.0001, autostart=True,
                 loop=None, shutdown_on_exception=True,
                 close_loop_on_shutdown=True,
                 ip_address=None, ip_port=None,
                 ):
        """
        If you are using the Firmata Express Arduino sketch,
        and have a single Arduino connected to your computer,
        then you may accept all the default values.

        If you are using some other Firmata sketch, then
        you must specify both the com_port and baudrate for
        as serial connection, or ip_address and ip_port if
        using StandardFirmataWifi.

        :param com_port: e.g. COM3 or /dev/ttyACM0.

        :param baud_rate: Match this to the Firmata sketch in use.

        :param arduino_instance_id: If you are using the Firmata
                                    Express sketch, match this
                                    value to that in the sketch.

        :param arduino_wait: Amount of time to wait for an Arduino to
                             fully reset itself.

        :param sleep_tune: A tuning parameter (typically not changed by user)

        :param autostart: If you wish to call the start method within
                          your application, then set this to False.

        :param loop: optional user provided event loop

        :param shutdown_on_exception: call shutdown before raising
                                      a RunTimeError exception, or
                                      receiving a KeyboardInterrupt exception

        :param close_loop_on_shutdown: stop and close the event loop loop
                                       when a shutdown is called or a serial
                                       error occurs

        :param ip_address: When interfacing with StandardFirmataWifi, set the
                           IP address of the device.

        :param ip_port: When interfacing with StandardFirmataWifi, set the
                        ip port of the device.
        """
```
There are many optional parameters available when you instantiate PymataExpress. 


If you are using FiramataExpress with a single Arduino, then in most cases, you
 can accept all of the default parameters provided in the \__init__ method.
 
But there are times when you may wish to take advantage of the flexibility provided
by the \__init__ method parameters, so let's explore the definition and purpose
of each parameter:

### The Auto-Discovery Parameters - com_port, baud_rate, and arduino_instance
By accepting the default values for these parameters, pymata-express assumes you have
flashed your Arduino with FirmataExpress. 

### com_port
The *com_port* parameter specifies a serial com_port, such as COM4 or '/dev/ttyACM0'
 used for PC to Arduino communication. If the default value of _None_ is accepted,
 pymata-express will attempt to find the connected Arduino automatically.
 
### baud_rate
The default for this parameter is 115200, matching the speed set in the 
FirmataExpress sketch. If you wish to use StandardFirmata instead of
FirmataExpress, you will set the baud_rate to 57600. If you specify the baud_rate
and accept the default com_port value, pymata-express attempts to find a connected Arduino.

### arduino_instance_id
This parameter is only valid when using FirmataExpress. This parameter
allows pymata-express to connect to an Arduino with a matching ID.

This is useful if you have multiple Arduino's plugged into your computer,
and you wish to have a specific Arduino selected for connection. 

StandardFirmata does not have this capability, and auto-discovery connects to the first
Arduino it finds. This is not always the desired result.

The default value for the arduino_instance_id for both pymata-express and FirmataExpress is 1.

Instructions for changing the FirmataExpress value may be found
in the [**Installing FirmataExpress**](../firmata_express) section of this document.

### arduino_wait
This parameter specifies the amount of time that pymata-express assumes it takes for an Arduino 
to reboot the FirmataExpress (or StandardFirmata) sketch from a power-up or reset.

The default is 4 seconds. If the Arduino is not fully booted when com_port auto-discovery begins,
auto-discovery will fail.

### sleep_tune
This is an asyncio.sleep value expressed in seconds. It is used to yield the asyncio loop 
so that other tasks may run without blocking.
The default value is 0.000001 seconds.

### autostart
If the default of True is accepted, the class will continue with its initialization. There
may be times when you wish to control when that occurs within your application. If set to False,
you may use the non-asyncio *start()* method, or the async version, *start_aio()*.

### loop
If the default of *None* is accepted for this parameter, the default system asyncio event loop is 
used. If you should need to specify your own loop, then this parameter should be set with your custom loop.

### shutdown_on_exception
When this parameter is set to True, the shutdown method is automatically
called when an exception is detected. This disables reporting for both digital and analog pins, 
in addition to closing the serial port.

By setting this parameter to False, the Arduino may continue to send data to
your application even after restarting it.

The default is True and recommended to be used.

### close_loop_on_shutdown
When True (the default) a call to shutdown() will close the event loop.
If set to False, then the event loop is left open.

### ip_address
If you are using StandardFirmataWiFi, set this parameter to the IP address of your WiFi
connected device.

### ip_port
If you are using StandardFirmataWiFi, set this parameter to the IP port of your WiFi
connected device.

### Examples
   1. Each [example on GitHub](https://github.com/MrYsLab/pymata-express/tree/master/examples) 
   demonstrates instantiating the PymataExpress class.
   
   2. A [blink demo](https://github.com/MrYsLab/pymata-express/blob/master/examples/wifi_blink.py) is provided for StandardFirmata WiFi connections.

<br>
<br>

Copyright (C) 2020 Alan Yorinks. All Rights Reserved.
