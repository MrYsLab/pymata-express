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


async def the_callback(data):
    print("analog callback data: ", data)


async def analog_in(my_board, pin):
    await my_board.set_pin_mode_analog_input(pin,
                                             callback=the_callback,
                                             differential=5)
    # value = await my_board.analog_read(pin)
    # print("analog_input value read: ", value)
    while True:
        await asyncio.sleep(1)


print('Example: analog_input')
loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(analog_in(board, 2))
    loop.run_until_complete(board.shutdown())
except (KeyboardInterrupt, RuntimeError) as e:
    print('exception caught')
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
