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

from pymata_express.pymata_express import PymataExpress


# noinspection PyTypeChecker
class MultiTask:
    """

    This program will run 3 concurrent asyncio tasks:
       1. Blink an LED.
       2. Blink an additional LED at a different rate than the first
       3. Read a potentiometer and set the intensity of a third LED
          scaled to the potentiometer value

    """

    def __init__(self, board):
        """
        Initialize the class
        :param board: a pymata express instance
        """

        # get the event loop
        self.loop = board.get_event_loop()

        # save the PymataExpress instance
        self.board = board

        # establish pin numbers

        # digital pins
        self.white_led = 6
        self.blue_led = 9
        self.green_led = 10

        # analog pin
        self.potentiometer = 2

        # continue with init using an async method
        loop.run_until_complete(self.async_init_and_run())

    async def potentiometer_change_callback(self, data):
        """
        Call back to receive potentiometer changes.
        Scale the reported value between 0 and ~127 to
        control the green led.
        :param data: [pin, current reported value, pin_mode, timestamp]
        """

        scaled_value = data[1] // 4
        await self.board.analog_write(self.green_led, scaled_value)

    async def async_init_and_run(self):
        """
        Initialize pin modes, create tasks and run the tasks
        """

        await self.board.set_pin_mode_digital_output(self.white_led)
        await self.board.set_pin_mode_digital_output(self.blue_led)
        await self.board.set_pin_mode_pwm(self.green_led)
        await self.board.set_pin_mode_analog_input(self.potentiometer,
                                                   self.potentiometer_change_callback)

        # Create the 2 additional tasks
        white_led_task = asyncio.create_task(self.blink_led_1(self.white_led,
                                                              1))
        blue_led_task = asyncio.create_task(self.blink_led_2(self.blue_led,
                                                             .5))
        # start the 2 tasks
        await white_led_task
        await blue_led_task

    async def blink_led_1(self, pin, sleep):
        """
        This is run as a task from async_init_and_run
        :param pin: Arduino Pin Number
        :param sleep: Blink time
        """
        toggle = 0
        while True:
            await self.board.digital_pin_write(pin, toggle)
            await asyncio.sleep(sleep)
            toggle ^= 1

    async def blink_led_2(self, pin, sleep):
        """
        This is run as a task from async_init_and_run
        :param pin: Arduino Pin Number
        :param sleep: Blink time
        """
        toggle = 0
        while True:
            await self.board.digital_pin_write(pin, toggle)
            await asyncio.sleep(sleep)
            toggle ^= 1


# Retrieve the asyncio event loop - used by exception
loop = asyncio.get_event_loop()

# Instantiate PyMataExpress
my_board = PymataExpress()
try:
    # Instantiate this class, passing in the
    # PymataExpress instance.
    MultiTask(my_board)
except (KeyboardInterrupt, RuntimeError):
    # cleanup
    loop.run_until_complete(my_board.shutdown())
    print('goodbye')
