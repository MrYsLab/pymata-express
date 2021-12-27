"""
 Copyright (c) 2018-2020 Alan Yorinks All rights reserved.

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
from typing import Any
from typing import Callable
from typing import Dict
from typing import List

# noinspection PyPackageRequirementscd
from serial.serialutil import SerialException
# noinspection PyPackageRequirements
from serial.tools import list_ports

from pymata_express.pin_data import PinData
from pymata_express.private_constants import PrivateConstants
from pymata_express.pymata_express_serial import PymataExpressSerial
from pymata_express.pymata_express_socket import PymataExpressSocket


class PymataExpress:
    """
    This class exposes and implements the PymataExpress API.
    It includes the public API methods as well as
    a set of private methods. This is an asyncio API

    """

    # noinspection PyPep8,PyPep8
    def __init__(self, com_port=None, baud_rate=115200,
                 arduino_instance_id=1, arduino_wait=4,
                 sleep_tune=0.0001, autostart=True,
                 loop=None, shutdown_on_exception=True,
                 close_loop_on_shutdown=True,
                 ip_address=None, ip_port=None,
                 ):
        """
        If you are using the Firmata Express Arduino sketch,
        and have a single Arduino connected to your computer,
        then you may accept all the default values.

        If you are using some other Firmata sketch, then
        you must specify both the com_port and baudrate for
        as serial connection, or ip_address and ip_port if
        using StandardFirmataWifi.

        :param com_port: e.g. COM3 or /dev/ttyACM0.

        :param baud_rate: Match this to the Firmata sketch in use.

        :param arduino_instance_id: If you are using the Firmata
                                    Express sketch, match this
                                    value to that in the sketch.

        :param arduino_wait: Amount of time to wait for an Arduino to
                             fully reset itself.

        :param sleep_tune: A tuning parameter (typically not changed by user)

        :param autostart: If you wish to call the start method within
                          your application, then set this to False.

        :param loop: optional user provided event loop

        :param shutdown_on_exception: call shutdown before raising
                                      a RunTimeError exception, or
                                      receiving a KeyboardInterrupt exception

        :param close_loop_on_shutdown: stop and close the event loop loop
                                       when a shutdown is called or a serial
                                       error occurs

        :param ip_address: When interfacing with StandardFirmataWifi, set the
                           IP address of the device.

        :param ip_port: When interfacing with StandardFirmataWifi, set the
                        ip port of the device.
        """
        # check to make sure that Python interpreter is version 3.7 or greater
        python_version = sys.version_info[:3]
        if sys.platform == 'win32':
            min_version = (3, 8, 2)
        else:
            min_version = (3, 7, 0)

        for (v, mv) in zip(python_version, min_version):
            if v > mv:  # check if version is strictly greater (major first)
                break
        else:  # still need to check whether there is not exact equality
            if not list(python_version) == list(min_version):
                raise RuntimeError("ERROR: Python {} or greater is "
                                           "required for use of this program".format('.'.join([str(x) for x in min_version])))

        # save input parameters
        self.com_port = com_port
        self.baud_rate = baud_rate
        self.arduino_instance_id = arduino_instance_id
        self.arduino_wait = arduino_wait
        self.sleep_tune = sleep_tune
        self.autostart = autostart
        self.ip_address = ip_address
        self.ip_port = ip_port

        # set the event loop
        if loop is None:
            self.loop = asyncio.get_event_loop()
        else:
            self.loop = loop

        self.shutdown_on_exception = shutdown_on_exception
        self.close_loop_on_shutdown = close_loop_on_shutdown

        # a list of PinData objects - one for each pin segregated by pin type
        # see pin_data.py
        self.analog_pins = []
        self.digital_pins = []

        # serial port in use
        self.serial_port = None

        # reference to tcp/ip socket
        self.sock = None

        # An i2c_map entry consists of a device i2c address as the key, and
        #  the value of the key consists of a dictionary containing 2 entries.
        #  The first entry. 'value' contains the last value reported, and
        # the second, 'callback' contains a reference to a callback function,
        # and the third, a time-stamp
        # For example:
        # {12345: {'value': 23, 'callback': None, time_stamp:None}}
        self.i2c_map = {}

        # The active_sonar_map maps the sonar trigger pin number (the key)
        # to the current data value returned
        # if a callback was specified, it is stored in the map as well.
        # A map entry consists of:
        #   pin: [callback, current_data_returned, time_stamp]
        self.active_sonar_map = {}

        # keep alive variables
        self.keep_alive_interval = []
        self.period = 0
        self.margin = 0
        self.keep_alive_task = None

        # first analog pin number
        self.first_analog_pin = None

        # dht error flag
        self.dht_sensor_error = False

        # a list of pins assigned to DHT devices
        self.dht_list = []

        # SPI read and write requests are recorded here until the SPI
        # reply is received. A request consists of:
        #   spi_request_id: {'callback': callback, 'skip_read': bool}
        self.spi_requests: Dict[int, Dict[str, Any]] = {}

        # Used to associate SPI read/write requests with SPI data replies.
        # Incremented on each read request. Valid range is 0-127.
        self.spi_request_id: int = 0

        # generic asyncio task holder
        self.the_task = None
        self.the_socket_receive_task = None

        # flag to indicate we are in shutdown mode
        self.shutdown_flag = False

        # reference to instant of pymata_express_socket
        self.socket_transport = None

        self.using_firmata_express = False

        # this dictionary for mapping incoming Firmata message types to
        # handlers for the messages
        self.command_dictionary = {PrivateConstants.REPORT_VERSION:
                                       self._report_version,
                                   PrivateConstants.REPORT_FIRMWARE:
                                       self._report_firmware,
                                   PrivateConstants.CAPABILITY_RESPONSE:
                                       self._capability_response,
                                   PrivateConstants.ANALOG_MAPPING_RESPONSE:
                                       self._analog_mapping_response,
                                   PrivateConstants.PIN_STATE_RESPONSE:
                                       self._pin_state_response,
                                   PrivateConstants.STRING_DATA:
                                       self._string_data,
                                   PrivateConstants.ANALOG_MESSAGE:
                                       self._analog_message,
                                   PrivateConstants.DIGITAL_MESSAGE:
                                       self._digital_message,
                                   PrivateConstants.I2C_REPLY:
                                       self._i2c_reply,
                                   PrivateConstants.SONAR_DATA:
                                       self._sonar_data,
                                   PrivateConstants.DHT_DATA:
                                       self._dht_read_response,
                                   PrivateConstants.SPI_DATA:
                                       self._spi_reply,
                                   }

        # report query results are stored in this dictionary
        self.query_reply_data = {PrivateConstants.REPORT_VERSION: '',
                                 PrivateConstants.STRING_DATA: '',
                                 PrivateConstants.REPORT_FIRMWARE: '',
                                 PrivateConstants.CAPABILITY_RESPONSE: None,
                                 PrivateConstants.ANALOG_MAPPING_RESPONSE:
                                     None,
                                 PrivateConstants.PIN_STATE_RESPONSE: None,
                                 PrivateConstants.DHT_DATA: '',
                                 }

        print('{}{}{}'.format('\n', 'Pymata Express Version ' +
                              PrivateConstants.PYMATA_EXPRESS_VERSION,
                              '\nCopyright (c) 2018-2020 Alan Yorinks All '
                              'rights reserved.\n'))

        if autostart:
            self.loop.run_until_complete(self.start_aio())

    async def start_aio(self):
        """
        This method may be called directly, if the autostart
        parameter in __init__ is set to false.

        This method instantiates the serial interface and then performs auto pin
        discovery if using a serial interface, or creates and connects to
        a TCP/IP enabled device running StandardFirmataWiFi.

        Use this method if you wish to start PymataExpress manually from
        an asyncio function.
         """

        # using the serial port
        if not self.ip_address:
            if not self.com_port:
                # user did not specify a com_port
                try:
                    await self._find_arduino()
                except KeyboardInterrupt:
                    if self.shutdown_on_exception:
                        await self.shutdown()
            else:
                # com_port specified - set com_port and baud rate
                try:
                    await self._manual_open()
                except KeyboardInterrupt:
                    if self.shutdown_on_exception:
                        await self.shutdown()

            if self.com_port:
                print('{}{}\n'.format('\nArduino found and connected to ',
                                      self.com_port))

            # no com_port found - raise a runtime exception
            else:
                if self.shutdown_on_exception:
                    await self.shutdown()
                raise RuntimeError('No Arduino Found or User Aborted Program')
        # connect to a wifi enabled device server
        else:
            self.socket_transport = PymataExpressSocket(self.ip_address, self.ip_port,
                                                        self.loop)
            await self.socket_transport.start()
            # self.loop.create_task(self.socket_transport.read())

        # start the command dispatcher loop
        if not self.loop:
            self.loop = asyncio.get_event_loop()
        self.the_task = self.loop.create_task(self._arduino_report_dispatcher())

        # get arduino firmware version and print it
        firmware_version = await self.get_firmware_version()
        if not firmware_version:
            print('*** Firmware Version retrieval timed out. ***')
            print('\nDo you have Arduino connectivity and do you have a ')
            print('Firmata sketch uploaded to the board and are connected')
            print('to the correct serial port.\n')
            print('To see a list of serial ports, type: '
                  '"list_serial_ports" in your console.')
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError
        else:
            if self.using_firmata_express:
                version_number = firmware_version[0:3]
                if version_number != PrivateConstants.FIRMATA_EXPRESS_VERSION:
                    raise RuntimeError(f'You must use FirmataExpress version 1.2. '
                                       f'Version Found = {version_number}')
            print("\nArduino Firmware ID: " + firmware_version)

        # try to get an analog pin map. if it comes back as none - shutdown
        report = await self.get_analog_map()
        if not report:
            print('*** Analog map retrieval timed out. ***')
            print('\nDo you have Arduino connectivity and do you have a '
                  'Firmata sketch uploaded to the board?')
            if self.shutdown_on_exception:
                await self.shutdown()
            raise RuntimeError

        # custom assemble the pin lists
        for pin in report:
            digital_data = PinData()
            self.digital_pins.append(digital_data)
            if pin != PrivateConstants.IGNORE:
                analog_data = PinData()
                self.analog_pins.append(analog_data)

        print('{} {} {} {} {}'.format('Auto-discovery complete. Found',
                                      len(self.digital_pins),
                                      'Digital Pins and',
                                      len(self.analog_pins),
                                      'Analog Pins\n\n'))
        self.first_analog_pin = len(self.digital_pins) - len(self.analog_pins)
        await self.set_sampling_interval(19)

    async def get_event_loop(self):
        """
        Return the currently active asyncio event loop

        :return: Active event loop

        """
        return self.loop

    async def _find_arduino(self):
        """
        This method will search all potential serial ports for an Arduino
        containing a sketch that has a matching arduino_instance_id as
        specified in the input parameters of this class.

        This is used explicitly with the FirmataExpress sketch.
        """

        # a list of serial ports to be checked
        serial_ports = []

        print('Opening all potential serial ports...')
        the_ports_list = list_ports.comports()
        for port in the_ports_list:
            if port.pid is None:
                continue
            # print('\nChecking {}'.format(port.device))
            try:
                self.serial_port = PymataExpressSerial(port.device, self.baud_rate,
                                                       express_instance=self,
                                                       close_loop_on_error=self.close_loop_on_shutdown)
            except SerialException:
                continue
            # create a list of serial ports that we opened
            serial_ports.append(self.serial_port)

            # display to the user
            print('\t' + port.device)

            # clear out any possible data in the input buffer
            await self.serial_port.reset_input_buffer()

        # wait for arduino to reset
        print('\nWaiting {} seconds(arduino_wait) for Arduino devices to '
              'reset...'.format(self.arduino_wait))
        await asyncio.sleep(self.arduino_wait)

        print('\nSearching for an Arduino configured with an arduino_instance = ',
              self.arduino_instance_id)

        for serial_port in serial_ports:
            self.serial_port = serial_port
            # send the "are you there" sysex request to the arduino
            await self._send_sysex(PrivateConstants.ARE_YOU_THERE)

            # wait until the END_SYSEX comes back
            i_am_here = await self.serial_port.read_until(expected=b'\xf7')
            if not i_am_here:
                continue

            # make sure we get back the expected length
            if len(i_am_here) != 4:
                continue

            # convert i_am_here to a list
            i_am_here = list(i_am_here)

            # check sysex command is I_AM_HERE
            if i_am_here[1] != PrivateConstants.I_AM_HERE:
                continue
            else:
                # got an I am here message - is it the correct ID?
                if i_am_here[2] == self.arduino_instance_id:
                    self.com_port = serial_port.com_port
                    self.using_firmata_express = True
                    return

    async def _manual_open(self):
        """
        Com port was specified by the user - try to open up that port

        """
        # if port is not found, a serial exception will be thrown
        print('Opening {} ...'.format(self.com_port))
        self.serial_port = PymataExpressSerial(self.com_port, self.baud_rate,
                                               express_instance=self,
                                               close_loop_on_error=self.close_loop_on_shutdown)

        print('Waiting {} seconds for the Arduino To Reset.'
              .format(self.arduino_wait))
        await asyncio.sleep(self.arduino_wait)
        if self.baud_rate == 115200:
            await self._send_sysex(PrivateConstants.ARE_YOU_THERE)

            # await asyncio.sleep(1)
            # wait until the END_SYSEX comes back
            i_am_here = await self.serial_port.read_until(expected=b'\xf7')

            # convert i_am_here to a list
            i_am_here = list(i_am_here)

            if len(i_am_here) != 4:
                raise RuntimeError('Invalid Arduino ID reply length')

            # check sysex command is I_AM_HERE
            if i_am_here[1] != PrivateConstants.I_AM_HERE:
                raise RuntimeError('Retrieving ID From Arduino Failed.')
            else:
                # got an I am here message - is it the correct ID?
                if i_am_here[2] == self.arduino_instance_id:
                    return
                else:
                    raise RuntimeError('Invalid Arduino identifier retrieved')

    async def analog_read(self, pin):
        """
        Retrieve the last data update for the specified analog pin.

        :param pin: Analog pin number (ex. A2 is specified as 2)

        :returns:  [last value reported, time-stamp]
        """

        return self.analog_pins[pin].current_value, self.analog_pins[pin].event_time

    async def analog_write(self, pin, value):
        """
        This is an alias for PWM_write

        It may be removed in the future.

        Set the selected pin to the specified value.

        :param pin: Analog output pin number

        :param value: Pin value (0 - 0x4000)

        """

        await self.pwm_write(pin, value)

    async def _analog_write_extended(self, pin, data):
        """
        This method will send an extended-data analog write command to the
        selected pin.

        :param pin: 0 - 127

        :param data: 0 - 0xfffff

        :returns: No return value
        """
        analog_data = [pin, data & 0x7f, (data >> 7) & 0x7f,
                       (data >> 14) & 0x7f]
        await self._send_sysex(PrivateConstants.EXTENDED_ANALOG, analog_data)

    async def digital_read(self, pin):
        """
        Retrieve the last data update for the specified digital pin.

        :param pin: Digital pin number

        :returns:  [last value reported, time-stamp]

        """
        return self.digital_pins[pin].current_value, self.digital_pins[pin].event_time

    async def dht_read(self, pin):
        """
        Retrieve the last data update for the specified dht pin.

        :param pin: digital pin number

        :return: list = [humidity, temperature  time_stamp]

        """
        return self.digital_pins[pin].current_value[0], \
               self.digital_pins[pin].current_value[1], \
               self.digital_pins[pin].event_time

    async def digital_pin_write(self, pin, value):
        """
        Set the specified pin to the specified value directly without port manipulation.

        :param pin: arduino pin number

        :param value: pin value

        """

        command = (PrivateConstants.SET_DIGITAL_PIN_VALUE, pin, value)

        await self._send_command(command)

    async def digital_write(self, pin, value):
        """
        Set the specified pin to the specified value.

        :param pin: arduino pin number

        :param value: pin value (1 or 0)

        """
        # The command value is not a fixed value, but needs to be calculated
        # using the pin's port number
        port = pin // 8

        calculated_command = PrivateConstants.DIGITAL_MESSAGE + port
        mask = 1 << (pin % 8)
        # Calculate the value for the pin's position in the port mask
        if value == 1:
            PrivateConstants.DIGITAL_OUTPUT_PORT_PINS[port] |= mask
        else:
            PrivateConstants.DIGITAL_OUTPUT_PORT_PINS[port] &= ~mask

        # Assemble the command
        command = (calculated_command,
                   PrivateConstants.DIGITAL_OUTPUT_PORT_PINS[port] & 0x7f,
                   (PrivateConstants.DIGITAL_OUTPUT_PORT_PINS[port] >> 7)
                   & 0x7f)

        await self._send_command(command)

    async def disable_analog_reporting(self, pin):
        """
        Disables analog reporting for a single analog pin.

        :param pin: Analog pin number. For example for A0, the number is 0.

        """
        pin = pin + self.first_analog_pin
        await self.set_pin_mode_digital_input(pin)

    async def disable_digital_reporting(self, pin):
        """
        Disables digital reporting. By turning reporting off for this pin,
        Reporting is disabled for all 8 bits in the "port"

        :param pin: Pin and all pins for this port

        """
        port = pin // 8
        command = [PrivateConstants.REPORT_DIGITAL + port,
                   PrivateConstants.REPORTING_DISABLE]
        await self._send_command(command)

    async def enable_analog_reporting(self, pin, callback=None, differential=1):
        """
        Enables analog reporting. This is an alias for set_pin_mode_analog

        :param pin: Analog pin number. For example for A0, the number is 0.

        :param callback: async callback function

        :param differential: This value needs to be met for a callback
                             to be invoked.
        """
        await self.set_pin_mode_analog_input(pin, callback, differential)

    async def enable_digital_reporting(self, pin):
        """
        Enables digital reporting. By turning reporting on for all 8 bits
        in the "port" - this is part of Firmata's protocol specification.

        :param pin: Pin and all pins for this port

        :returns: No return value
            """
        port = pin // 8
        command = [PrivateConstants.REPORT_DIGITAL + port,
                   PrivateConstants.REPORTING_ENABLE]
        await self._send_command(command)

    async def get_analog_map(self):
        """
        This method requests a Firmata analog map query and returns the
        results.

        :returns: An analog map response or None if a timeout occurs
        """
        # get the current time to make sure a report is retrieved
        current_time = time.time()

        # if we do not have existing report results, send a Firmata
        # message to request one
        if self.query_reply_data.get(
                PrivateConstants.ANALOG_MAPPING_RESPONSE) is None:
            await self._send_sysex(PrivateConstants.ANALOG_MAPPING_QUERY)
            # wait for the report results to return for 4 seconds
            # if the timer expires, return None
            while self.query_reply_data.get(
                    PrivateConstants.ANALOG_MAPPING_RESPONSE) is None:
                elapsed_time = time.time()
                if elapsed_time - current_time > 4:
                    return None
                await asyncio.sleep(self.sleep_tune)
        return self.query_reply_data.get(
            PrivateConstants.ANALOG_MAPPING_RESPONSE)

    async def get_capability_report(self):
        """
        This method requests and returns a Firmata capability query report

        :returns: A capability report in the form of a list
        """
        if self.query_reply_data.get(
                PrivateConstants.CAPABILITY_RESPONSE) is None:
            await self._send_sysex(PrivateConstants.CAPABILITY_QUERY)
            while self.query_reply_data.get(
                    PrivateConstants.CAPABILITY_RESPONSE) is None:
                await asyncio.sleep(self.sleep_tune)
        return self.query_reply_data.get(PrivateConstants.CAPABILITY_RESPONSE)

    async def get_firmware_version(self):
        """
        This method retrieves the Firmata firmware version

        :returns: Firmata firmware version
        """
        current_time = time.time()
        if self.query_reply_data.get(PrivateConstants.REPORT_FIRMWARE) == '':
            await self._send_sysex(PrivateConstants.REPORT_FIRMWARE)
            while self.query_reply_data.get(
                    PrivateConstants.REPORT_FIRMWARE) == '':
                elapsed_time = time.time()
                if elapsed_time - current_time > 4:
                    return None
                await asyncio.sleep(self.sleep_tune)
        return self.query_reply_data.get(PrivateConstants.REPORT_FIRMWARE)

    async def get_protocol_version(self):
        """
        This method returns the major and minor values for the protocol
        version, i.e. 2.5

        :returns: Firmata protocol version
        """
        if self.query_reply_data.get(PrivateConstants.REPORT_VERSION) == '':
            await self._send_command([PrivateConstants.REPORT_VERSION])
            while self.query_reply_data.get(
                    PrivateConstants.REPORT_VERSION) == '':
                await asyncio.sleep(self.sleep_tune)
        return self.query_reply_data.get(PrivateConstants.REPORT_VERSION)

    async def get_pin_state(self, pin):
        """
        This method retrieves a pin state report for the specified pin.
        Pin modes reported:

        INPUT   = 0x00  # digital input mode

        OUTPUT  = 0x01  # digital output mode

        ANALOG  = 0x02  # analog input mode

        PWM     = 0x03  # digital pin in PWM output mode

        SERVO   = 0x04  # digital pin in Servo output mode

        I2C     = 0x06  # pin included in I2C setup

        STEPPER = 0x08  # digital pin in stepper mode

        PULLUP  = 0x0b  # digital pin in input pullup mode

        SONAR   = 0x0c  # digital pin in SONAR mode

        TONE    = 0x0d  # digital pin in tone mode

        :param pin: Pin of interest

        :returns: pin state report

        """
        # place pin in a list to keep _send_sysex happy
        await self._send_sysex(PrivateConstants.PIN_STATE_QUERY, [pin])
        while self.query_reply_data.get(
                PrivateConstants.PIN_STATE_RESPONSE) is None:
            await asyncio.sleep(self.sleep_tune)
        pin_state_report = self.query_reply_data.get(
            PrivateConstants.PIN_STATE_RESPONSE)
        self.query_reply_data[PrivateConstants.PIN_STATE_RESPONSE] = None
        return pin_state_report

    # noinspection PyMethodMayBeStatic
    async def get_pymata_version(self):
        """
        This method retrieves the PyMata Express version number

        :returns: PyMata Express version number.
        """
        return PrivateConstants.PYMATA_EXPRESS_VERSION

    async def i2c_read_saved_data(self, address):
        """
        This method retrieves cached i2c data to support a polling mode.

        :param address: I2C device address

        :returns data: [raw data returned from i2c device, time-stamp]

        """
        if address in self.i2c_map:
            map_entry = self.i2c_map.get(address)
            data = map_entry.get('value')
            return data
        else:
            return None

    async def i2c_read(self, address, register, number_of_bytes,
                       callback=None):
        """
        Read the specified number of bytes from the specified register for
        the i2c device.


        :param address: i2c device address

        :param register: i2c register (or None if no register selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Optional callback function to report i2c data as a
                   result of read command

        callback returns a data list:

        [pin_type, i2c_device_address, i2c_read_register, data_bytes returned, time_stamp]

        The pin_type for i2c = 6

        """

        await self._i2c_read_request(address, register, number_of_bytes,
                                     PrivateConstants.I2C_READ, callback)

    async def i2c_read_continuous(self, address, register, number_of_bytes,
                                  callback=None):
        """
        Some i2c devices support a continuous streaming data output.
        This command enables that mode for the device that supports
        continuous reads.


        :param address: i2c device address

        :param register: i2c register (or None if no register selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Optional callback function to report i2c data as a
                   result of read command

        callback returns a data list:

        [pin_type, i2c_device_address, i2c_read_register, data_bytes returned, time_stamp]

        The pin_type for i2c = 6

        """

        await self._i2c_read_request(address, register, number_of_bytes,
                                     PrivateConstants.I2C_READ_CONTINUOUSLY,
                                     callback)

    async def i2c_read_restart_transmission(self, address, register,
                                            number_of_bytes,
                                            callback=None):
        """
        Read the specified number of bytes from the specified register for
        the i2c device. This restarts the transmission after the read. It is
        required for some i2c devices such as the MMA8452Q accelerometer.


        :param address: i2c device address

        :param register: i2c register (or None if no register selection is needed)

        :param number_of_bytes: number of bytes to be read

        :param callback: Optional callback function to report i2c data as a
                   result of read command

        callback returns a data list:

        [pin_type, i2c_device_address, i2c_read_register, data_bytes returned, time_stamp]

        The pin_type for i2c = 6

        """

        await self._i2c_read_request(address, register, number_of_bytes,
                                     PrivateConstants.I2C_READ
                                     | PrivateConstants.I2C_END_TX_MASK,
                                     callback)

    async def _i2c_read_request(self, address, register, number_of_bytes, read_type,
                                callback=None):
        """
        This method requests the read of an i2c device. Results are retrieved
        by a call to i2c_get_read_data(). or by callback.

        If a callback method is provided, when data is received from the
        device it will be sent to the callback method.

        Some devices require that transmission be restarted
        (e.g. MMA8452Q accelerometer).

        I2C_READ | I2C_END_TX_MASK values for the read_type in those cases.

        I2C_READ = 0B00001000

        I2C_READ_CONTINUOUSLY = 0B00010000

        I2C_STOP_READING = 0B00011000

        I2C_END_TX_MASK = 0B01000000

        :param address: i2c device address

        :param register: register number (can be set to zero or None)

        :param number_of_bytes: number of bytes expected to be returned

        :param read_type: I2C_READ  or I2C_READ_CONTINUOUSLY. I2C_END_TX_MASK
                          may be OR'ed when required

        :param callback: Optional callback function to report i2c data as a
                   result of read command

        """
        if address not in self.i2c_map:
            self.i2c_map[address] = {'value': None, 'callback': callback}
        if register is not None:
            data = [address, read_type, register & 0x7f, (register >> 7) & 0x7f,
                    number_of_bytes & 0x7f, (number_of_bytes >> 7) & 0x7f]
        else:
            data = [address, read_type,
                    number_of_bytes & 0x7f, (number_of_bytes >> 7) & 0x7f]
        await self._send_sysex(PrivateConstants.I2C_REQUEST, data)

    async def i2c_write(self, address, args):
        """
        Write data to an i2c device.

        :param address: i2c device address

        :param args: A variable number of bytes to be sent to the device
                     passed in as a list

        """
        data = [address, PrivateConstants.I2C_WRITE]
        for item in args:
            item_lsb = item & 0x7f
            data.append(item_lsb)
            item_msb = (item >> 7) & 0x7f
            data.append(item_msb)
        await self._send_sysex(PrivateConstants.I2C_REQUEST, data)

    async def keep_alive(self, period=1, margin=.3):
        """
        This is a FirmataExpress feature.

        Periodically send a keep alive message to the Arduino.

        If the Arduino does not received a keep alive, the Arduino
        will physically reset itself.

        Frequency of keep alive transmission is calculated as follows:
        keep_alive_sent = period - (period * margin)


        :param period: Time period between keepalives. Range is 0-10 seconds.
                       0 disables the keepalive mechanism.

        :param margin: Safety margin to assure keepalives are sent before
                    period expires. Range is 0.1 to 0.9
        """

        self.period = period
        self.margin = margin
        if period < 0:
            period = 0

        # if there is a currently running keep alive task
        # and the the period is 0, kill the task and return
        if period == 0 and self.keep_alive_task:
            self.keep_alive_task.cancel()
            return

        self.keep_alive_interval = period & 0x7f, (period >> 7) & 0x7f
        # if there is no keep alive task, start one
        if not self.keep_alive_task:
            self.keep_alive_task = self.loop.create_task(
                self._send_keep_alive())

    async def play_tone(self, pin_number, frequency, duration):
        """

        This is FirmataExpress feature

        Play a tone at the specified frequency for the specified duration.

        :param pin_number: arduino pin number

        :param frequency: tone frequency in hz

        :param duration: duration in milliseconds

        """
        await self._play_tone(pin_number, PrivateConstants.TONE_TONE, frequency=frequency,
                              duration=duration)

    async def play_tone_continuously(self, pin_number, frequency):
        """

        This is a FirmataExpress feature

        This method plays a tone continuously until play_tone_off is called.

        :param pin_number: arduino pin number

        :param frequency: tone frequency in hz

        """

        await self._play_tone(pin_number, PrivateConstants.TONE_TONE, frequency=frequency,
                              duration=None)

    async def play_tone_off(self, pin_number):
        """
        This is a FirmataExpress Feature

        This method turns tone off for the specified pin.

        :param pin_number: arduino pin number

        """

        await self._play_tone(pin_number, PrivateConstants.TONE_NO_TONE,
                              frequency=None, duration=None)

    async def _play_tone(self, pin, tone_command, frequency, duration):
        """
        This method will call the Tone library for the selected pin.
        It requires FirmataPlus to be loaded onto the arduino

        If the tone command is set to TONE_TONE, then the specified
        tone will be played.

        Else, if the tone command is TONE_NO_TONE, then any currently
        playing tone will be disabled.

        :param pin: arduino pin number

        :param tone_command: Either TONE_TONE, or TONE_NO_TONE

        :param frequency: Frequency of tone

        :param duration: Duration of tone in milliseconds

        """
        # convert the integer values to bytes
        if tone_command == PrivateConstants.TONE_TONE:
            # duration is specified
            if duration:
                data = [tone_command, pin, frequency & 0x7f,
                        (frequency >> 7) & 0x7f,
                        duration & 0x7f, (duration >> 7) & 0x7f]

            else:
                data = [tone_command, pin,
                        frequency & 0x7f, (frequency >> 7) & 0x7f, 0, 0]
        # turn off tone
        else:
            data = [tone_command, pin]
        await self._send_sysex(PrivateConstants.TONE_DATA, data)

    async def pwm_write(self, pin, value):
        """
        This is an alias for PWM_write
        Set the selected pin to the specified value.

        :param pin: PWM pin number

        :param value: Pin value (0 - 0x4000)

        """
        if PrivateConstants.ANALOG_MESSAGE + pin < 0xf0:
            command = [PrivateConstants.ANALOG_MESSAGE + pin, value & 0x7f,
                       (value >> 7) & 0x7f]
            await self._send_command(command)
        else:
            await self._analog_write_extended(pin, value)

    async def send_reset(self):
        """
        Send a Sysex reset command to the arduino

        """
        try:
            await self._send_command([PrivateConstants.SYSTEM_RESET])
        except RuntimeError:
            raise

    async def set_pin_mode_analog_input(self, pin_number, callback=None,
                                        differential=1):
        """
        Set a pin as an analog input.

        :param pin_number: arduino pin number

        :param callback: async callback function

        :param differential: This value needs to be met for a callback
                             to be invoked.

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for analog input pins = 2

        """
        await self._set_pin_mode(pin_number, PrivateConstants.ANALOG,
                                 callback=callback,
                                 differential=differential)

    async def set_pin_mode_dht(self, pin_number, sensor_type=22, differential=.1,
                               callback=None):
        """
        Configure a DHT sensor prior to operation.
        Up to 6 DHT sensors are supported

        :param pin_number: digital pin number on arduino.

        :param sensor_type: type of dht sensor
                            Valid values = DHT11, DHT22,

        :param differential: This value needs to be met for a callback
                             to be invoked.

        :param callback: callback function

        callback: returns a data list:

        [pin_type, pin_number, DHT type, validation flag, humidity value, temperature
        raw_time_stamp]

        The pin_type for DHT input pins = 15

        Validation Flag Values:

            No Errors = 0

            Checksum Error = 1

            Timeout Error = 2

            Invalid Value = 999
        """

        # if the pin is not currently associated with a DHT device
        # initialize it.
        if pin_number not in self.dht_list:
            self.dht_list.append(pin_number)
            self.digital_pins[pin_number].cb = callback
            self.digital_pins[pin_number].current_value = [0, 0]
            self.digital_pins[pin_number].differential = differential
            data = [pin_number, sensor_type]
            await self._send_sysex(PrivateConstants.DHT_CONFIG, data)
        else:
            # allow user to change the differential value
            self.digital_pins[pin_number].differential = differential

    async def set_pin_mode_digital_input(self, pin_number, callback=None):
        """
        Set a pin as a digital input.

        :param pin_number: arduino pin number

        :param callback: async callback function

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for digital input pins = 0

        """
        await self._set_pin_mode(pin_number, PrivateConstants.INPUT, callback)

    async def set_pin_mode_digital_input_pullup(self, pin_number, callback=None):
        """
        Set a pin as a digital input with pullup enabled.

        :param pin_number: arduino pin number

        :param callback: async callback function

        callback returns a data list:

        [pin_type, pin_number, pin_value, raw_time_stamp]

        The pin_type for digital input pins with pullups enabled = 11

        """
        await self._set_pin_mode(pin_number, PrivateConstants.PULLUP, callback)

    async def set_pin_mode_digital_output(self, pin_number):
        """
        Set a pin as a digital output pin.

        :param pin_number: arduino pin number
        """

        await self._set_pin_mode(pin_number, PrivateConstants.OUTPUT)

    # noinspection PyIncorrectDocstring
    async def set_pin_mode_i2c(self, read_delay_time=0):
        """
        Establish the standard Arduino i2c pins for i2c utilization.

        NOTE: THIS METHOD MUST BE CALLED BEFORE ANY I2C REQUEST IS MADE
        This method initializes Firmata for I2c operations.

        :param read_delay_time (in microseconds): an optional parameter,
                                                  default is 0

        """
        data = [read_delay_time & 0x7f, (read_delay_time >> 7) & 0x7f]
        await self._send_sysex(PrivateConstants.I2C_CONFIG, data)

    async def set_pin_mode_pwm(self, pin_number):
        """

        This is an alias for set_pin_mode_pwm_output.

        Set a pin as a pwm (analog output) pin.

        :param pin_number:arduino pin number

        """
        await self.set_pin_mode_pwm_output(pin_number)

    async def set_pin_mode_pwm_output(self, pin_number):
        """
        Set a pin as a pwm (analog output) pin.

        :param pin_number:arduino pin number

        """
        await self._set_pin_mode(pin_number, PrivateConstants.PWM)

    async def set_pin_mode_servo(self, pin, min_pulse=544, max_pulse=2400):
        """
        Configure a pin as a servo pin. Set pulse min, max in microseconds.

        :param pin: Servo Pin.

        :param min_pulse: Min pulse width in microseconds.

        :param max_pulse: Max pulse width in microseconds.

        """
        command = [pin, min_pulse & 0x7f, (min_pulse >> 7) & 0x7f,
                   max_pulse & 0x7f,
                   (max_pulse >> 7) & 0x7f]

        await self._send_sysex(PrivateConstants.SERVO_CONFIG, command)

    async def set_pin_mode_sonar(self, trigger_pin, echo_pin,
                                 callback=None, timeout=80000):
        """
        This is a FirmataExpress feature.

        Configure the pins,ping interval and maximum distance for an HC-SR04
        type device.

        Up to a maximum of 6 SONAR devices is supported.
        If the maximum is exceeded a message is sent to the console and the
        request is ignored.

        NOTE: data is measured in centimeters

        :param trigger_pin: The pin number of for the trigger (transmitter).

        :param echo_pin: The pin number for the received echo.

        :param callback: optional callback function to report sonar data changes

        :param timeout: a tuning parameter. 80000UL equals 80ms.

        callback returns a data list:

        [pin_type, trigger_pin_number, distance_value (in cm), raw_time_stamp]

        The pin_type for sonar pins = 12


        """
        # if there is an entry for the trigger pin in existence,
        # ignore the duplicate request.
        if trigger_pin in self.active_sonar_map:
            return

        timeout_lsb = timeout & 0x7f
        timeout_msb = (timeout >> 7) & 0x7f
        data = [trigger_pin, echo_pin, timeout_lsb,
                timeout_msb]

        await self._set_pin_mode(trigger_pin, PrivateConstants.SONAR,
                                 PrivateConstants.INPUT)
        await self._set_pin_mode(echo_pin, PrivateConstants.SONAR,
                                 PrivateConstants.INPUT)
        # update the ping data map for this pin
        if len(self.active_sonar_map) > 6:
            print('sonar_config: maximum number of devices assigned'
                  ' - ignoring request')
        else:
            self.active_sonar_map[trigger_pin] = [callback, 0, 0]

        await self._send_sysex(PrivateConstants.SONAR_CONFIG, data)

    async def set_pin_mode_stepper(self, steps_per_revolution, stepper_pins):
        """
        This is a FirmataExpress feature.

        Configure stepper motor prior to operation.
        This is a FirmataPlus feature.

        NOTE: Single stepper only. Multiple steppers not supported.

        :param steps_per_revolution: number of steps per motor revolution

        :param stepper_pins: a list of control pin numbers - either 4 or 2

        """
        data = [PrivateConstants.STEPPER_CONFIGURE,
                steps_per_revolution & 0x7f,
                (steps_per_revolution >> 7) & 0x7f]
        for pin in range(len(stepper_pins)):
            data.append(stepper_pins[pin])
        await self._send_sysex(PrivateConstants.STEPPER_DATA, data)

    async def set_pin_mode_tone(self, pin_number):
        """
        This is FirmataExpress feature.

        Set a PWM pin to tone mode.

        :param pin_number: arduino pin number

        """
        command = [PrivateConstants.SET_PIN_MODE, pin_number,
                   PrivateConstants.TONE]
        await self._send_command(command)

    async def set_pin_mode_spi(self, pin_number: int) -> None:
        """
        This is FirmataExpress feature.

        Set an SPI pin to SPI mode.

        :param pin_number: arduino pin number

        """
        command: List[int] = [
            PrivateConstants.SET_PIN_MODE,
            pin_number,
            PrivateConstants.SPI
        ]
        await self._send_command(command)

    async def _set_pin_mode(self, pin_number, pin_state, callback=None,
                            differential=1):
        """
        A private method to set the various pin modes.

        :param pin_number: arduino pin number

        :param pin_state: INPUT/OUTPUT/ANALOG/PWM/PULLUP - for SERVO use
                          servo_config()
                          For DHT   use: set_pin_mode_dht

        :param callback: A reference to an async call back function to be
                         called when pin data value changes

        :param differential: This value needs to be met for a callback
                             to be invoked

        """

        # There is a potential start up race condition when running pymata3.
        # This is a workaround for that race condition
        #
        if not len(self.digital_pins):
            await asyncio.sleep(2)
        if callback:
            if pin_state == PrivateConstants.INPUT:
                self.digital_pins[pin_number].cb = callback
            elif pin_state == PrivateConstants.PULLUP:
                self.digital_pins[pin_number].cb = callback
                self.digital_pins[pin_number].pull_up = True
            elif pin_state == PrivateConstants.ANALOG:
                self.analog_pins[pin_number].cb = callback
                self.analog_pins[pin_number].differential = differential
            else:
                print('{} {}'.format('set_pin_mode: callback ignored for '
                                     'pin state:', pin_state))

        pin_mode = pin_state

        if pin_mode == PrivateConstants.ANALOG:
            pin_number = pin_number + self.first_analog_pin

        command = [PrivateConstants.SET_PIN_MODE, pin_number, pin_mode]
        await self._send_command(command)

        if pin_state == PrivateConstants.INPUT or pin_state == PrivateConstants.PULLUP:
            await self.enable_digital_reporting(pin_number)
        else:
            pass

        await asyncio.sleep(.05)

    async def _send_keep_alive(self):
        """
        This is a the task to continuously send keep alive messages
        """
        while not self.shutdown_flag:
            if self.period:
                await self._send_sysex(PrivateConstants.KEEP_ALIVE,
                                       self.keep_alive_interval)

                # wait the requested amount of time before sending the next
                # keep alive to the Arduino
                await asyncio.sleep(self.period - self.margin)

    async def set_sampling_interval(self, interval):
        """
        This method sends the desired sampling interval to Firmata.

        Note: Standard Firmata  will ignore any interval less than
              10 milliseconds

        :param interval: Integer value for desired sampling interval
                         in milliseconds

        """
        data = [interval & 0x7f, (interval >> 7) & 0x7f]
        await self._send_sysex(PrivateConstants.SAMPLING_INTERVAL, data)

    async def servo_write(self, pin, position):
        """
        This is an alias for pwm_write to set
        the position of a servo that has been
        previously configured using set_pin_mode_servo.

        :param pin: arduino pin number

        :param position: servo position

        """

        await self.pwm_write(pin, position)

    async def shutdown(self):
        """
        This method attempts an orderly shutdown
        If any exceptions are thrown, they are ignored.

        """

        self.shutdown_flag = True

        # stop all reporting - both analog and digital
        for pin in range(len(self.analog_pins)):
            await self.disable_analog_reporting(pin)

        for pin in range(len(self.digital_pins)):
            await self.disable_digital_reporting(pin)

        try:
            if self.close_loop_on_shutdown:
                self.loop.stop()
            await self.send_reset()
            await self.serial_port.reset_input_buffer()
            await self.serial_port.close()
            if self.close_loop_on_shutdown:
                self.loop.close()
        except (RuntimeError, SerialException):
            pass

    async def sonar_read(self, trigger_pin):
        """
        This is a FirmataExpress feature

        Retrieve Ping (HC-SR04 type) data. The data is presented as a
        dictionary.

        The 'key' is the trigger pin specified in sonar_config()
        and the 'data' is the current measured distance (in centimeters)
        for that pin. If there is no data, the value is set to None.

        :param trigger_pin: key into sonar data map

        :returns: [last distance, raw time stamp]
        """

        sonar_pin_entry = self.active_sonar_map.get(trigger_pin)
        return [sonar_pin_entry[1], sonar_pin_entry[2]]
        # value = sonar_pin_entry[1]
        # return value

    async def stepper_write(self, motor_speed, number_of_steps):
        """
        This is a FirmataExpress feature

        Move a stepper motor for the number of steps at the specified speed.
        This is a FirmataPlus feature.

        :param motor_speed: 21 bits of data to set motor speed

        :param number_of_steps: 14 bits for number of steps & direction
                                positive is forward, negative is reverse

        """
        if number_of_steps > 0:
            direction = 1
        else:
            direction = 0
        abs_number_of_steps = abs(number_of_steps)
        data = [PrivateConstants.STEPPER_STEP, motor_speed & 0x7f,
                (motor_speed >> 7) & 0x7f, (motor_speed >> 14) & 0x7f,
                abs_number_of_steps & 0x7f, (abs_number_of_steps >> 7) & 0x7f,
                direction]
        await self._send_sysex(PrivateConstants.STEPPER_DATA, data)

    async def spi_begin(self, device_channel: int) -> None:
        """
        This is a FirmataExpress feature

        Initialize the SPI bus. This function must be called at least once
        before calling any of the other SPI commands.

        :param device_channel: The SPI port to use. Up to 8 SPI ports are
        supported, where each port is identified by its channel number (0-7).

        NOTE: Currently only channel 0 is supported by FirmataExpress
        """
        send_data: List[int] = [
            PrivateConstants.SPI_BEGIN,
            device_channel
        ]
        await self._send_sysex(PrivateConstants.SPI_DATA, send_data)

    async def spi_device_config(self,
                                device_id: int,
                                device_channel: int,
                                data_mode: int,  # TODO: Maybe encapsulate me?
                                bit_order: int,  # TODO: Encapsulate me
                                max_speed: int,
                                word_size: int,  # TODO: Encapsulate me, only 8 bit words supported
                                cs_pin_control: bool,
                                cs_active_state: int,
                                cs_pin: int,
                                ) -> None:
        """
        This is a FirmataExpress feature

        Configure an attached SPI device to initialize it before use.

        :param device_id: The device ID may either be used as a specific
        identifier (Linux) or as an arbitrary identifier (Arduino). Device
        ID values range from 0 to 15 and can be specified separately for
        each SPI channel. The device ID will also be returned with the
        channel for each SPI_REPLY command so that it is clear which device
        the data corresponds to.

        :param device_channel: The SPI port to use. Up to 8 SPI ports are
        supported, where each port is identified by its channel number (0-7).

        :param data_mode: A 2-bit value that specifies the clock polarity
        (CPOL) and clock phase (CPHA). See the table:

            mode | CPOL | CPHA
            -----|------|-----
            0    | 0    | 0
            1    | 0    | 1
            2    | 1    | 0
            3    | 1    | 1

        :param bit_order: 0 for LSB, 1 for MSB (default)

        :param max_speed: The maximum speed of communication with the SPI
        device. For an SPI device rated up to 5 MHz, use 5000000.

        :param word_size: The size of a word in bits. Typically 8-bits
        (default). 0 = Default, 1 = 1 bit, 2 = 2 bits, etc. (limit is TBD)

        :param cs_pin_control: True to enable the chip select pin (default),
        false to disable. Some boards have SPI implementations that handle
        the CS pin automatically (RaspberryPi boards for example).

        :param cs_active_state: 0 to use LOW for the active state of the CS
        pin (typical), 1 to use HIGH for the active state.

        :param cs_pin: The pin to use for chip select (CS). Ignored if CS
        pin control is disabled.
        """
        # (bits 3-6: device_id, bits 0-2: device_channel)
        device_id_channel: int = (device_id << 3) | device_channel

        # (bits 1-2: data_mode (0-3), bit 0: bit_order)
        data_mode_bit_order: int = (data_mode << 1) | bit_order

        max_speed_1: int = max_speed & 0b01111111  # Bits 0-6
        max_speed_2: int = (max_speed >> 7) & 0b01111111  # Bits 7-14
        max_speed_3: int = (max_speed >> 14) & 0b01111111  # Bits 15-21
        max_speed_4: int = (max_speed >> 21) & 0b01111111  # Bits 22-28
        max_speed_5: int = (max_speed >> 28) & 0b00001111  # Bits 29-32

        cs_pin_options: int = 0
        if cs_pin_control:
            cs_pin_options |= (1 << 0)
        if cs_active_state != 0:
            cs_pin_options |= (1 << 1)
        # Bits 2-6: reserved for future options

        send_data: List[int] = [
            PrivateConstants.SPI_DEVICE_CONFIG,
            device_id_channel,
            data_mode_bit_order,
            max_speed_1,
            max_speed_2,
            max_speed_3,
            max_speed_4,
            max_speed_5,
            word_size,
            cs_pin_options,
            cs_pin
        ]
        await self._send_sysex(PrivateConstants.SPI_DEVICE_CONFIG, send_data)

    async def spi_read(self,
                       device_id: int,
                       device_channel: int,
                       deselect_cs_pin: bool,  # TODO: Encapsulate me
                       num_words: int,  # TODO: Change to num bytes
                       data_callback: Callable[[List[Any]], None],
                       ) -> None:
        """
        This is a FirmataExpress feature

        Read data without specifying data to write.

        To read data, a 0 is written for each word to be read. This is
        provided as a convenience, as the same can be accomplished using
        spi_transfer() and sending a 0 for each byte to be read.

        :param device_id: The device ID (see spi_device_config())

        :param device_channel: The device channel (see spi_device_config())

        :param deselect_cs_pin: True to deselect the CS pin (default),
        False to not deselect the CS pin.

        :param num_words: The number of words to read (0-127)

        :param data_callback: A callback to receive the SPI reply data.
        Called with an empty array ([]) if the read fails.
        """
        # (bits 3-6: device_id, bits 0-2: device_channel)
        device_id_channel: int = (device_id << 3) | device_channel

        # Get the next request ID
        next_request_id: int = self.spi_request_id

        # Loop until we find an unused ID
        while (next_request_id + 1) % 128 != self.spi_request_id:
            # Check if request with same ID is already in progress:
            if next_request_id in self.spi_requests:
                # A read request with the ID is already in progress, try
                # the next ID
                next_request_id += 1
                continue

            # Set the callback for when data is returned
            self.spi_requests[next_request_id] = {
                'callback': data_callback,
                'skip_read': False,
            }

            # Send the data
            send_data: List[int] = [
                PrivateConstants.SPI_READ,
                device_id_channel,
                next_request_id,
                deselect_cs_pin,
                num_words
            ]
            await self._send_sysex(PrivateConstants.SPI_DATA, send_data)

            # Calculate the next request ID
            self.spi_request_id = (next_request_id + 1) % 128
        else:
            # No request IDs are available, indicate the read failed with an
            # empty array
            data_callback([])

    async def spi_write(self,
                        device_id: int,
                        device_channel: int,
                        deselect_cs_pin: bool,
                        data: List[int],  # TODO: Change to bytes
                        write_callback: Callable[[bool], None],
                        ) -> None:
        """
        This is a FirmataExpress feature

        Only write data, and ignore any data returned by the SPI device.

        Provided as a convenience. The same can be accomplished using
        spi_transfer() and ignoring the reply.

        :param device_id: The device ID (see spi_device_config())

        :param device_channel: The device channel (see spi_device_config())

        :param deselect_cs_pin: True to deselect the CS pin (default),
        False to not deselect the CS pin.

        :param num_words: The number of words to write (0-127)

        :param data: An array of bytes to write

        :param write_callback: Called with True if the write request
        succeed, False if the write request failed
        """
        # (bits 3-6: device_id, bits 0-2: device_channel)
        device_id_channel: int = (device_id << 3) | device_channel

        data_words: List[int] = data  # TODO: Convert to 7-bit words
        num_words: int = len(data_words)

        # Get the next request ID
        next_request_id: int = self.spi_request_id

        # Loop until we find an unused ID
        while (next_request_id + 1) % 128 != self.spi_request_id:
            # Check if request with same ID is already in progress:
            if next_request_id in self.spi_requests:
                # A read request with the ID is already in progress, try
                # the next ID
                next_request_id += 1
                continue

            # Set the callback for when data is returned
            # Set the callback for when data is returned
            self.spi_requests[next_request_id] = {
                'callback': write_callback,
                'skip_read': True,
            }

            send_data: List[int] = [
                PrivateConstants.SPI_WRITE,
                device_id_channel,
                next_request_id,
                deselect_cs_pin,
                num_words
            ] + data_words
            await self._send_sysex(PrivateConstants.SPI_DATA, send_data)

            # Calculate the next request ID
            self.spi_request_id = (next_request_id + 1) % 128
        else:
            # No request IDs are available, indicate the read failed with an
            # empty array
            write_callback(False)

    async def spi_transfer(self,
                           device_id: int,
                           device_channel: int,
                           deselect_cs_pin: bool,
                           data: List[int],  # TODO: Change to bytes
                           data_callback: Callable[[List[Any]], None],
                           ) -> None:
        """
        This is a FirmataExpress feature

        Write data to the SPI device. For each word written, a word
        is read simultaneously. This is the normal SPI transfer mode.

        Since transport (serial, ethernet, Wi-Fi, etc.) buffers tend to
        be small on microcontroller platforms, it may be necessary to
        send several spi_transfer() commands to complete a single SPI
        transaction. Use the deselect_cs_pin parameter to ensure the
        CS pin is not deselected in between transfer commands until the
        transaction is complete.

        :param device_id: The device ID (see spi_device_config())

        :param device_channel: The device channel (see spi_device_config())

        :param deselect_cs_pin: True to deselect the CS pin (default),
        False to not deselect the CS pin.

        :param data: An array of bytes to write

        :param data_callback: A callback to receive the SPI reply data.
        Called with an empty array ([]) if the read fails.
        """
        # (bits 3-6: device_id, bits 0-2: device_channel)
        device_id_channel: int = (device_id << 3) | device_channel

        data_words: List[int] = data  # TODO: Convert to 7-bit words
        num_words: int = len(data_words)

        # Get the next request ID
        next_request_id: int = self.spi_request_id

        # Loop until we find an unused ID
        while (next_request_id + 1) % 128 != self.spi_request_id:
            # Check if request with same ID is already in progress:
            if next_request_id in self.spi_requests:
                # A read request with the ID is already in progress, try
                # the next ID
                next_request_id += 1
                continue

            # Set the callback for when data is returned
            # Set the callback for when data is returned
            self.spi_requests[next_request_id] = {
                'callback': data_callback,
                'skip_read': False,
            }

            # Send the data
            send_data: List[int] = [
                PrivateConstants.SPI_TRANSFER,
                device_id_channel,
                next_request_id,
                deselect_cs_pin,
                num_words
            ] + data_words
            await self._send_sysex(PrivateConstants.SPI_DATA, send_data)

            # Calculate the next request ID
            self.spi_request_id = (next_request_id + 1) % 128
        else:
            # No request IDs are available, indicate the read failed with an
            # empty array
            data_callback([])

    async def spi_end(self) -> None:
        """
        This is a FirmataExpress feature

        Disable the SPI bus.
        """
        send_data: List[int] = [PrivateConstants.SPI_END]
        await self._send_sysex(PrivateConstants.SPI_DATA, send_data)

    async def _arduino_report_dispatcher(self):
        """
        This is a private method.
        It continually accepts and interprets data coming from Firmata,and then
        dispatches the correct handler to process the data.

        :returns: This method never returns
        """
        # sysex commands are assembled into this list for processing
        sysex = []

        while True:
            if self.shutdown_flag:
                break
            try:
                if not self.ip_address:
                    next_command_byte = await self.serial_port.read()
                else:
                    next_command_byte = await self.socket_transport.read()

            except TypeError:
                continue
            # if this is a SYSEX command, then assemble the entire
            # command process it
            if next_command_byte == PrivateConstants.START_SYSEX:
                while next_command_byte != PrivateConstants.END_SYSEX:
                    if not self.ip_address:
                        next_command_byte = await self.serial_port.read()
                    else:
                        next_command_byte = await self.socket_transport.read()
                    sysex.append(next_command_byte)
                await self.command_dictionary[sysex[0]](sysex)
                sysex = []
            # if this is an analog message, process it.
            elif 0xE0 <= next_command_byte <= 0xEF:
                # analog message
                # assemble the entire analog message in command
                command = []
                # get the pin number for the message
                pin = next_command_byte & 0x0f
                command.append(pin)
                # get the next 2 bytes for the command
                command = await self._wait_for_data(command, 2)
                # process the analog message
                await self._analog_message(command)
            # handle the digital message
            elif 0x90 <= next_command_byte <= 0x9F:
                command = []
                port = next_command_byte & 0x0f
                command.append(port)
                command = await self._wait_for_data(command, 2)
                await self._digital_message(command)
            # handle all other messages by looking them up in the
            # command dictionary
            elif next_command_byte in self.command_dictionary:
                await self.command_dictionary[next_command_byte]()
                await asyncio.sleep(self.sleep_tune)
            else:
                continue

    '''
    Firmata message handlers
    '''

    async def _analog_mapping_response(self, data):
        """
        This is a private message handler method.
        It is a message handler for the analog mapping response message.

        :param data: response data

        """
        self.query_reply_data[PrivateConstants.ANALOG_MAPPING_RESPONSE] = \
            data[1:-1]

    async def _analog_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for analog messages.

        :param data: message data

        """
        pin_type = PrivateConstants.ANALOG
        pin = data[0]
        value = (data[PrivateConstants.MSB] << 7) + data[PrivateConstants.LSB]

        # only report when there is a change in value
        differential = abs(value - self.analog_pins[pin].current_value)
        if differential >= self.analog_pins[pin].differential:
            self.analog_pins[pin].current_value = value
            time_stamp = time.time()
            self.analog_pins[pin].event_time = time_stamp

            # append pin number, pin value, and pin type to return value and return as a list
            message = [pin_type, pin, value, time_stamp]

            if self.analog_pins[pin].cb:
                # if self.analog_pins[pin].cb_type:
                await self.analog_pins[pin].cb(message)

    async def _capability_response(self, data):
        """
        This is a private message handler method.
        It is a message handler for capability report responses.

        :param data: capability report

        """
        self.query_reply_data[PrivateConstants.CAPABILITY_RESPONSE] = data[1:-1]

    async def _dht_read_response(self, data):
        """
        Process the dht response message.

        :param: data: [pin, dht_type, validation_flag,
        humidity_positivity_flag, temperature_positivity_flag, humidity, temperature]
        """

        # get the time of the report
        time_stamp = time.time()

        # adjust data to just show values from sensor
        data = data[1:-1]
        # initiate a list for a potential call back
        reply_data = [PrivateConstants.DHT]

        # get the pin and type of the dht
        pin = data[0]
        reply_data.append(pin)
        dht_type = data[1]
        reply_data.append(dht_type)
        humidity = temperature = 0

        if data[2] == 0:  # all is well
            humidity = float(data[5] + data[6] / 100)
            if data[3]:
                humidity *= -1.0
            temperature = float(data[7] + data[8] / 100)
            if data[4]:
                temperature *= -1.0


        self.digital_pins[pin].event_time = time_stamp
        reply_data.append(data[2])
        reply_data.append(humidity)
        reply_data.append(temperature)
        reply_data.append(time_stamp)

        # retrieve the last reported values
        last_value = self.digital_pins[pin].current_value

        self.digital_pins[pin].current_value = [humidity, temperature]
        if self.digital_pins[pin].cb:
            # only report changes
            # has the humidity changed?
            if last_value[0] != humidity:

                differential = abs(humidity - last_value[0])
                if differential >= self.digital_pins[pin].differential:
                    await self.digital_pins[pin].cb(reply_data)
                return
            if last_value[1] != temperature:
                differential = abs(temperature - last_value[1])
                if differential >= self.digital_pins[pin].differential:
                    await self.digital_pins[pin].cb(reply_data)
                return

    async def _digital_message(self, data):
        """
        This is a private message handler method.
        It is a message handler for Digital Messages.

        :param data: digital message

        """
        port = data[0]
        # noinspection PyPep8,PyPep8
        port_data = (data[PrivateConstants.MSB] << 7) + \
                    data[PrivateConstants.LSB]
        pin = port * 8
        for pin in range(pin, min(pin + 8, len(self.digital_pins))):
            # get pin value
            value = port_data & 0x01

            last_value = self.digital_pins[pin].current_value

            # set the current value in the pin structure
            self.digital_pins[pin].current_value = value
            time_stamp = time.time()
            self.digital_pins[pin].event_time = time_stamp

            # append pin number, pin value, and pin type to return value and return as a list
            # if self.legacy_mode:
            #     message = [pin, value, PrivateConstants.INPUT, time_stamp]
            # else:
            pin_type = PrivateConstants.PULLUP if self.digital_pins[pin].pull_up else PrivateConstants.INPUT

            message = [pin_type, pin, value, time_stamp]

            if last_value != value:
                if self.digital_pins[pin].cb:
                    await self.digital_pins[pin].cb(message)

            port_data >>= 1

    async def _i2c_reply(self, data):
        """
        This is a private message handler method.
        It handles replies to i2c_read requests. It stores the data
        for each i2c device address in a dictionary called i2c_map.
        The data may be retrieved via a polling call to i2c_get_read_data().
        It a callback was specified in pymata.i2c_read, the raw data is sent
        through the callback

        :param data: raw data returned from i2c device

        """
        # remove the start and end sysex commands from the data
        data = data[1:-1]
        reply_data = [PrivateConstants.I2C]
        # reassemble the data from the firmata 2 byte format
        address = (data[0] & 0x7f) + (data[1] << 7)

        # if we have an entry in the i2c_map, proceed
        if address in self.i2c_map:
            # get 2 bytes, combine them and append to reply data list
            for i in range(0, len(data), 2):
                combined_data = (data[i] & 0x7f) + (data[i + 1] << 7)
                reply_data.append(combined_data)

            current_time = time.time()
            reply_data.append(current_time)

            # place the data in the i2c map without storing the address byte or
            #  register byte (returned data only)
            map_entry = self.i2c_map.get(address)
            map_entry['value'] = reply_data[2:]
            map_entry['time_stamp'] = current_time
            self.i2c_map[address] = map_entry
            cb = map_entry.get('callback')
            if cb:
                # send everything, including address and register bytes back
                # to caller
                await cb(reply_data)

    async def _pin_state_response(self, data):
        """
        This is a private message handler method.
        It handles pin state query response messages.

        :param data: Pin state message

        """
        self.query_reply_data[PrivateConstants.PIN_STATE_RESPONSE] = data[1:-1]

    async def _report_firmware(self, sysex_data):
        """
        This is a private message handler method.

        This method handles the sysex 'report firmware' command sent by
        Firmata (0x79).

        It assembles the firmware version by concatenating the major and
        minor version number components and the firmware identifier into
        a string.

        e.g. "2.3 StandardFirmata.ino"

        :param sysex_data: Sysex data sent from Firmata

        """
        # first byte after command is major number
        major = sysex_data[1]
        version_string = str(major)

        # next byte is minor number
        minor = sysex_data[2]

        # append a dot to major number
        version_string += '.'

        # append minor number
        version_string += str(minor)
        # add a space after the major and minor numbers
        version_string += ' '

        # slice the identifier - from the first byte after the minor
        #  number up until, but not including the END_SYSEX byte

        name = sysex_data[3:-1]
        firmware_name_iterator = iter(name)

        # convert each element from two 7-bit bytes into characters, then add each
        # character to the version string
        for e in firmware_name_iterator:
            version_string += chr(e + (next(firmware_name_iterator) << 7))

        # store the value
        self.query_reply_data[PrivateConstants.REPORT_FIRMWARE] = version_string

    async def _report_version(self):
        """
        This is a private message handler method.

        This method reads the following 2 bytes after the report version
        command (0xF9 - non sysex).

        The first byte is the major number and the second byte is the
        minor number.

        """
        # get next two bytes
        if not self.ip_address:
            major = await self.serial_port.read()
        else:
            major = await self.socket_transport.read()
        version_string = str(major)

        if not self.ip_address:
            minor = await self.serial_port.read()
        else:
            minor = await self.socket_transport.read()

        version_string += '.'
        version_string += str(minor)
        self.query_reply_data[PrivateConstants.REPORT_VERSION] = version_string

    async def _sonar_data(self, data):
        """
        This method handles the incoming sonar data message and stores
        the data in the response table.

        :param data: Message data from Firmata

        """

        # strip off sysex start and end
        data = data[1:-1]
        pin_number = data[0]
        val = int((data[PrivateConstants.MSB] << 7) +
                  data[PrivateConstants.LSB])
        reply_data = [PrivateConstants.SONAR]

        sonar_pin_entry = self.active_sonar_map[pin_number]

        if sonar_pin_entry[0] is not None:
            # check if value changed since last reading
            if sonar_pin_entry[1] != val:
                sonar_pin_entry[1] = val
                time_stamp = time.time()
                sonar_pin_entry[2] = time_stamp
                self.active_sonar_map[pin_number] = sonar_pin_entry
                # Do a callback if one is specified in the table
                if sonar_pin_entry[0]:
                    reply_data.append(pin_number)
                    reply_data.append(val)
                    reply_data.append(time_stamp)

                    if sonar_pin_entry[1]:
                        await sonar_pin_entry[0](reply_data)

        # update the data in the table with latest value
        else:
            sonar_pin_entry[1] = val
            self.active_sonar_map[pin_number] = sonar_pin_entry

        await asyncio.sleep(self.sleep_tune)

    async def _spi_reply(self, data):
        """
        This method handles the incoming SPI message and stores the data
        in the response table. SPI messages are received after a read
        request or a transfer command.

        :param data: Message data from Firmata
        """
        # Strip off sysex start and end
        data = data[1:-1]

        # TODO
        request_id = data[0]
        reply_data = [PrivateConstants.SPI]

        # If we have an entry in the SPI request map, proceed
        request_entry = self.spi_read_requests.get(request_id)
        if request_entry is not None:
            callback = request_entry['callback']
            skip_read = request_entry['skip_read']

            # Allow another request to use this ID
            del self.spi_requests[request_id]

            if skip_read:
                # This was a write request, report the result instead
                # of the data
                reply_data.append(True)
            else:
                # Add the combined data to reply data list
                combined_data = []  # TODO
                reply_data.append(combined_data)

            current_time = time.time()
            reply_data.append(current_time)

            # Send everything back to caller
            await callback(reply_data)

    async def _send_command(self, command):
        """
        This is a private utility method.
        The method sends a non-sysex command to Firmata.

        :param command:  command data

        :returns: number of bytes sent
        """
        send_message = ""

        for i in command:
            send_message += chr(i)
        result = None
        if not self.ip_address:
            for data in send_message:
                try:
                    result = await self.serial_port.write(data)
                except AttributeError:
                    raise RuntimeError
        else:
            for data in send_message:
                try:
                    result = await self.socket_transport.write(data)
                except AttributeError:
                    raise RuntimeError

        return result

    async def _send_sysex(self, sysex_command, sysex_data=None):
        """
        This is a private utility method.
        This method sends a sysex command to Firmata.

        :param sysex_command: sysex command

        :param sysex_data: data for command

        """
        if not sysex_data:
            sysex_data = []

        # convert the message command and data to characters
        sysex_message = chr(PrivateConstants.START_SYSEX)
        sysex_message += chr(sysex_command)
        if len(sysex_data):
            for d in sysex_data:
                sysex_message += chr(d)
        sysex_message += chr(PrivateConstants.END_SYSEX)

        if not self.ip_address:
            for data in sysex_message:
                await self.serial_port.write(data)
        else:
            await self.socket_transport.write(sysex_message)
            await asyncio.sleep(.01)

        # noinspection PyMethodMayBeStatic

    # noinspection PyMethodMayBeStatic
    async def _string_data(self, data):
        """
        This is a private message handler method.
        It is the message handler for String data messages that will be
        printed to the console.

        :param data:  message

        """
        reply = ''
        data = data[1:-1]
        for x in data:
            reply_data = x
            if reply_data:
                reply += chr(reply_data)
        print(reply)

    async def _wait_for_data(self, current_command, number_of_bytes):
        """
        This is a private utility method.
        This method accumulates the requested number of bytes and
        then returns the full command

        :param current_command:  command id

        :param number_of_bytes:  how many bytes to wait for

        :returns: command
        """
        while number_of_bytes:
            if not self.ip_address:
                next_command_byte = await self.serial_port.read()
                current_command.append(next_command_byte)
                number_of_bytes -= 1
            else:
                next_command_byte = await self.socket_transport.read()
                current_command.append(next_command_byte)
                number_of_bytes -= 1
        return current_command
