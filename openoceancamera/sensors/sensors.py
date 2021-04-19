import os
import json
from logger import logger
from datetime import datetime
from constants import LOG_FILE

from .ms5837 import MS5837
from .tsys01 import TSYS01_30BA, UNITS_Centigrade
from tsl2561 import TSL2561
from .gps import GPS


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
        
    def write_sensor_data(self):
        if os.path.exists(self.log_filename):
            file_mode = "a"
        else:
            file_mode = "w"
        try:
            self.read_sensor_data()
            sensor_data_object = {
                "timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                "luminosity": self.luminosity_data,
                "temp": self.temperature_data,
                "mstemp": self.ms_temperature_data,
                "depth": self.depth,
                "pressure": self.pressure_data,
                "gps": self.coordinates
            }
            sensor_data_json = json.dumps(sensor_data_object)
            with open(self.log_filename, file_mode) as f:
                f.write(sensor_data_json)
                f.write("\n")
        except Exception as err:
            logger.error(err)

    def read_sensor_data(self):
        if hasattr(self, 'luminosity_sensor'):
            try:
                self.luminosity = self.luminosity_sensor.luminosity() 
            except LuminositySensorCannotReadException as err: 
                self.luminosity_data = -1 
                logger.error(f"Error: {err}")
            except Exception as err:
                logger.error(f"Sensor error: {err}")
        else:
            self.luminosity_data = -1 

        if hasattr(self, 'gps'):
            try:
                self.gps.update()
                self.coordinates = {
                  "lat": self.gps.latitude,
                  "lng": self.gps.longitude
                }
            except Exception as err:
                logger.error(f"GPS not connected: {err}")
        else:
            self.coordinates = {
                  "lat": -1,
                  "lng": -1
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
                temperature = self.temperature_sensor.temperature()
            except Exception as err:
                logger.error(f"Pressure sensor: {err}")

        return {
            "pressure": self.pressure, 
            "temperature" : self.temperature, 
            "mstemp": self.temperature,
            "depth": self.depth,
            "luminosity" : self.luminosity,
            "gps": self.gps_coordinates
        }
    

    def get_sensor_data():
        return {
            "pressure": self.pressure, 
            "temperature" : self.temperature, 
            "mstemp": self.temperature,
            "depth": self.depth,
            "luminosity" : self.luminosity,
            "gps": self.gps_coordinates
        }

    def write_sensor_data(self, sensor_data_object=None):
        if os.path.exists(LOG_FILE):
            file_mode = "a"
        else:
            file_mode = "w"
        try:
            sensor_data_object = {
                "pressure": self.pressure, 
                "temperature" : self.temperature, 
                "mstemp": self.temperature,
                "depth": self.depth,
                "luminosity" : self.luminosity,
                "gps": self.gps_coordinates
            }
            sensor_data_object["timestamp"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            sensor_data_json = json.dumps(sensor_data_object)
            with open(LOG_FILE, file_mode) as f:
                f.write(sensor_data_json)
                f.write("\n")
        except Exception as err:
            logger.error(err)
            return None

class PressureSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PressureSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PressureSensor(MS5837):
    def __init__(self):
        super().__init__('30BA')
        self.initialize_sensor()


class TemperatureSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TemperatureSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs):
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LuminositySensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class LuminositySensor(TSL2561):
    def __init__(self):
        try:
            super().__init__()
        except Exception as err:
            logger.warning(f"TSL2561_30BA may not be connected: {err}")
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


def start_sensor_readings(sensors: Sensor):
    while True:
        sensors.read_sensor_data()

if __name__ == "__main__":
    pass
