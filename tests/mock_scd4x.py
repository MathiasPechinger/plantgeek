#!/usr/bin/env python3
import random
import time
import sys
import os

# Force flush of print statements
import functools
print = functools.partial(print, flush=True)

class MockSCD4X:
    def __init__(self, i2c):
        print(f"[MOCK] Command line arguments: {sys.argv}")
        self._temperature = 25.0
        self._humidity = 60.0
        self._co2 = 1000
        self._data_ready = True
        self._measurement_active = False
        
        # Check if mode is passed as environment variable first
        self._mode = os.environ.get('MOCK_SENSOR_MODE', 'normal')
        
        # If no env var, check command line args
        if self._mode == 'normal' and len(sys.argv) > 1:
            self._mode = sys.argv[1]
        
        print(f"[MOCK] Initialized in mode: {self._mode}")
        self._frozen_counter = 0
        
    def start_periodic_measurement(self):
        print("[MOCK] Starting periodic measurement")
        self._measurement_active = True
        
    @property
    def temperature(self):
        if self._mode == "disconnect":
            print("[MOCK] Disconnect mode - raising OSError")
            raise OSError("I2C device not found")
        elif self._mode == "freeze":
            print("[MOCK] Freeze mode - returning 25.0°C")
            return 25.0
        elif self._mode == "high_temp":
            high_temp = 32.0 + random.uniform(-0.2, 0.2)
            print(f"[MOCK] High temperature mode - returning {high_temp:.1f}°C")
            return round(high_temp, 1)
        elif self._mode == "overheat":
            overheat_temp = 34.0 + random.uniform(-0.2, 0.2)
            print(f"[MOCK] Overheat mode - returning {overheat_temp:.1f}°C")
            return round(overheat_temp, 1)
        elif self._mode == "missing_timestamp":
            # This mode will be handled by the data writer
            self._temperature += random.uniform(-0.5, 0.5)
            print(f"[MOCK] Missing timestamp mode - returning {self._temperature:.1f}°C")
            return round(self._temperature, 1)
        else:        
            self._temperature += random.uniform(-0.5, 0.5)
            print(f"[MOCK] Normal mode - returning {self._temperature:.1f}°C")
            return round(self._temperature, 1)
    
    @property
    def relative_humidity(self):
        # Add some random fluctuation
        self._humidity += random.uniform(-1, 1)
        self._humidity = max(0, min(100, self._humidity))  # Keep between 0-100%
        return round(self._humidity, 1)
    
    @property
    def CO2(self):
        if self._mode == "high_co2":
            return 2000  # Return high CO2 level
        else:
            self._co2 += random.uniform(-10, 10)
            self._co2 = max(400, min(self._co2, 4000))
        
        return int(self._co2)
    
    @property
    def data_ready(self):
        return self._data_ready
    
    def stop_periodic_measurement(self):
        self._measurement_active = False
        self._data_ready = False

    # Method to simulate sensor failures
    def set_error_state(self, state):
        if state == "disconnect":
            raise OSError("I2C device not found")
        elif state == "malfunction":
            raise RuntimeError("Sensor malfunction") 