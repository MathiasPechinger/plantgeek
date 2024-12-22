import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import time
from include.health_monitoring import HealthMonitor
from include.health_monitoring_errors import HealthErrorCode, HealthWarningCode

class TestHealthMonitor(unittest.TestCase):
    def setUp(self):
        # Create mock config
        self.mock_config = {
            'TemperatureControl': {
                'targetDayTemperature': 25.0,
                'targetNightTemperature': 20.0
            },
            'CO2Control': {
                'targetValue': 800
            },
            'HumidityControl': {
                'targetHumidity': 65
            },
            'ControlConfig': {
                'targetTempDay': 25.0,
                'targetTempNight': 20.0,
                'targetCO2': 800,
                'targetHumidity': 65,
                'tempThreshold': 1.0,
                'co2Threshold': 100,
                'humidityThreshold': 5.0
            }
        }
        
        # Initialize HealthMonitor with mock config
        self.health_monitor = HealthMonitor(self.mock_config)
        
        # do tests after init is done
        self.health_monitor.initDone = True
        
        # Create mock objects
        self.mock_scheduler = Mock()
        self.mock_mqtt = Mock()
        self.mock_sensor_data = Mock()
        
        # Set default mock values
        self.mock_mqtt.devicesHealthy = True
        self.mock_mqtt.getLightState = Mock(return_value=True)
        self.mock_sensor_data.currentTemperature = 25.0
        self.mock_sensor_data.currentCO2 = 800
        self.mock_sensor_data.currentHumidity = 65.0
        self.mock_sensor_data.lastTimestamp = time.time()

    def test_normal_operation_daytime(self):
        """Test system behavior under normal conditions"""
        
        # Set default mock values
        self.mock_mqtt.devicesHealthy = True
        self.mock_mqtt.getLightState = Mock(return_value=True) # because of daytime
        self.mock_sensor_data.currentTemperature = 25.0
        self.mock_sensor_data.currentCO2 = 800
        self.mock_sensor_data.currentHumidity = 65.0
        self.mock_sensor_data.lastTimestamp = time.time()
        
        
        self.health_monitor.check_status(
            self.mock_scheduler, 
            self.mock_mqtt, 
            self.mock_sensor_data, 
            True
        )
        
        self.assertTrue(self.health_monitor.systemHealthy)
        self.assertFalse(self.health_monitor.systemOverheated)
        self.assertEqual(len(self.health_monitor.get_active_errors()), 0)
        
    def test_normal_operation_nighttime(self):
        """Test system behavior under normal conditions"""
        
        # Set default mock values
        self.mock_mqtt.devicesHealthy = True
        self.mock_mqtt.getLightState = Mock(return_value=False) # because of nighttime
        self.mock_sensor_data.currentTemperature = 20.0
        self.mock_sensor_data.currentCO2 = 800
        self.mock_sensor_data.currentHumidity = 65.0
        self.mock_sensor_data.lastTimestamp = time.time()
        
        self.health_monitor.check_status(
            self.mock_scheduler, 
            self.mock_mqtt, 
            self.mock_sensor_data, 
            True
        )
        
        self.assertTrue(self.health_monitor.systemHealthy)
        self.assertFalse(self.health_monitor.systemOverheated)
        self.assertEqual(len(self.health_monitor.get_active_errors()), 0)
        
    def test_invalid_temperature_sensor(self):
        """Test system response to invalid temperature sensor data"""
        self.mock_sensor_data.currentTemperature = None
        
        self.health_monitor.check_status(
            self.mock_scheduler, 
            self.mock_mqtt, 
            self.mock_sensor_data, 
            True
        )
        
        self.assertFalse(self.health_monitor.systemHealthy)
        active_errors = self.health_monitor.get_active_errors()
        self.assertEqual(len(active_errors), 1)
        self.assertEqual(active_errors[0].code, HealthErrorCode.TEMPERATURE_SENSOR_INVALID)

    def test_frozen_temperature_sensor(self):
        """Test detection of frozen temperature sensor"""
        # Set initial temperature
        self.health_monitor.previousTemperature = 25.0
        self.mock_sensor_data.currentTemperature = 25.0
        
        # Simulate frozen sensor by keeping temperature constant
        for _ in range(301):  # Slightly more than temperatureFrozenTimeout
            self.health_monitor.check_status(
                self.mock_scheduler,
                self.mock_mqtt,
                self.mock_sensor_data,
                True
            )
            
        active_errors = self.health_monitor.get_active_errors()
        self.assertTrue(any(error.code == HealthErrorCode.TEMPERATURE_SENSOR_FROZEN 
                          for error in active_errors))

    def test_system_overheat_detection(self):
        """Test system overheat detection and hysteresis"""
        # Simulate overheating
        self.mock_sensor_data.currentTemperature = 34.0  # Above overheatTemperature
        
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        
        self.assertTrue(self.health_monitor.systemOverheated)
        self.assertFalse(self.health_monitor.systemHealthy)
        
        # Test hysteresis - temperature drops but not enough to clear overheating
        self.mock_sensor_data.currentTemperature = 33.0
        
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        
        self.assertTrue(self.health_monitor.systemOverheated)
        
        # Temperature drops below hysteresis threshold
        self.mock_sensor_data.currentTemperature = 32.0
        
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        
        self.assertFalse(self.health_monitor.systemOverheated)

    def test_stale_sensor_data(self):
        """Test detection of stale sensor data"""
        self.mock_sensor_data.lastTimestamp = time.time() - 121  # More than 120 seconds old
        
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        
        active_errors = self.health_monitor.get_active_errors()
        self.assertTrue(any(error.code == HealthErrorCode.SENSOR_DATA_NOT_UPDATED 
                          for error in active_errors))


if __name__ == '__main__':
    unittest.main()
