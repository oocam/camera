"""Final classes to control the Atlas sensors connected to OOCAM.

There are three classes in this script: EC_Sensor, DO_Sensor, PH_Sensor.
All three classes are final subclasses that inherit from the super/parent
class - AtlasI2C.
These classes are supposed to be instantiated. They initialise the sensors
and provide whatever functionality is unnique to each sensor.

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
from .atlasI2C import AtlasI2C
import time


class EC_Sensor(AtlasI2C):
    """Final class to control the Atlas Scientific conductivity sensor (EZO-EC).

    This class should be instantiated.
    Official datasheet for this sensor: https://atlas-scientific.com/files/EC_EZO_Datasheet.pdf

    This sensor can measure 4 parameters:
    - Electrical conducitivity (Unit: μS/cm)
    - Total dissolved solids (Unit: ppm)
    - Salinity (Unit: PSU(ppt))
    - Specific gravity (No unit)

    Public Methods:
        set_TDS_conv: Sets the conversion factor for total dissolved solids calculation. 
        get_TDS_conv: Shows the current conversion factor for TDS calculation.
        set_temp_compensation: Sets the temperature in order to compensate for it.
        set_params: Enables/disables measurement parameters.
        set_probe: Sets the type/model of probe.
        get_probe: Shows the probe model that is currently set.
        get_conductivity: Gets the conductivity readings.
        get_salinity: Gets the salinity readings.
        get_tds: Gets the total dissolved solids readings.
        get_salinity: Gets the salinity readings.
    
    Example Use:
        ec_sensor = EC_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        ec_sensor.initialise_sensor()    # To re initialise it if you want.
        
        ec_sensor.get_conductivity()   # Takes readings.
    """
    _PARAMS = ['EC', 'TDS', 'S', 'SG']

    def __init__(self, 
                 address: int = 100, 
                 moduletype: str = 'EC', 
                 name: str = 'Atlas_EC_sensor', 
                 bus: int = 1) -> None:
        """Initialises the sensor and enables all measurement parameters.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        # The .initialise method is called in AtlasI2C __init__ 
        # to initialise the sensors.

        super().__init__(moduletype=moduletype, name=name, address=address, bus=bus)

        for param in self._PARAMS:    # Ensures that all measurement params are enabled.
            self.query(f'O,{param},1')
            time.sleep(2)     # TODO: Test this with no delay, if it works remove line. 21/07/2021

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
    
    def get_conductivity(self) -> float:
        """Explicitly returns the electrical conductivity measurement."""
        try:
            datalist = self.get_data()
            data = datalist[0]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'get_conductivity error: {err}')
            return -1
    
    def get_tds(self) -> float:
        """Explicitly returns the total dissolved solids measurement."""
        try:
            datalist = self.get_data()
            data = datalist[1]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'get_tds error: {err}')
            return -1
    
    def get_salinity(self) -> float:
        """Explicitly returns the salinity measurement."""
        try:
            datalist = self.get_data()
            data = datalist[2]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'get_salinity error: {err}')
            return -1
    
    def get_specific_gravity(self) -> float:
        """Explicitly returns the specific gravity measurement."""
        try:
            datalist = self.get_data()
            data = datalist[3]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'get_specific_gravity error: {err}')
            return -1


class DO_Sensor(AtlasI2C):
    """Final class to control the Atlas Scientific dissolved oxygen sensor (EZO-DO).
    
    This class should be instantiated.
    Official datasheet for this sensor: https://atlas-scientific.com/files/DO_EZO_Datasheet.pdf

    Public Methods:
        set_temp_compensation: Sets the temperature in order to compensate for it.
        set_press_compensation: Sets the pressure in order to compensate for it.
        set_sal_compensation: Sets the salinity in order to compensate for it.
        set_params: Enables/disables measurement parameters.
        get_do: Gets dissolved oxygen readings.
        get_percentage_oxygen: Gets percentage oxygen readings.

    This sensor can measure 2 parameters:
    - Dissolved oxygen (Unit: mg/L)
    - Percentage oxygen (Unit: % saturation)

    Example Use:
        do_sensor = DO_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        do_sensor.initialise_sensor()    # To re initialise it if you want.
        
        do_sensor.get_do()  # Takes readings.
    """
    _PARAMS = ['DO', '%']
    
    def __init__(self, 
                 address: int = 97, 
                 moduletype: str = 'DO', 
                 name: str = 'Atlas_DO_sensor', 
                 bus: int = 1) -> None:
        """Initialises the sensor and enables all measurement parameters.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        # The .initialise method is called in AtlasI2C __init__ 
        # to initialise the sensors.
        super().__init__(address=address, moduletype=moduletype, name=name, bus=bus)

        for param in self._PARAMS:    # Ensures that all measurement parameters are enabled.
            self.query(f'O,{param},1')
            time.sleep(2)

    def get_do(self) -> float:
        """Explicitly returns the dissolved oxygen measurement."""
        try:
            datalist = self.get_data()
            data = datalist[0]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'get_do error: {err}')
            return -1
        
    def get_percent_oxygen(self) -> float:
        """Explicitly returns the percentage oxygen measurement."""
        try:
            datalist = self.get_data()
            data = datalist[1]
            if data.endswith('\x00'):
                data = data.rstrip('\x00')
                return float(data)
            else:
                return float(data)
        except Exception as err:
            print(f'po read error: {err}')
            return -1
    
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

    This sensor can measure one parameter: 
    - pH (Unit: pH)

    Public Methods:
        set_temp_compensation: Sets the temperature in order to compensate for it.
        get_slope: Shows how well the probe is working compared to an ideal probe.
        get_ph: Gets pH readings.
    
    Example Use:
        ph_sensor = PH_Sensor()    # Sets up the class for the sensor, it automatically gets initialised.
        ph_sensor.initialise_sensor()    # To re initialise it if you want.
        
        ph_sensor.get_ph()   # Takes readings.
    """
    # Only reads pH, so no _PARAMS or _UNITS class attributes.
    def __init__(self,
                 moduletype: str = 'pH', 
                 name: str = 'Atlas_pH_sensor', 
                 bus: int = 1, 
                 address: int = 99) -> None:
        """Initialises the sensor.

        See AtlasI2C's (super class) __init__ method for more information.
        """
        # The .initialise method is called in AtlasI2C __init__ 
        # to initialise the sensors.
        super().__init__(moduletype=moduletype, name=name, bus=bus, address=address)
        
    def get_ph(self) -> float:
        """Explicitly returns the pH measurement."""
        try:
            datalist = self.get_data()
            data = datalist[0].rstrip('\x00')
            return float(data)
        except Exception as err:
            print(f'get_ph error: {err}')
            return -1
    
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