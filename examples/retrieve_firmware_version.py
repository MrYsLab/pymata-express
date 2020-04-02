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

"""
This example retrieves the Firmata version, which consists
of a version number and name of the file.
"""


async def retrieve_firmware_version(my_board):
    """

    :param my_board: pymata_express instance
    :return: the firmware version
    """
    version = await my_board.get_firmware_version()
    print(version)


loop = asyncio.get_event_loop()
board = PymataExpress()
try:
    loop.run_until_complete(retrieve_firmware_version(board))
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
