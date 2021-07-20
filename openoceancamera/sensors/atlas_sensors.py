"""Final classes to control the Atlas sensors connected to OOCAM.

There are three classes in this script: EC_Sensor, DO_Sensor, PH_Sensor.
All three classes are final subclasses that inherit from the super/parent
class - AtlasI2C.
These classes are supposed to be instantiated. They initialise the sensors
and provide whatever functionality is unnique to each sensor.

There are also two functions in this script, that should be used with 
the sensors:
    getAllSensorData: Gets data from all sensors.
    getAllHeaderRows: Gets headers from all sensors.

Note: 
    Code, docstrings, comments and type annotation formatting as
    per Google Python Style Guide:
    https://github.com/google/styleguide/blob/gh-pages/pyguide.md#doc-function-args

Pinouts:
    For all the sensors, once they are fixed into the electrically isolated
    carrier boards, their pinouts are
    Carrier Board - R Pi
    VCC - 5V or 3.3V
    GND - GND
    VCL - VCL
    VDA - VDA
    OFF - Trim and leave unconnected. 
"""
from os import strerror
from typing import List
from .atlasI2C import AtlasI2C
import time

# TODO:
# 2) see if get header row method needed at all.
# 3) Ask UG about compensation methods and conversion methods etc... How to implement?

class EC_Sensor(AtlasI2C):
    """Final class to control the Atlas Scientific conductivity sensor (EZO-EC).

    This class should be instantiated.
    Official datasheet for this sensor: https://atlas-scientific.com/files/EC_EZO_Datasheet.pdf

    Public Methods:
        get_header_rows: Shows the measurement params and the units for them.
        set_TDS_conv: Sets the conversion factor for total dissolved solids calculation. 
        get_TDS_conv: Shows the current conversion factor for TDS calculation.
        set_temp_compensation: Sets the temperature in order to compensate for it.
        set_params: Enables/disables measurement parameters.
        set_probe: Sets the type/model of probe.
        get_probe: Shows the probe model that is currently set.
    
    Example Use:
        ec_sensor = EC_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        ec_sensor.initialise_sensor()    # To re initialise it if you want.
        
        print(ec_sensor.get_header_rows())    # Shows a header row to start the data file with.
        print(ec_sensor.get_data())   # Takes readings.
    """
    _PARAMS = ['EC', 'TDS', 'SAL', 'SG']
    _UNITS = ['μS/cm', 'ppm', 'PSU(ppt)', 'N/A']

    def __init__(self, 
                 address: int = 100, 
                 moduletype: str = 'EC', 
                 name: str = 'Atlas_EC_sensor', 
                 bus: int = 1):
        """Initialises the sensor and enables all measurement parameters.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        super().__init__(moduletype=moduletype, name=name, address=address, bus=bus)

        # TODO: remove the print statements when the code is fixed.
        print('ec enabling all parameters')
        for param in self._PARAMS:    # Ensures that all measurement params are enabled.
            print(self.query(f'O,{param},1'))
            time.sleep(self._LONG_TIMEOUT)
        print(self.query('O,?'))
        
    def get_header_row(self) -> str:
        """Gets the measurement params and also shows the units for each one.

        To be called before taking readings, as it provides a header/label row 
        for the CSV file of data.

        RETURNS: 
            Header row CSV string for the data file.
            Example: 'EC unit: μS/cm, TDS unit: ppm'
        """
        row = ''
        for n in range(len(self._UNITS)):
            row = row + f'{self._PARAMS[n]} unit: {self._UNITS[n]}, '
        return row

    def set_TDS_conv(self, conv_factor: float = 0.54) -> bool:
        """Set custom conversion factor for the TDS measurement.

        TDS is total dissolved solids, and it's measured like this:
        TDS = EC * conv factor.
        
        Args:
             conv_factor: default value = 0.54. Has to be between 0.01 and 0.95.
        
        Returns:
            True if successful, False if not.
        """        
        if type(conv_factor) == float:
            if (0.01 <= conv_factor <= 1.00):
                response = self.query(f'TDS,{conv_factor}')
                return True
            else:
                print('Conversion factor invalid! Should be between 0.01-1.00.')
                return False
        else:
            print('\nShould be a decimal/floating point number')
            return False

    def get_TDS_conv(self) -> str:
        """Gets the currently set TDS conversion factor (str)."""
        return self.query('TDS,?')

    def set_temp_compensation(self, temp: int = 25) -> str:
        """Sets the temperature and compensates for its effects in the measurements.
        
        If the solution is at a different temperature than 25 C, then compensating
        for this will increase accuracy of readings.

        Args:
            temp: int; Default value = 25 Celcius. Has to be entered in Celcius.
        """
        if type(temp) == float or int:
            response = self.query(f'T,{temp}')
            if temp < 10 or temp > 40:
                print(f'\nNOTE: Unusual ocean temperature set: {temp} C.')
        else:
            print('Temp compensation factor should be a decimal/integer!')
        return response

    def set_probe(self, probe: float = 1.0) -> bool:
        """Sets the type of Atlas EC probe that you have connected to the sensor.

        Args:
            Probe: Either 0.1, 1.0, 10.0; For details on probe types, see datasheet of sensor.
        """
        if probe in [0.1, 1.0, 10.0]:
            print(self.query(f'K,{probe}'))
            print(f'probe value set to {probe}')
            return True
        else:
            print('Error: Value for probe must be 0.1, 1,0 or 10')
            return False
        
    def get_probe(self) -> str:
        """Shows the current probe type/model that is set."""
        return self.query('K,?')

    # # FIXME: This is broken. This may be returning a list with just one item. To check for 
    # this, I have added more print statements.
    
    def get_conductivity(self) -> float:
        """Explicitly returns the electrical conductivity measurement."""
        datalist = self.get_data()
        data = datalist[0]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'conduct read error: {err}')
            print(f'cond data: {datalist}')
            return 69.69
    
    def get_tds(self) -> float:
        """Explicitly returns the total dissolved solids measurement."""
        datalist = self.get_data()
        data = datalist[1]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'tds read error: {err}')
            print(f'tds data: {datalist}')
            return 69.69
    
    def get_salinity(self) -> float:
        """Explicitly returns the salinity measurement."""
        datalist = self.get_data()
        data = datalist[2]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'sal read error: {err}')
            print(f'sal data: {datalist}')
            return 69.69
    
    def get_specific_gravity(self) -> float:
        """Explicitly returns the specific gravity measurement."""
        datalist = self.get_data()
        data = datalist[3]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'sg read error: {err}')
            print(f'sg data: {datalist}')
            return 69.69


class DO_Sensor(AtlasI2C):
    """Final class to control the Atlas Scientific dissolved oxygen sensor (EZO-DO).
    
    This class should be instantiated.
    Official datasheet for this sensor: https://atlas-scientific.com/files/DO_EZO_Datasheet.pdf

    Public Methods:
        get_header_rows: Shows the measurement params and the units for them.
        set_temp_compensation: Sets the temperature in order to compensate for it.
        set_press_compensation: Sets the pressure in order to compensate for it.
        set_sal_compensation: Sets the salinity in order to compensate for it.
        set_params: Enables/disables measurement parameters.
    
    Example Use:
        do_sensor = DO_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        do_sensor.initialise_sensor()    # To re initialise it if you want.
        
        print(do_sensor.get_header_rows())    # Shows a header row to start the data file with.
        print(do_sensor.get_data())   # Takes readings.
    """
    _PARAMS = ['DO', '%']
    _UNITS = ['mg/L', '% sat.']
    
    def __init__(self, 
                 address: int = 97, 
                 moduletype: str = 'DO', 
                 name: str = 'Atlas_DO_sensor', 
                 bus: int = 1):
        """Initialises the sensor and enables all measurement parameters.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        super().__init__(address=address, moduletype=moduletype, name=name, bus=bus)

        print('enabling all parameters for do')
        for param in self._PARAMS:    # Ensures that all measurement parameters are enabled.
            print(self.query(f'O,{param},1'))
        print(self.query('O,?'))
    
    # FIXME: This is broken. This may be returning a list with just one item. To check for 
    # this, I have added more print statements.

    def get_do(self) -> float:
        """Explicitly returns the dissolved oxygen measurement."""
        datalist = self.get_data()
        data = datalist[0]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'do read error: {err}')
            print(f'do data: {datalist}')
            return 69.69
        
    def get_percent_oxygen(self) -> float:
        """Explicitly returns the percentage oxygen measurement."""
        datalist = self.get_data()
        data = datalist[1]
        try:
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'po read error: {err}')
            print(f'po data: {datalist}')
            return 69.69

    def get_header_row(self) -> str:
        """Gets the measurement params and also shows units for each one.

        To be called before taking readings, as it provides a header/label row 
        for the CSV file of data.

        RETURNS: 
            Header row CSV string for the data file.
            Example: 'DO unit: mg/L, % unit: % sat.'
        """
        row = ''
        for n in range(len(self._UNITS)):
            row = row + f'{self._PARAMS[n]} unit: {self._UNITS[n]}, '
        return row
    
    # NOTE: Same response issue as above.

    def set_temp_compensation(self, temp: int = 20) -> str:
        """Sets the temperature and compensates for its effects in the measurements.

        If the solution is at a different temperature than 20 C, then compensating
        for this will increase accuracy of readings.

        Args:
            temp: int; Default value = 20 Celcius. Has to be entered in Celcius.
        """
        response = 'ERROR'
        if type(temp) == float or int:
            response = self.query(f'T,{temp}')
            if temp < 10 or temp > 40:
                response = response + f'\nNOTE: Unusual ocean temperature set: {temp} C.'
        else:
            print('Temp compensation factor should be a decimal/integer!')
        return response
        
    def set_press_compensation(self, press: float = 101.3) -> str:
        """Sets the pressure and compensates for its effects in the measurements.

        If the environment is at a different pressure than 101.3kPa, compensating
        for this will increase accuracy of readings.

        Args:
            press: float; Default value = 101.3kPa. Has to be entered in kPa.
        """
        response = 'ERROR'
        if type(press) == float or int:
            response = self.query(f'P,{press}')
            print(f'Pressure compensation set: {press}')
        else:
            print('Pressure compensation factor should be a decimal/integer!')
        return response

    def set_sal_compensation(self,
                             sal: float = 0.0, 
                             unit: str = 'microsiemens') -> str:
        """Compensates for the effects of ambient salinity.

        If the solution has salinity > 0.0 μS, then compensating for this will
        increase measurement accuracy.

        Args:
            sal: float; Default value = 0.0 μS. Unit should be specified as either
            'microsiemens' or 'ppt'.
        """
        response = 'ERROR'
        if type(sal) == float or int:
            if unit == 'microsiemens':
                response = self.query(f'S,{sal}')
            else:
                response = self.query(f'S,{sal},ppt')
                print(f'Salinity compensation set: {sal}')
                print('note: value was entered in ppt units')
        else:
            print('Salinity compensation factor should be a decimal/integer!')
        return response


class PH_Sensor(AtlasI2C):
    """Final class to control the Atlas Scientific pH sensor (EZO-pH).
    
    This class should be instantiated.
    Official datasheet for this sensor: https://atlas-scientific.com/files/pH_EZO_Datasheet.pdf

    Public Methods:
        get_header_rows: Shows the measurement params and the units for them.
        set_temp_compensation: Sets the temperature in order to compensate for it.
        get_slope: Shows how well the probe is working compared to an ideal probe.
    
    Example Use:
        ph_sensor = PH_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        ph_sensor.initialise_sensor()    # To re initialise it if you want.
        
        print(ph_sensor.get_header_rows())    # Shows a header row to start the data file with.
        print(ph_sensor.get_data())   # Takes readings.
    """
    # Only reads pH, so no _PARAMS or _UNITS class attributes.
    def __init__(self,
                 moduletype: str = 'pH', 
                 name: str = 'Atlas_pH_sensor', 
                 bus: int = 1, 
                 address: int = 99):
        """Initialises the sensor.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        super().__init__(moduletype=moduletype, name=name, bus=bus, address=address)

    def get_ph(self) -> float:
        """Explicitly returns the pH measurement."""
        datalist = self.get_data()
        try:
            data = datalist[0].rstrip('\x00')
            return float(data)
        except Exception as err:
            print(f'ph read error: {err}')
            print(f'ph data: {datalist}')
            return 69.69

    def get_header_row(self) -> str:
        """Gets the measurement param and also shows the unit for it.

        To be called before taking readings, as it provides a header/label row 
        for the CSV file of data.

        RETURNS: 
            'pH unit: pH'
        """
        return 'pH unit: pH'
    
    def set_temp_compensation(self, temp: int = 25) -> str:
        """Compensates for the effects of ambient temperature in the measurements.

        If the solution is at a different temperature than 25 C, then compensating
        for this will increase accuracy of readings.

        Args:
            temp: int; Default value = 25 Celcius. Has to be entered in Celcius.
        """
        response = 'ERROR'
        if type(temp) == float or int:
            response = self.query(f'T,{temp}')
            if temp < 10 or temp > 40:
                response = response + f'\nNOTE: Unusual ocean temperature set: {temp} C.'
        else:
            print('Temp compensation factor should be a decimal/integer!')
        return response

    def get_slope(self) -> str:
        """Shows, in %, how closely the probe is working to an ideal probe.

        Returns:
            A string result. Example: '?Slope,99.7,100.3,-0.89'

            99.7% is how closely the slope of the acid calibration line matched
            the 'ideal' pH probe.
            100.3% is how closely the slope of the base calibration matches the
            'ideal' pH probe.
            The last term is how many millivolts the zero point is off from true 0.
        """
        return self.query('slope,?')

if __name__ == '__main__':
    pass