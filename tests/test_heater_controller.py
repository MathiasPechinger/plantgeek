import unittest
from unittest.mock import Mock
from include.heater_controller import Heater

class TestHeater(unittest.TestCase):
    def setUp(self):
        self.mock_mqtt = Mock()
        self.heater = Heater(db_config={})

    def test_switch_on(self):
        self.heater.off_time = None
        self.mock_mqtt.setHeaterState.return_value = True
        self.heater.switch_on(self.mock_mqtt)
        self.assertTrue(self.heater.is_on)

    def test_switch_off(self):
        self.mock_mqtt.setHeaterState.return_value = True
        self.heater.switch_off(self.mock_mqtt)
        self.assertFalse(self.heater.is_on)

    def test_control_temperature(self):
        self.heater.set_control_temperature(22.0)
        self.assertEqual(self.heater.controlTemperature, 22.0)

    def test_hysteresis_setting(self):
        self.heater.set_hysteresis(0.5)
        self.assertEqual(self.heater.hysteresis, 0.5)

if __name__ == '__main__':
    unittest.main()