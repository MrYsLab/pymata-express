"""
 Copyright (c) 2018-2019 Alan Yorinks All rights reserved.

 This program is free software; you can redistribute it and/or
 modify it under the terms of the GNU AFFERO GENERAL PUBLIC LICENSE
 Version 3 as published by the Free Software Foundation; either
 or (at your option) any later version.
 This library is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 General Public License for more details.

 You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
 along with this library; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""

import asyncio
import sys
from pymata_express.pymata_express import PymataExpress

# This program continuously monitors an HC-SR04 Ultrasonic Sensor
# It reports changes to the distance sensed.


# A callback function to display the distance
async def the_callback(data):
    """
    The callback function to display the change in distance
    :param data: data[0] = pin number, data[1] = distance
    """
    print("Distance in cm: ", data[1])


async def sonar(my_board, trigger_pin, echo_pin, callback):
    """
    Set the pin mode for a sonar device. Results will appear via the
    callback.

    :param my_board: an pymata express instance
    :param trigger_pin: Arduino pin number
    :param echo_pin: Arduino pin number
    :param callback: The callback function
    """

    # set the pin mode for the trigger and echo pins
    await my_board.set_pin_mode_sonar(trigger_pin, echo_pin,
                                      callback)
    # wait forever
    while True:
        try:
            await asyncio.sleep(.01)
        except KeyboardInterrupt:
            await my_board.shutdown()

loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(sonar(board, 12, 13, the_callback))
    loop.run_until_complete(board.shutdown())
except (KeyboardInterrupt, RuntimeError):
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
