import requests
import urllib3
from requests.exceptions import Timeout, ConnectionError

# Disable SSL warnings for self-signed certificates (development only, TODO!!!!) 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PlantGeekBackendConnector:
    def __init__(self):
        self.login_url = 'https://plantgeek.de:5000/login'
        self.data_url = 'https://plantgeek.de:5000/api/data'
        self.image_url = 'https://plantgeek.de:5000/api/image'
        self.credentials = {
            'username': 'mathiaspechinger_iut8g5oo',
            'api_key': '2114aadec64001c77d394845971f63dc'
        }
        self.timeout = 10  # Set a timeout of 10 seconds

    def updateCredentials(self, username, api_key):
        self.credentials = {
            'username': username,
            'api_key': api_key
        }

    def sendImageToPlantGeekBackend(self, sc):
        try:
            # Send the login request with timeout
            login_response = requests.post(self.login_url, json=self.credentials, verify=False, timeout=self.timeout)

            if login_response.status_code == 200:
                access_token = login_response.json().get('access_token')
                file_path = 'static/cameraImages/latest/lastFrame.jpg'
                files = {'file': open(file_path, 'rb')}
                headers = {'Authorization': f'Bearer {access_token}'}

                # Send the image with timeout
                data_response = requests.post(self.image_url, headers=headers, files=files, verify=False, timeout=self.timeout)

                if data_response.status_code != 200:
                    print(f'Failed to send data. Status code: {data_response.status_code}')
                    print('Response:', data_response.text)
            else:
                print(f'Failed to log in. Status code: {login_response.status_code}')
                print('Response:', login_response.text)
                
        except (Timeout, ConnectionError) as e:
            print(f"Connection error or timeout: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            sc.enter(300, 1, self.sendImageToPlantGeekBackend, (sc,))

    def sendDataToPlantGeekBackend(self, sc, sensorData, mqtt_interface):
        try:
            # Send the login request with timeout
            login_response = requests.post(self.login_url, json=self.credentials, verify=False, timeout=self.timeout)

            if login_response.status_code == 200:
                access_token = login_response.json().get('access_token')

                if sensorData.currentTemperature is None or sensorData.currentHumidity is None or sensorData.currentCO2 is None:
                    print('Data not ready yet')
                    sc.enter(5, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface,))
                    return

                data = {
                    'username': self.credentials['username'],
                    'api_key': self.credentials['api_key'],
                    'temperature_c': sensorData.currentTemperature,
                    'humidity': sensorData.currentHumidity,
                    'co2': sensorData.currentCO2,
                    'light_state': mqtt_interface.getLightState(),
                    'fridge_state': mqtt_interface.getFridgeState(),
                    'co2_state': mqtt_interface.getCO2State(),
                }
                headers = {'Authorization': f'Bearer {access_token}'}

                # Send the data with timeout
                data_response = requests.post(self.data_url, json=data, headers=headers, verify=False, timeout=self.timeout)

                if data_response.status_code != 200:
                    print(f'Failed to send data. Status code: {data_response.status_code}')
                    print('Response:', data_response.text)
            else:
                print(f'Failed to log in. Status code: {login_response.status_code}')
                print('Response:', login_response.text)
                
        except (Timeout, ConnectionError) as e:
            print(f"Connection error or timeout: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            sc.enter(60, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface,))
