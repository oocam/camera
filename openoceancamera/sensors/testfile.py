"""Temporary testfile to sort out list index error in code."""

from .atlas_sensors import EC_Sensor, PH_Sensor, DO_Sensor

# Initialise the three sensors.
# NOTE: they should initialise in the following order, so check the order! 
# (just to see if the sensors are booting properly. THe order isn't otherwise important)

print('Initialisation check!')
print('First the EC sensor')
ec_sensor = EC_Sensor()

print('then the DO sensor')
do_sensor = DO_Sensor()

print('First the PH sensor')
ph_sensor = PH_Sensor()

# Now lets see the readings. The faulty part is that some of the _get_data calls 
# appear to not be returning an entire list of values
# Hench the 'index error'.

print('EC sensor should return a list of 4 vals')
print(ec_sensor._get_data())

print('DO sensor should return 2 vals:')
print(ec_sensor._get_data())

print('PH sensor should return 1 val')
print(ph_sensor._get_data())

print('Now lets check the specific get data methods')
print('EC sensor')
print(ec_sensor.get_conductivity())
print(ec_sensor.get_tds())
print(ec_sensor.get_salinity())
print(ec_sensor.get_specific_gravity())

print('DO sensor')
print(do_sensor.get_do())
print(do_sensor.get_percent_oxygen())

print('PH sensor')
print(ph_sensor.get_ph())