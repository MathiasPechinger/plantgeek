import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import time
from include.heater_controller import Heater

class MockMQTTInterface:
    def __init__(self):
        self.heater_state = False
        
    def setHeaterState(self, state):
        self.heater_state = state
        return True
        
    def getHeaterState(self):
        return self.heater_state

class TestHeaterController(unittest.TestCase):
    def setUp(self):
        self.db_config = {
            'host': 'dummy',
            'user': 'dummy',
            'password': 'dummy',
            'database': 'dummy'
        }
        self.heater = Heater(self.db_config)
        self.heater.set_timeout(3)  # Set timeout to 3 seconds for faster testing
        self.mqtt = MockMQTTInterface()
        
        # Set control parameters
        self.heater.set_control_temperature(24.5)  # Target temperature
        self.heater.set_hysteresis(0.5)           # Hysteresis
        
        # Mock is_temperature_falling to always return True
        self.heater.is_temperature_falling = lambda: True
        
        self.heater.switch_on_delay = 0
        self.heater.UnitTestActive = True
        
    @patch('mysql.connector.connect')
    def test_temperature_control_cycle(self, mock_connect):
        # Create a mock cursor and connection
        mock_cursor = MagicMock()
        mock_connect.return_value.cursor.return_value = mock_cursor
        
        # Test scenario: Detailed temperature cycling with 0.1°C steps
        test_temperatures = [
            # From 23 to 26 (increasing)
            23.0, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9,
            24.0, 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9,
            25.0, 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8, 25.9, 26.0,
            # From 26 to 23 (decreasing)
            26.0, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1,
            25.0, 24.9, 24.8, 24.7, 24.6, 24.5, 24.4, 24.3, 24.2, 24.1,
            24.0, 23.9, 23.8, 23.7, 23.6, 23.5, 23.4, 23.3, 23.2, 23.1, 23.0,
            # From 23 to 24.8 (increasing)
            23.0, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9,
            24.0, 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8,
            # From 24.8 to 23 (decreasing)
            24.8, 24.7, 24.6, 24.5, 24.4, 24.3, 24.2, 24.1, 24.0,
            23.9, 23.8, 23.7, 23.6, 23.5, 23.4, 23.3, 23.2, 23.1, 23.0,
            # From 23 to 26 (increasing)
            23.0, 23.1, 23.2, 23.3, 23.4, 23.5, 23.6, 23.7, 23.8, 23.9,
            24.0, 24.1, 24.2, 24.3, 24.4, 24.5, 24.6, 24.7, 24.8, 24.9,
            25.0, 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7, 25.8, 25.9, 26.0,
            # From 26 to 24.8 (decreasing)
            26.0, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1,
            25.0, 24.9, 24.8,
            # From 24.8 to 26 (increasing)
            24.8, 24.9, 25.0, 25.1, 25.2, 25.3, 25.4, 25.5, 25.6, 25.7,
            25.8, 25.9, 26.0,
            # From 26 to 23 (decreasing)
            26.0, 25.9, 25.8, 25.7, 25.6, 25.5, 25.4, 25.3, 25.2, 25.1,
            25.0, 24.9, 24.8, 24.7, 24.6, 24.5, 24.4, 24.3, 24.2, 24.1,
            24.0, 23.9, 23.8, 23.7, 23.6, 23.5, 23.4, 23.3, 23.2, 23.1, 23.0
        ]
        
        expected_states = [
            # From 23 to 26 (increasing) - ON until 25.0
            True, True, True, True, True, True, True, True, True, True,
            True, True, True, True, True, True, True, True, True, True,
            False, False, False, False, False, False, False, False, False, False, False,
            # From 26 to 23 (decreasing) - Stays OFF until timeout after reaching 24.5
            False, False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, True, True, True, True,
            True, True, True, True, True, True, True, True, True, True, True,
            # From 23 to 24.8 (increasing) - ON until reaches 24.8
            True, True, True, True, True, True, True, True, True, True,
            True, True, True, True, True, True, True, True, True,
            # From 24.8 to 23 (decreasing) - ON all the way as below 25.0
            True, True, True, True, True, True, True, True, True,
            True, True, True, True, True, True, True, True, True, True,
            # From 23 to 26 (increasing) - ON until 25.0
            True, True, True, True, True, True, True, True, True, True,
            True, True, True, True, True, True, True, True, True, True,
            False, False, False, False, False, False, False, False, False, False, False,
            # From 26 to 24.8 (decreasing) - Stays OFF until timeout after reaching 24.5
            False, False, False, False, False, False, False, False, False, False,
            False, False, False,
            # From 24.8 to 26 (increasing) - stays off 
            False, False, False, False, False, False, False, False, False, False,
            False, False, False,
            # From 26 to 23 (decreasing) - Stays OFF until timeout after reaching 24.5
            False, False, False, False, False, False, False, False, False, False,
            False, False, False, False, False, False, True, True, True, True,
            True, True, True, True, True, True, True, True, True, True, True
        ]
        
        # Create a mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.enter = MagicMock()
        
        # Indices where heater switches off (temperature reaches 25.0°C)
        switch_off_indices = [20, 140, 232]  # These are the indices where temp hits 25.0
        
        # Test sections with their ranges
        test_sections = [
            (0, 31, "Testing 23°C to 26°C (increasing)"),
            (31, 62, "Testing 26°C to 23°C (decreasing)"),
            (62, 81, "Testing 23°C to 24.8°C (increasing)"),
            (81, 100, "Testing 24.8°C to 23°C (decreasing)"),
            (100, 131, "Testing 23°C to 26°C (increasing)"),
            (131, 143, "Testing 26°C to 24.8°C (decreasing)"),
            (143, 156, "Testing 24.8°C to 26°C (increasing)"),
            (156, 187, "Testing 26°C to 23°C (decreasing)")
        ]
        
        current_section = 0
        for i, (temp, expected_state) in enumerate(zip(test_temperatures, expected_states)):
            # Print section header when starting new section
            if current_section < len(test_sections) and i == test_sections[current_section][0]:
                print(f"\n=== {test_sections[current_section][2]} ===")
                current_section += 1
            
            # Setup mock database response
            mock_cursor.fetchall.return_value = [(temp,)]
            
            # Run heater control cycle
            self.heater.control_heater(mock_scheduler, self.mqtt)
            
            # Print current test state
            print(f"Temperature: {temp:4.1f}°C, Expected: {'ON ' if expected_state else 'OFF'}, "
                  f"Actual: {'ON ' if self.mqtt.getHeaterState() else 'OFF'}")
            
            # Verify heater state
            self.assertEqual(
                self.mqtt.getHeaterState(), 
                expected_state,
                f"Failed at temperature {temp}°C: expected heater to be "
                f"{'ON' if expected_state else 'OFF'} but it was "
                f"{'ON' if self.mqtt.getHeaterState() else 'OFF'}"
            )
            
            # Handle sleep timing based on test position
            if i in switch_off_indices:
                print(f"Waiting for timeout (4s) at {temp}°C...")
                time.sleep(4)  # Wait longer than the 3s timeout right when we switch off
            else:
                time.sleep(0.1)  # Normal delay between tests

    def test_required_attributes_exist(self):
        """Test that all required attributes are initialized in __init__"""
        required_attributes = [
            'is_on',
            'off_time',
            'db_config',
            'controlTemperature',
            'hysteresis',
            'timeout',
            'switch_on_delay',
            'pending_switch_on_time',
            'UnitTestActive',
            'falling_temp_threshold'
        ]
        
        for attr in required_attributes:
            self.assertTrue(
                hasattr(self.heater, attr),
                f"Heater class is missing required attribute: {attr}"
            )

if __name__ == '__main__':
    unittest.main() 