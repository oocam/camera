import os
import json
from logger import logger
from datetime import datetime
from constants import LOG_FILE

# sensors_logger = logging.getLogger(__name__)

from .ms5837 import MS5837_30BA, DENSITY_SALTWATER, UNITS_Centigrade, UNITS_mbar
from .tsys01 import TSYS01_30BA, UNITS_Centigrade
from .tsl2561 import TSL2561_30BA
from .gps import GPS


class Sensor:
    def __init__(self):
        super().__init__()
        self.pressure_data = -1
        self.temperature_data = -1
        self.luminosity_data = -1
        self.coordinates = {
          "lat": -1,
          "long": -1
        }
        self.log_filename = LOG_FILE

        try:
            self.gps = GPS()
        except Exception as err: 
            logger.error(f"Sensor Error: {err}")
        try:
            self.pressure_sensor = PressureSensor()
        except Exception as err: 
            logger.error(f"Sensor Error: {err}")
        try:
            self.temperature_sensor = TemperatureSensor() 
        except Exception as err: 
            logger.error(f"Sensor Error: {err}")
        try:
            self.luminosity_sensor = LuminositySensor() 
        except Exception as err: 
            logger.error(f"Sensor Error: {err}")
        
    def write_sensor_data(self):
        if os.path.exists(self.log_filename):
            file_mode = "a"
        else:
            file_mode = "w"
        try:
            self.read_sensor_data()
            try:
                latitude = self.gps.latitude
                longitude = self.gps.longitude
            except:
                latitude = -1
                longitude = -1
            with open(self.log_filename, file_mode) as f:
                f.write(
                    json.dumps(
                        {
                            "timestamp": datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                            "luminosity": self.luminosity_data,
                            "temp": self.temperature_data,
                            "pressure": self.pressure_data,
                            "gps": self.coordinates
                        }
                    )
                )
                f.write("\n")
        except:
            with open(self.log_filename, "w"):
                pass

    def read_sensor_data(self):
        try:
            self.pressure_data = self.pressure_sensor.pressure()
        except PressureSensorCannotReadException as err:
            self.pressure_data = -1
            logger.error(f"Error: {err}")
        except Exception as err:
            logger.error(f"Sensor error: {err}")
            pass

        try:
            self.temperature_data = self.temperature_sensor.temperature() 
        except TemperatureSensorCannotReadException as err: 
            self.temperature_data = -1 
            logger.error(f"Error: {err}")
        except Exception as err:
            logger.error(f"Sensor error: {err}")
            pass

        try:
            self.luminosity_data = self.luminosity_sensor.luminosity() 
        except LuminositySensorCannotReadException as err: 
            self.luminosity_data = -1 
            logger.error(f"Error: {err}")
        except Exception as err:
            logger.error(f"Sensor error: {err}")
            pass

        try:
            self.coordinates = {
              "lat": self.gps.latitude,
              "long": self.gps.longitude
            }
        except Exception as err:
            logger.error(f"Sensor error: {err}")
            pass
    
    def get_sensor_data(self): 
        return { 
            "pressure": self.pressure_data, 
            "temperature" : self.temperature_data, 
            "luminosity" : self.luminosity_data,
            "gps": self.coordinates
        }

class PressureSensorNotConnectedException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PressureSensorCannotReadException(Exception):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class PressureSensor(MS5837_30BA):
    def __init__(self, bus=1):
        super().__init__(bus=bus)
        if not super().init():
            logger.warning("MS5837_30BA may not be connected")
            raise PressureSensorNotConnectedException(
                "MS5837_30BA may not be connected"
            )
        self.setFluidDensity(DENSITY_SALTWATER)

    def pressure(self, conversion=UNITS_mbar):
        if self.read():
            data = super().pressure(conversion=conversion)
            logger.info(f"Reading pressure data from the sensor: {data}")
            return data
        else:
            raise PressureSensorCannotReadException("Could not read pressure values")

    def temperature(self, conversion=UNITS_Centigrade):
        if self.read():
            data = super().temperature(conversion=conversion)
            logger.info(f"Reading temperature data from the sensor: {data}")
            return data
        else:
            raise PressureSensorCannotReadException("Could not read temperature values")

    def depth(self):
        if self.read():
            data = super().depth()
            logger.info(f"Reading depth data from the sensor: {data}")
            return data
        else:
            raise PressureSensorCannotReadException("Could not read depth values")


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


class LuminositySensor(TSL2561_30BA):
    def __init__(self, bus=1):
        super().__init__(bus=bus)
        if not super().init():
            logger.warning("TSL2561_30BA may not be connected")
            raise LuminositySensorNotConnectedException(
                "TSL2561_30BA may not be connected"
            )

    def luminosity(self):
        if self.read():
            data = super().lux()
            logger.info(f"Reading luminosity data from the sensor: {data}")
            return data
        else:
            raise LuminositySensorCannotReadException(
                "Could not read luminosity values"
            )

if __name__ == "__main__":
    pass

