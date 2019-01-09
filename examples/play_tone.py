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

# retrieve the event loop
loop = asyncio.get_event_loop()

# instantiate pymata express
board = PymataExpress()

try:
    # specify pin, frequency and duration and play tone
    loop.run_until_complete(board.set_pin_mode_tone(3))
    print(loop.run_until_complete(board.get_pin_state(3)))

    loop.run_until_complete(board.play_tone(3, 1000, 500))
    loop.run_until_complete(asyncio.sleep(2))

    # specify pin and frequency and play continuously
    loop.run_until_complete(board.play_tone_continuously(3, 2000))
    loop.run_until_complete(asyncio.sleep(2))
    print(loop.run_until_complete(board.get_pin_state(3)))

    # specify pin to turn pin off
    loop.run_until_complete(board.play_tone_off(3))

    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
