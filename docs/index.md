<img align="middle" src="./images/pymata_express.png">

<p style="color:#990033; text-align:center; font-family:Georgia; font-size:5em;">Pymata Express</p>
<br>
<br>

<p style="color:#990033; text-align:center; font-family:Georgia; font-size:3.5em;"> The User's Guide</p>


<br>

[Pymata Express](https://github.com/MrYsLab/pymata-express) is a fast and streamlined Firmata client used
to control Arduino micro-controllers
remotely from a Windows, Linux (including Raspberry Pi), or a macOS computer.

It uses the Python 3.7 [asyncio library](https://docs.python.org/3/library/asyncio.html)
to support concurrency (running multiple things simultaneously)
by taking advantage of asyncio tasks, which simplifies program design.

When used with the [FirmataExpress](https://github.com/MrYsLab/FirmataExpress) Arduino sketch,
the serial data rate is 115200 baud, twice the speed of StandardFirmata. FirmataExpress,
based on [StandardFirmata 2.5.8 protocol](https://github.com/firmata/protocol/blob/master/protocol.md),
 adds support for
stepper motors, tone generation, HC-SRO4 distance sensors, and the auto-detection of Arduino boards.

If you prefer to work with StandardFirmata or other slower sketches, Pymata Express is compatible with those
slower versions as well.

Included with the distribution are [full API documentation](https://mryslab.github.io/pymata-express/api/)
and a set of [working examples.](https://github.com/MrYsLab/pymata-express/tree/master/examples)

<br>
<br>


Last updated 10 January 2020 For Release v1.9

Copyright (C) 2019-2020 Alan Yorinks. All Rights Reserved.
