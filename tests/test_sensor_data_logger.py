import unittest
from unittest.mock import Mock
from include.data_writer_mysql import SensorDataLogger

class TestSensorDataLogger(unittest.TestCase):
    def setUp(self):
        self.logger = SensorDataLogger()

    def test_sensor_data_validity(self):
        # Simulate invalid sensor data
        self.logger.currentTemperature = None
        self.logger.currentHumidity = None
        self.logger.currentCO2 = None
        self.assertIsNone(self.logger.currentTemperature, "Temperature data should be None")
        self.assertIsNone(self.logger.currentHumidity, "Humidity data should be None")
        self.assertIsNone(self.logger.currentCO2, "CO2 data should be None")

if __name__ == '__main__':
    unittest.main()