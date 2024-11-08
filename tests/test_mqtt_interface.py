import unittest
from unittest.mock import Mock, patch
from include.mqtt_interface import MQTT_Interface

class TestMQTTInterface(unittest.TestCase):
    def setUp(self):
        # Patch the MQTT client to prevent actual network calls
        patcher = patch('include.mqtt_interface.mqtt.Client')
        self.addCleanup(patcher.stop)
        self.mock_mqtt_client = patcher.start()

        # Create an instance of MQTT_Interface with the mocked client
        self.mqtt_interface = MQTT_Interface('broker', 1883, 'user', 'password')
        self.mqtt_interface.client = self.mock_mqtt_client.return_value

    def test_publish(self):
        topic = "test/topic"
        payload = "test_payload"
        self.mqtt_interface.publish(topic, payload)
        self.mqtt_interface.client.publish.assert_called_with(topic, payload)

    def test_get_light_state(self):
        # Mock the device state
        self.mqtt_interface.devices = [Mock(state=True)]
        self.assertTrue(self.mqtt_interface.getLightState())

    def test_set_light_state(self):
        # Mock the device with a friendly name and ensure manual override is inactive
        self.mqtt_interface.devices = [Mock(friendly_name="light", state=False, manualOverrideActive=False)]
        
        # Mock the switch function to simulate successful state change
        self.mqtt_interface.switchLedvanceSocket_4058075729261 = Mock(return_value=True)
        
        # Call the method to set the light state
        result = self.mqtt_interface.setLightState(True)
        
        # Check if the state was updated
        self.assertTrue(result)
        # Verify the switch function was called with the correct parameters
        self.mqtt_interface.switchLedvanceSocket_4058075729261.assert_called_with("light", True, "60", "10")

    def test_get_device_state(self):
        # Mock the device and its friendly name
        self.mqtt_interface.devices = [Mock(friendly_name="light", state=True)]
        self.assertTrue(self.mqtt_interface.getDeviceState("light"))

if __name__ == '__main__':
    unittest.main()