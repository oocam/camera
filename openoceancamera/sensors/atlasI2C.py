#!/usr/bin/python
"""Script with core functionality for Atlas Scientific sensors.

This script contains the AtlasI2C class, which Atlas Scientific
provides on their website. It has since been modified to give it
added functionality.

Note: 
    Code, docstrings, comments and type annotation formatting as
    per Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md#doc-function-args
"""
from abc import abstractmethod, ABC
import io
import sys
import fcntl
import time
import copy
from typing import List, Optional

class AtlasI2C(ABC):
    """An abstract, parent/super class for Atlas Sensors.

    This class functions as a parent/super class for 3 subclasses:
    EC_Sensor, DO_Sensor, and PH_Sensor. It should NOT be instantiated.
    This class has been modified and added to, and is not the same AtlasI2C
    class that is available on the Atlas Scientific website.

    Public Attributes:
        name: str; The name assigned to the sensor.
        module: str; The name of the sensor module/type.
    
    Public Methods:
        query: Writes and reads from device, returns response.
        sleep: Puts device to sleep.
        get_device_info: Gets basic info of sensor (see method docstring for more).
        close: Closes IO streams.
        factory_reset: Resets the device to factory settings.
        list_i2c_devices: Lists addresses of all devices connected to I2C bus.
    
    Example Uses:
        def ChildClassForSpecificSensor(AtlasI2C):
            ...
    """
    _LONG_TIMEOUT = 1.5
    _SHORT_TIMEOUT = .3
    _LONG_TIMEOUT_COMMANDS = ('R', 'CAL')
    _SLEEP_COMMANDS = ('SLEEP',)

    def __init__(self,
                 address: int = 98, 
                 moduletype: str = '', 
                 name: str = '', 
                 bus: int = 1):
        """Initialises sensor with main attributes, and opens read/write file streams.

        Assigns an I2C address, I2C bus, name, and moduletype to the sensor.

        It opens two file streams, one for reading and one for writing.
        The specific I2C channel is selected with bus. It is usually 1,
        except for older versions where its 0. wb and rb indicate binary
        read and write.
        """
        self._address = address
        self._bus = bus
        self._long_timeout = self._LONG_TIMEOUT
        self._short_timeout = self._SHORT_TIMEOUT

        # Opens two IO file streams to read/write to the device with I2C.
        self._file_read = io.open(file=f'/dev/i2c-{self._bus}', 
                                 mode='rb', 
                                 buffering=0)
        self._file_write = io.open(file=f'/dev/i2c-{self._bus}',
                                  mode='wb', 
                                  buffering=0)

        self._set_i2c_address(self._address)    # Sets the I2C address.
        self.name = name
        self.module = moduletype
        print(self.initialise_sensor())
	
    @property
    def long_timeout(self):
        return self._long_timeout

    @property
    def short_timeout(self):
        return self._short_timeout
        
    @property
    def address(self):
        return self._address
        
    @property
    def moduletype(self):
        return self.module
    
    @abstractmethod
    def get_header_row(self):
        """Get the header row for the data file, to show what data is being read."""
        return
    
    def __del__(self):
        try:
            self._file_read.close()
            self._file_write.close()
        except Exception:
            pass
        
    def _set_i2c_address(self, addr: int) -> bool:
        """Sets the I2C address for communications with the slave sensor.

        The commands for I2C dev using the IOCTL functions are 
        specified in the i2c-dev.h file from i2c-tools.
        """
        I2C_SLAVE = 0x703
        fcntl.ioctl(self._file_read, I2C_SLAVE, addr)
        fcntl.ioctl(self._file_write, I2C_SLAVE, addr)
        self._address = addr
        return True

    def _write(self, command: str):   
        """Appends the null character to the command and sends the string over I2C."""
        command += '\00'
        self._file_write.write(command.encode('latin-1'))
    
    def _read(self, num_of_bytes: int = 31) -> str:
        """Reads a specified number of bytes from I2C and parses and displays the result."""
        raw_data = self._file_read.read(num_of_bytes)
        response = self._get_response(raw_data=raw_data)
        is_valid, error_code = self._response_valid(response=response)

        if is_valid:
            char_list = self._handle_raspi_glitch(response[1:])
            result = str(''.join(char_list))
        else:
            result = error_code
        return result
    
    # TODO: remove this method. No longer required.
    def list_i2c_devices(self) -> List[int]:
        """Lists the addresses of all devices connected to I2C bus."""
        prev_addr = copy.deepcopy(self._address)
        i2c_devices = []
        for i in range(0, 128):
            try:
                self._set_i2c_address(i)
                self._read(1)
                i2c_devices.append(i)
            except IOError:
                pass
        self._set_i2c_address(prev_addr)    # Restore the previous address.
        return i2c_devices
            
    def _get_response(self, raw_data):
        if self._app_using_python_two():
            response = [i for i in raw_data if i != '\x00']
        else:
            response = raw_data
        return response

    # TODO: See if this could be useful in logging.
    def get_device_info(self) -> str:
        """Returns a string of basic device information.
        
        Returns:
            A string of device information. The string has the format:
            Module, I2C address, name, last restart cause, current VCC pin voltage.
        """
        # These are the possible reasons for last shutdown of sensor.
        cause_dict = {
            'P': 'powered off',
            'S': 'software reset', 
            'B': 'brown out',
            'W': 'watchdog',
            'U': 'unknown',
        }
        response = self.query('status').split(',')
        key, volt = response[1], response[2]    # Volt is the voltage at the VCC Pin.
        cause = cause_dict[key]
        if self.name == '':
            return f'{self.module} {str(self.address)}\nLast restart cause: {cause}\nVCC pin: {volt}V'
        else:
            return f'{self.module} {str(self.address)} {self.name} \nLast restart cause: {cause}\nVCC pin: {volt}V'
        
    def query(
        self, 
        command: str, 
        num_of_bytes: int = 31) -> str:
        """Writes a command to the sensor, waits correct timeout, and returns the response.

        Args:
            command: str; The command that it writes to the sensor.
            num_of_bytes: int; The number of bytes to be read from the sensor.
        
        Note:
            A complete list of commands can be found in the datasheet of the sensor.
            See class definition of EC_Sensor, PH_Sensor or DO_Sensor, depending on 
            which sensor's commands you want to know more about.

        Returns:
            A string with the response from the sensor.
        """
        self._write(command)
        current_timeout = self._get_command_timeout(command=command)
        if not current_timeout:
            return 'sleep mode'
        else:
            time.sleep(current_timeout)
            return self._read(num_of_bytes)

    def _get_command_timeout(self, command: str) -> Optional[float]:
        """Gets correct timeout for the command that is being sent."""
        timeout = None
        if command.upper().startswith(self._LONG_TIMEOUT_COMMANDS):
            timeout = self._long_timeout
        elif not command.upper().startswith(self._SLEEP_COMMANDS):
            timeout = self._short_timeout
        return timeout

    def factory_reset(self) -> bool:
        """Performs factory reset on sensor, keeps the I2C mode setting.
        
        Returns:
            True if successful, False if not.
        """
        try:
            self.query('r')
            self.query('Factory')
            return True
        except Exception as err:
            print(f'Error: {err}')
            return False

    def _set_cal_data(self) -> bool:
        """Saves the calibration data from the sensor.

        Saves this data to an instance attribute called '_cal_data'.
        """
        try:
            info = self.query('Export,?').split(',')
            num_strings = int(info[1]) 
            self._cal_data = []
            for n in range(num_strings):
                self._cal_data.append((self.query('Export', 12)))
            return True
        except Exception as err:
            print(f'set_cal_data Error: {err}')
            return False
        
    def _import_calibration(self) -> bool:
        """Accesses the saved calibration data and uses it to calibrate the sensor.

        Use cases:

            1) When we calibrate sensors before shipping, we save their calibration
            data. Upon switching the camera on, this saved data is reapplied to
            sensors to ensure that the sensors are still properly calibrated.

            2) If we have multiple sensors of the same kind, calibration data can be
            imported in one go, to all the sensors.
        """
        if hasattr(self,'_cal_data'):
            try:
                for string in self._cal_data:
                    self._write(f'import,{string}')
                print('Sensor calibrated!')
                return True
            except:
                return False
        else:
            print('Error: Calibration data has not been saved yet\n')
            return False
            
    def get_data(self) -> List[str]:
        """Gets the data measurements from the sensor.

        RETURNS: A list of str data measurements.
        """
        raw_data = self.query('r')
        try:
            data = raw_data.split(',')
            return data
        except:
            return [raw_data]    
            # This will only happen with the pH sensor, as it only 
            # returns one parameter.
        
    def sleep(self) -> bool:
        """Puts the sensor in sleep mode for power saving.
        
        The sensor can be woken up with any command.

        Returns: True if successful, False if not.
        """
        try:
            self.query('sleep')
            return True
        except:
            return False
    
    def close(self) -> bool:
        """Closes the I2C IO streams for reading/writing to the sensor."""
        self._file_read.close()
        self._file_write.close()
        return True

    def _handle_raspi_glitch(self, response):
        """
        Changes MSB to 0 for all received characters except the first 
        and gets a list of characters.

        NOTE: Having to change the MSB to 0 is a glitch in the Raspberry Pi, 
        and you shouldn't have to do this!
        """
        if self._app_using_python_two():
            return list(map(lambda x: chr(ord(x) & ~0x80), list(response)))
        else:
            return list(map(lambda x: chr(x & ~0x80), list(response)))

    def _app_using_python_two(self):
        return sys.version_info[0] < 3

    def _response_valid(self, response):
        valid = True
        error_code = None
        if(len(response) > 0):
            
            if self._app_using_python_two():
                error_code = str(ord(response[0]))
            else:
                error_code = str(response[0])
                
            if error_code != '1':
                valid = False
        return valid, error_code

    def initialise_sensor(self) -> bool:
        """Initialise sensor by factory resetting it and calibrating.
        Returns:
            True if successful, False if not.
        """
        try:
            if (not hasattr(self, '_cal_data')):
                self._set_cal_data()
            self.factory_reset()
            self._import_calibration()
            return True
        except:
            return False