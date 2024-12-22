import random
import time

class MockSCD4X:
    def __init__(self, i2c):
        self._temperature = 25.0
        self._humidity = 60.0
        self._co2 = 1000
        self._data_ready = True
        self._measurement_active = False
        
    @property
    def temperature(self):
        # Add some random fluctuation
        self._temperature += random.uniform(-0.5, 0.5)
        return round(self._temperature, 1)
    
    @property
    def relative_humidity(self):
        # Add some random fluctuation
        self._humidity += random.uniform(-1, 1)
        self._humidity = max(0, min(100, self._humidity))  # Keep between 0-100%
        return round(self._humidity, 1)
    
    @property
    def CO2(self):
        # Add some random fluctuation
        self._co2 += random.randint(-50, 50)
        self._co2 = max(400, min(5000, self._co2))  # Keep between 400-5000 ppm
        return int(self._co2)
    
    @property
    def data_ready(self):
        return self._data_ready
    
    def start_periodic_measurement(self):
        self._measurement_active = True
        self._data_ready = True
        
    def stop_periodic_measurement(self):
        self._measurement_active = False
        self._data_ready = False

    # Method to simulate sensor failures
    def set_error_state(self, state):
        if state == "disconnect":
            raise OSError("I2C device not found")
        elif state == "malfunction":
            raise RuntimeError("Sensor malfunction") 