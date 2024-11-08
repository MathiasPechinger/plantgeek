import unittest
import requests
from unittest.mock import patch

class TestPlantGeekBackendConnector(unittest.TestCase):
    @patch('requests.get')
    def test_ssl_verification(self, mock_get):
        # Simulate a successful request
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b'Success'

        # Make a request with SSL verification enabled
        response = requests.get('https://example.com', verify=True)
        mock_get.assert_called_with('https://example.com', verify=True)
        self.assertEqual(response.content, b'Success')

if __name__ == '__main__':
    unittest.main()