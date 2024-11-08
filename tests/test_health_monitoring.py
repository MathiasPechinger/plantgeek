import unittest
from unittest.mock import Mock, patch
import sys
import os
import time
from include.health_monitoring import HealthMonitor

class TestHealthMonitoring(unittest.TestCase):
    def setUp(self):
        self.health_monitor = HealthMonitor()
        self.mock_scheduler = Mock()
        self.mock_scheduler.enter = Mock()
        self.mock_mqtt = Mock()
        self.mock_mqtt.devicesHealthy = True
        self.mock_mqtt.getLightState = Mock(return_value=True)
        self.mock_mqtt.getFridgeState = Mock(return_value=True)
        self.mock_mqtt.getCO2State = Mock(return_value=True)
        self.mock_mqtt.getHeaterState = Mock(return_value=True)
        self.mock_sensor_data = Mock()
        self.mock_sensor_data.currentTemperature = 25.0
        self.mock_sensor_data.currentHumidity = 50.0
        self.mock_sensor_data.currentCO2 = 800
        self.mock_sensor_data.lastTimestamp = time.time()

    def test_temperature_within_range(self):
        self.assertTrue(15 <= self.mock_sensor_data.currentTemperature <= 30)

    def test_humidity_within_range(self):
        self.assertTrue(30 <= self.mock_sensor_data.currentHumidity <= 70)

    def test_co2_within_range(self):
        self.assertTrue(400 <= self.mock_sensor_data.currentCO2 <= 2000)

    def test_light_state(self):
        light_state = self.mock_mqtt.getLightState()
        self.assertIsInstance(light_state, bool)

    def test_device_states(self):
        states = {
            'light': self.mock_mqtt.getLightState(),
            'fridge': self.mock_mqtt.getFridgeState(),
            'co2': self.mock_mqtt.getCO2State(),
            'heater': self.mock_mqtt.getHeaterState()
        }
        self.assertTrue(all(isinstance(state, bool) for state in states.values()))

    def test_invalid_sensor_data(self):
        self.mock_sensor_data.currentTemperature = None
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        with patch('builtins.print') as mock_print:
            self.health_monitor.check_status(
                self.mock_scheduler,
                self.mock_mqtt,
                self.mock_sensor_data,
                True
            )
            mock_print.assert_any_call("Temperature sensor data invalid.")
        self.assertFalse(self.health_monitor.systemHealthy)

    def test_outdated_sensor_data(self):
        self.mock_sensor_data.lastTimestamp = time.time() - 180
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        with patch('builtins.print') as mock_print:
            self.health_monitor.check_status(
                self.mock_scheduler,
                self.mock_mqtt,
                self.mock_sensor_data,
                True
            )
            mock_print.assert_any_call("Sensor data not updated for more than 60 seconds.")
        self.assertFalse(self.health_monitor.systemHealthy)

    def test_unhealthy_zigbee_devices(self):
        self.mock_mqtt.devicesHealthy = False
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        with patch('builtins.print') as mock_print:
            self.health_monitor.check_status(
                self.mock_scheduler,
                self.mock_mqtt,
                self.mock_sensor_data,
                True
            )
            mock_print.assert_any_call("Zigbee devices not healthy.")
        self.assertFalse(self.health_monitor.systemHealthy)

    def test_temperature_too_high(self):
        self.mock_sensor_data.currentTemperature = 34.0
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        with patch('builtins.print') as mock_print:
            self.health_monitor.check_status(
                self.mock_scheduler,
                self.mock_mqtt,
                self.mock_sensor_data,
                True
            )
            mock_print.assert_called_with(
                "WARNTING: System overheated! Reduce energy input (light, dehumidifier)!"
            )
        self.assertTrue(self.health_monitor.systemOverheated)

    def test_frozen_temperature_sensor(self):
        self.mock_sensor_data.currentTemperature = 25.0
        self.health_monitor.check_status(
            self.mock_scheduler,
            self.mock_mqtt,
            self.mock_sensor_data,
            True
        )
        self.health_monitor.temperatureFrozenTimeout = 2
        for _ in range(3):
            with patch('builtins.print') as mock_print:
                self.health_monitor.check_status(
                    self.mock_scheduler,
                    self.mock_mqtt,
                    self.mock_sensor_data,
                    True
                )
        self.assertFalse(self.health_monitor.systemHealthy)

if __name__ == '__main__':
    unittest.main()