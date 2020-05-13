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
from pymata_express import pymata_express

"""
This is a demonstration of the tone methods
"""

# instantiate pymata express
TONE_PIN = 3


async def play_tone(my_board):
    try:
        # set a pin's mode for tone operations
        await my_board.set_pin_mode_tone(TONE_PIN)

        # specify pin, frequency and duration and play tone
        await my_board.play_tone(TONE_PIN, 1000, 500)
        await asyncio.sleep(2)

        # specify pin and frequency and play continuously
        await my_board.play_tone_continuously(TONE_PIN, 2000)
        await asyncio.sleep(2)

        # specify pin to turn pin off
        await my_board.play_tone_off(TONE_PIN)

        # clean up
        await my_board.shutdown()
    except KeyboardInterrupt:
        await my_board.shutdown()
        sys.exit(0)


loop = asyncio.get_event_loop()
board = pymata_express.PymataExpress()
try:
    loop.run_until_complete(play_tone(board))
except (KeyboardInterrupt, RuntimeError):
    board.shutdown()
    sys.exit(0)
