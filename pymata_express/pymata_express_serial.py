# -*- coding: utf-8 -*-
"""
 Copyright (c) 2015-2020 Alan Yorinks All rights reserved.

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
import serial
import time

LF = 0x0a


# noinspection PyStatementEffect,PyUnresolvedReferences,PyUnresolvedReferences
class PymataExpressSerial:
    """
    This class encapsulates management of the serial port that communicates
    with the Arduino Firmata
    It provides a 'futures' interface to make Pyserial compatible with asyncio
    """

    def __init__(self, com_port='/dev/ttyACM0', baud_rate=115200, sleep_tune=.001,
                 express_instance=None, close_loop_on_error=True):

        """
        This is the constructor for the aio serial handler

        :param com_port: Com port designator
        :param baud_rate: UART baud rate
        :param express_instance: the pymata-express class instance
        :return: None
        """
        # print('Initializing Arduino - Please wait...', end=" ")
        sys.stdout.flush()
        self.my_serial = serial.Serial(com_port, baud_rate, timeout=1,
                                       writeTimeout=1)

        self.com_port = com_port
        self.sleep_tune = sleep_tune
        self.express_instance = express_instance
        self.close_loop_on_error = close_loop_on_error

        # used by read_until
        self.start_time = None

    async def get_serial(self):
        """
        This method returns a reference to the serial port in case the
        user wants to call pyserial methods directly

        :return: pyserial instance
        """
        return self.my_serial

    async def write(self, data):
        """
        This is an asyncio adapted version of pyserial write. It provides a
        non-blocking  write and returns the number of bytes written upon
        completion

        :param data: Data to be written
        :return: Number of bytes written
        """
        # the secret sauce - it is in your future
        future = asyncio.Future()
        result = None
        try:
            result = self.my_serial.write(bytes([ord(data)]))
        except serial.SerialException:
            # noinspection PyBroadException
            loop = None
            await self.close()
            future.cancel()
            if self.close_loop_on_error:
                loop = asyncio.get_event_loop()
                loop.stop()

            if self.express_instance.the_task:
                self.express_instance.the_task.cancel()
            await asyncio.sleep(1)
            if self.close_loop_on_error:
                loop.close()

        if result:
            future.set_result(result)
            while True:
                if not future.done():
                    # spin our asyncio wheels until future completes
                    await asyncio.sleep(self.sleep_tune)

                else:
                    return future.result()

    async def read(self, size=1):
        """
        This is an asyncio adapted version of pyserial read
        that provides non-blocking read.

        :return: One character
        """

        # create an asyncio Future
        future = asyncio.Future()

        # create a flag to indicate when data becomes available
        data_available = False

        # wait for a character to become available and read from
        # the serial port
        while True:
            if not data_available:
                # test to see if a character is waiting to be read.
                # if not, relinquish control back to the event loop through the
                # short sleep
                if not self.my_serial.in_waiting:
                    await asyncio.sleep(self.sleep_tune*2)

                # data is available.
                # set the flag to true so that the future can "wait" until the
                # read is completed.
                else:
                    data_available = True
                    data = self.my_serial.read(size)
                    # set future result to make the character available
                    if size == 1:
                        future.set_result(ord(data))
                    else:
                        future.set_result(list(data))
            else:
                # wait for the future to complete
                if not future.done():
                    await asyncio.sleep(self.sleep_tune)
                else:
                    # future is done, so return the character
                    return future.result()

    async def read_until(self, expected=LF, size=None, timeout=1):
        """
        This is an asyncio adapted version of pyserial read
        that provides non-blocking read.

        :return: Data delimited by expected
        """

        expected = str(expected).encode()
        # create an asyncio Future
        future = asyncio.Future()

        # create a flag to indicate when data becomes available
        data_available = False

        if timeout:
            self.start_time = time.time()

        # wait for a character to become available and read from
        # the serial port
        while True:
            if not data_available:
                # test to see if a character is waiting to be read.
                # if not, relinquish control back to the event loop through the
                # short sleep
                if not self.my_serial.in_waiting:
                    if timeout:
                        elapsed_time = time.time() - self.start_time
                        if elapsed_time > timeout:
                            return None
                    await asyncio.sleep(self.sleep_tune)
                # data is available.
                # set the flag to true so that the future can "wait" until the
                # read is completed.
                else:
                    data_available = True
                    data = self.my_serial.read_until(expected, size)
                    # set future result to make the character available
                    return_value = list(data)
                    future.set_result(return_value)
            else:
                # wait for the future to complete
                if not future.done():
                    await asyncio.sleep(self.sleep_tune)
                else:
                    # future is done, so return the character
                    return future.result()

    async def reset_input_buffer(self):
        """
        Reset the input buffer
        """
        self.my_serial.reset_input_buffer()

    async def close(self):
        """
        Close the serial port
        """
        if self.my_serial:
            self.my_serial.close()
