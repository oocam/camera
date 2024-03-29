import os
import json
from logger import logger
from datetime import datetime
from time import sleep
from constants import LOG_FILE

from .ms5837 import MS5837
from .tsys01 import TSYS01_30BA, UNITS_Centigrade
from tsl2561 import TSL2561
from .gps import GPS
from .atlas_sensors import EC_Sensor, DO_Sensor, PH_Sensor

from typing import Dict

# TODO: Additional features need to be added for the new sensors. 20/07/2021
# The new sensors need to compensate for things such as salinity, 
# pressure, temp. Ideally this should be done continuously, but at a
# bare minimum, at least once when initialising.

class Sensor:
    def __init__(self):
        self.luminosity = -1
        self.temperature = -1
        self.pressure = -1
        self.depth = -1
        self.gps_coordinates = {
          "lat": -1,
          "lng": -1
        }
        self.conductivity = -1
        self.total_dissolved_solids = -1
        self.salinity = -1
        self.specific_gravity = -1
        self.dissolved_oxygen = -1
        self.percentage_oxygen = -1
        self.pH = -1

        try:
            self.gps = GPS()
        except Exception as err: 
            logger.error(f"GPS: {err}")
        try:
            self.pressure_sensor = PressureSensor()
        except Exception as err: 
            logger.error(f"Pressure sensor: {err}")
        try:
            self.temperature_sensor = TemperatureSensor() 
        except Exception as err: 
            logger.error(f"Temperature sensor: {err}")
        try:
            self.luminosity_sensor = LuminositySensor() 
        except Exception as err: 
            logger.error(f"Luminosity: {err}")
        try:
            self.ec_sensor = EC_Sensor()
        except Exception as err:
            logger.error(f"Conductivity sensor: {err}")
        try:
            self.do_sensor = DO_Sensor()
        except Exception as err:
            logger.error(f"Dissolved oxygen sensor: {err}")
        try:
            self.ph_sensor = PH_Sensor()
        except Exception as err:
            logger.error(f"pH sensor: {err}")

    def read_sensor_data(self) -> Dict[str, str]:
        """Reads data from all connected sensors.

        Returns:
            A dictionary. Parameters are keys, and values are the
            readings.
        """
        if hasattr(self, 'luminosity_sensor'):
            try:
                self.luminosity = self.luminosity_sensor.luminosity() 
            except LuminositySensorCannotReadException as err: 
                self.luminosity = -1 
                logger.error(f"Error: {err}")
            except Exception as err:
                logger.error(f"Sensor error: {err}")
        else:
            self.luminosity = -1 

        if hasattr(self, 'gps'):
            try:
                self.gps.update()
                if self.gps.has_fix:
                    self.gps_coordinates = {
                      "lat": self.gps.latitude,
                      "lng": self.gps.longitude
                    }
            except Exception as err:
                logger.error(f"GPS not connected: {err}")
        else:
            self.gps_coordinates = {
                  "lat": -1,
                  "lng": -1,
                }
        
        if hasattr(self, 'pressure_sensor'):
            try:
                self.pressure = self.pressure_sensor.absolute_pressure()
                self.temperature = self.pressure_sensor.temperature()
                self.depth = self.pressure_sensor.depth()
            except PressureSensorCannotReadException as err:
                logger.error(f"Error: {err}")
            except Exception as err:
                logger.error(f"Pressure sensor: {err}")
        
        if hasattr(self, 'temperature_sensor'):
            try:
                self.temperature = self.temperature_sensor.temperature()
            except Exception as err:
                logger.error(f"Pressure sensor: {err}")

        # TODO: Repeated _get_data method calls
        # Each of these 'get' methods, is calling _get_data again and again
        # behind the scenes. This is repetitive, and may even be causing errors.
        # This should be changed so that it calls _get_data once, gets a list of 
        # parameters, and then simply parses that list, to get the values for each
        # component.

        if hasattr(self, 'ec_sensor'):
            try:
                self.conductivity = self.ec_sensor.get_conductivity()
            except Exception as err:
                self.conductivity = -1
                logger.error(f"Sensor error: {err}")
            
            try:
                self.total_dissolved_solids = self.ec_sensor.get_tds()
            except Exception as err:
                self.total_dissolved_solids = -1
                logger.error(f"Sensor error: {err}")
            
            try:
                self.salinity = self.ec_sensor.get_salinity()
            except Exception as err:
                self.salinity = -1
                logger.error(f"Sensor error: {err}")
            
            try:
                self.specific_gravity = self.ec_sensor.get_specific_gravity()
            except Exception as err:
                self.specific_gravity = -1
                logger.error(f"Sensor error: {err}")
        
        if hasattr(self, 'do_sensor'):
            try:
                self.dissolved_oxygen = self.do_sensor.get_do()
            except Exception as err:
                self.dissolved_oxygen = -1
                logger.error(f"Sensor error: {err}")
            
            try:
                self.percentage_oxygen = self.do_sensor.get_percent_oxygen()
            except Exception as err:
                self.percentage_oxygen = -1
                logger.error(f"Sensor error: {err}")

        if hasattr(self, 'ph_sensor'):
            try:
                self.pH = self.ph_sensor.get_ph()
            except Exception as err:
                self.pH = -1
                logger.error(f"Sensor error: {err}")

        return {
            "pressure": self.pressure, 
            "temperature": self.temperature,
            "mstemp": self.temperature,
            "depth": self.depth,
            "luminosity": self.luminosity,
            "gps": self.gps_coordinates,
            "conductivity": self.conductivity,
            "total_dissolved_solids": self.total_dissolved_solids,
            "salinity": self.salinity,
            "specific_gravity": self.specific_gravity,
            "dissolved_oxygen": self.dissolved_oxygen,
            "percentage_oxygen": self.percentage_oxygen,
            "pH": self.pH,
        }

    def get_sensor_data(self, short=False) -> Dict[str, str]:
        if short:
            return {
                "p": self.pressure, 
                "t": self.temperature,
                "d": self.depth,
                "l": self.luminosity,
                "g": self.gps_coordinates,
                "c": self.conductivity,
                "s": self.salinity,
                "sg": self.specific_gravity,
                "td": self.total_dissolved_solids,
                "do": self.dissolved_oxygen,
                "po": self.percentage_oxygen,
                "pH": self.pH,
            }
        else:
            return {
                "pressure": self.pressure, 
                "temperature": self.temperature,
                "mstemp": self.temperature,
                "depth": self.depth,
                "luminosity": self.luminosity,
                "gps": self.gps_coordinates,
                "conductivity": self.conductivity,
                "salinity": self.salinity,
                "specific_gravity": self.specific_gravity,
                "total_dissolved_solids": self.total_dissolved_solids,
                "dissolved_oxygen": self.dissolved_oxygen,
                "percentage_oxygen": self.percentage_oxygen,
                "pH": self.pH,
            }

    def write_sensor_data(self, sensor_data_object=None) -> None:
        if os.path.exists(LOG_FILE):
            file_mode = "a"
        else:
            file_mode = "w"
        try:
            self.read_sensor_data()
            sensor_data_object = {
                "pressure": self.pressure,
                "temperature": self.temperature,
                "mstemp": self.temperature,
                "depth": self.depth,
                "luminosity": self.luminosity,
                "gps": self.gps_coordinates,
                "conductivity": self.conductivity,
                "total_dissolved_solids": self.total_dissolved_solids,
                "salinity": self.salinity,
                "specific_gravity": self.specific_gravity,
                "dissolved_oxygen": self.dissolved_oxygen,
                "percentage_oxygen": self.percentage_oxygen,
                "pH": self.pH,
                "timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            }
            sensor_data_json = json.dumps(sensor_data_object)
            with open(LOG_FILE, file_mode) as f:
                f.write(sensor_data_json)
                f.write("\n")
        except Exception as err:
            logger.error(err)
            return None


class PressureSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class PressureSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class PressureSensor(MS5837):
    def __init__(self):
        super().__init__('30BA')
        self.initialize_sensor()


class TemperatureSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class TemperatureSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class TemperatureSensor(TSYS01_30BA):
    def __init__(self, bus=1):
        super().__init__(bus=bus)
        if not super().init():
            logger.warning("TSYS01_30BA may not be connected")
            raise TemperatureSensorNotConnectedException(
                "TSYS01_30BA may not be connected"
            )

    def temperature(self, conversion=UNITS_Centigrade):
        if self.read():
            data = super().temperature(conversion=conversion)
            logger.info(f"Reading temperature data from the sensor: {data}")
            return data
        else:
            raise TemperatureSensorCannotReadException(
                "Could not read temperature values"
            )


class LuminositySensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class LuminositySensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class LuminositySensor(TSL2561):
    def __init__(self):
        try:
            super().__init__()
        except Exception as err:
            logger.warning(f"TSL2561_30BA may not be connected: {err}.")
            raise LuminositySensorNotConnectedException(
                "TSL2561_30BA may not be connected"
            )

    def luminosity(self):
        if self.lux() >= 0:
            data = self.lux()
            logger.info(f"Reading luminosity data from the sensor: {data}")
            return data
        else:
            raise LuminositySensorCannotReadException(
                "Could not read luminosity values"
            )

# TODO : review these classes
class ECSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class ECSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class DOSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class DOSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class PHSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


class PHSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)


if __name__ == "__main__":
    pass
