"""
 Copyright (c) 2020 Alan Yorinks All rights reserved.

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


# This example manipulates a PWM pin and retrieves its pin
# state after each manipulation


async def retrieve_pin_state(my_board):
    """
    Establish a pin as a PWM pin. Set its value
    to 127 and get the pin state. Then set the pin's
    value to zero and get the pin state again.

    :param my_board: pymata_aio instance
    :return: No values returned by results are printed to console
    """
    await my_board.set_pin_mode_pwm(9)
    await my_board.analog_write(9, 127)
    pin_state = await my_board.get_pin_state(9)
    print('You should see [9, 3, 127] and received: ', pin_state)
    await my_board.analog_write(9, 0)
    pin_state = await my_board.get_pin_state(9)
    print('You should see [9, 3, 0]   and received: ', pin_state)

loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(retrieve_pin_state(board))
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
