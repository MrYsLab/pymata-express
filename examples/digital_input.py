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
import time
from pymata_express.pymata_express import PymataExpress


# Setup a pin for digital input and monitor its changes
# Both polling and callback are being used in this example.

async def the_callback(data):
    """
    A callback function to report data changes.
    This will print the pin number, its reported value and
    the date and time when the change occurred

    :param data: [pin, current reported value, pin_mode, timestamp]
    """
    date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(data[3]))
    print('Pin: {} Value: {} Time Stamp: {}'.format(data[0], data[1], date))


async def digital_in(my_board, pin):
    """
     This function establishes the pin as a
     digital input. Any changes on this pin will
     be reported through the call back function.

     :param my_board: a pymata_express instance
     :param pin: Arduino pin number
     """

    # set the pin mode
    await my_board.set_pin_mode_digital_input(pin, callback=the_callback)

    while True:
        # Do a read of the last value reported every 5 seconds and print it
        # digital_read returns A tuple of last value change and the time that it occurred
        value = await my_board.digital_read(pin)
        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(value[1]))
        # value
        print('Polling - last change: {} at {} '.format(value[0], date))
        await asyncio.sleep(5)


loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(digital_in(board, 13))
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
