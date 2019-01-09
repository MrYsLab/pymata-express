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

# Setup a pin for analog (PWM) output and output
# some different values.


async def set_intensity(my_board, pin):
    """
    This function will set an LED and set it to
    several PWM intensities.

    :param my_board: an PymataExpress instance
    :param pin: pin to be controlled
    """

    # set the pin mode
    print('analog_output example')
    await my_board.set_pin_mode_pwm(pin)

    # set the intensities with analog_write
    print('Maximum Intensity')
    await my_board.analog_write(pin, 255)
    await asyncio.sleep(.5)
    print('Mid Range Intensity')
    await my_board.analog_write(pin, 128)
    await asyncio.sleep(.5)
    print('Off')
    await my_board.analog_write(pin, 0)

loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(set_intensity(board, 9))

    # here we clean up after the program completes.
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)


