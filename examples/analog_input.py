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

# Setup a pin for analog input and monitor its changes


async def the_callback(data):
    """
    A callback function to report data changes.

    :param data: [pin, current reported value, pin_mode, timestamp]
    """
    print("analog callback data: ", data[1])


async def analog_in(my_board, pin):
    """
    This function establishes the pin as an
    analog input. Any changes on this pin will
    be reported through the call back function.

    Also, the differential parameter is being used.
    The callback will only be called when there is
    difference of 5 or more between the current and
    last value reported.

    :param my_board: a pymata_express instance
    :param pin: Arduino pin number
    """
    await my_board.set_pin_mode_analog_input(pin,
                                             callback=the_callback,

                                             differential=5)
    # run forever waiting for input changes
    while True:
        await asyncio.sleep(1)

# get the event loop
loop = asyncio.get_event_loop()

# instantiate pymata_express
board = PymataExpress()

try:
    # start the main function
    loop.run_until_complete(analog_in(board, 2))
except (KeyboardInterrupt, RuntimeError) as e:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
