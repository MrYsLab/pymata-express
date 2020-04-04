# Analog and Digital Input Pin  Reporting

Callback reporting begins immediately upon setting a pin as either a digital or analog
input pin. If your application should unexpectedly exit without an orderly shutdown,
the Arduino may continue to stream data, even though your application has exited.

In this scenario, if you do not re-power the Arduino before restarting your application,
the continuing data stream may cause pymata-express to fail. The data stream is out
of sync with the pymata-express's state, causing the failure.

One way of making sure that you do not encounter this scenario is to turn off
reporting before exiting your application.


## disable_analog_reporting

```python
 async def disable_analog_reporting(self, pin)

    Disables analog reporting for a single analog pin.

    :param pin: Analog pin number. For example for A0, the number is 0.

```

**Example:**

1. [disable_enable_analog_reporting.py](https://github.com/MrYsLab/pymata-express/blob/master/examples/disable_enable_analog_reporting.py) 

**Notes:**

This method resets the pin mode for the specified pin to a digital input
mode. 


## enable_analog_reporting
```python
 async def enable_analog_reporting(self, pin, callback=None, differential=1)

    Enables analog reporting. This is an alias for set_pin_mode_analog

    :param pin: Analog pin number. For example for A0, the number is 0.

    :param callback: async callback function

    :param differential: This value needs to be met for a callback to be invoked.
```

**Example:**

1. [disable_enable_analog_reporting.py](https://github.com/MrYsLab/pymata-express/blob/master/examples/disable_enable_analog_reporting.py) 

## disable_digital_reporting

```python
 async def disable_digital_reporting(self, pin)

    Disables digital reporting. By turning reporting off for this pin, Reporting is disabled for all 8 bits in the "port"

    :param pin: Pin and all pins for this port
```

**Example:**

1. [disable_enable_digital_reporting.py](https://github.com/MrYsLab/pymata-express/blob/master/examples/disable_enable_digital_reporting.py) 

## enable_digital_reporting

```python
 async def enable_digital_reporting(self, pin)

    Enables digital reporting. By turning reporting on for all 8 bits in the "port" - this is part of Firmata's protocol specification.

    :param pin: Pin and all pins for this port

```
**Example:**

1. [disable_enable_digital_reporting.py](https://github.com/MrYsLab/pymata-express/blob/master/examples/disable_enable_digital_reporting.py) 


<br>
<br>

Copyright (C) 2020 Alan Yorinks. All Rights Reserved.
