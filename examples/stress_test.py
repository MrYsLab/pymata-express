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
import time

from pymata_express import pymata_express


# This example attempts to provide some system stress
# to compare performance with pymata4

async def the_callback(data):
    print(data)


async def stress_test(my_board, loop_count, the_loop):
    print(f'Iterating {loop_count} times.')

    await my_board.set_pin_mode_digital_input(12, callback=the_callback)
    await my_board.set_pin_mode_digital_input(13, callback=the_callback)
    await my_board.set_pin_mode_analog_input(2, callback=the_callback, differential=5)
    await my_board.set_pin_mode_pwm_output(9)
    await my_board.set_pin_mode_digital_output(6)

    start_time = the_loop.time()

    for x in range(loop_count):
        await my_board.digital_pin_write(6, 1)
        await my_board.pwm_write(9, 255)
        await my_board.analog_read(2)
        await my_board.digital_pin_write(6, 0)
        await my_board.pwm_write(9, 0)
        await my_board.digital_read(13)

    print(f'Execution time: {the_loop.time() - start_time} seconds for {loop_count} iterations.')

loop = asyncio.get_event_loop()
board = pymata_express.PymataExpress()
try:
    loop.run_until_complete(stress_test(board, 10000, loop))
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)

