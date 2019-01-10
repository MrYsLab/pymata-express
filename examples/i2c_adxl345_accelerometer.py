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


# This example sets up and control an ADXL345 i2c
# accelerometer. It will continuously print data
# the raw xyz data from the device.

# the call back function to print the adxl345 data
async def the_callback(data):
    """

    :param data: [Device address, x data pair, y data pair, z data pair]
    :return:
    """
    print(data)


async def adxl345(my_board):
    # setup adxl345
    # device address = 83
    await my_board.set_pin_mode_i2c()

    # set up power and control register
    await my_board.i2c_write(83, [45, 0])
    await asyncio.sleep(.1)
    await my_board.i2c_write(83, [45, 8])
    await asyncio.sleep(.1)

    # set up the data format register
    await my_board.i2c_write(83, [49, 8])
    await asyncio.sleep(.1)
    await my_board.i2c_write(83, [49, 3])
    await asyncio.sleep(1)

    while True:
        # read 6 bytes from the data register
        await my_board.i2c_read(83, 50, 6, the_callback)
        await asyncio.sleep(.2)


loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(adxl345(board))
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
