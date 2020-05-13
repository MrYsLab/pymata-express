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
This example retrieves the pymata_express version, which consists
of the major and minor version numbers.
"""


async def retrieve_pymata_version(my_board):
    """

    :param my_board: pymata_express instance
    :return: the pymata version
    """
    print(await my_board.get_pymata_version())


loop = asyncio.get_event_loop()
board = pymata_express.PymataExpress()
try:
    loop.run_until_complete(retrieve_pymata_version(board))
    loop.run_until_complete(board.shutdown())
except KeyboardInterrupt:
    loop.run_until_complete(board.shutdown())
    sys.exit(0)
