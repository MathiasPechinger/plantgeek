import os
import sys
import time

# Set testing environment
os.environ['TESTING'] = '1'

from include.data_writer_mysql import SensorDataLogger

def test_normal_readings():
    logger = SensorDataLogger(use_scd41=True)
    logger.initialize_sensors()
    
    # Get some readings
    for _ in range(5):
        if logger.scd4x.data_ready:
            temp = logger.scd4x.temperature
            humidity = logger.scd4x.relative_humidity
            co2 = logger.scd4x.CO2
            print(f"Temperature: {temp}°C, Humidity: {humidity}%, CO2: {co2}ppm")
        time.sleep(1)

def test_sensor_failure():
    logger = SensorDataLogger(use_scd41=True)
    logger.initialize_sensors()
    
    # Simulate sensor disconnect
    logger.scd4x.set_error_state("disconnect")
    
if __name__ == "__main__":
    test_normal_readings()
    test_sensor_failure() 