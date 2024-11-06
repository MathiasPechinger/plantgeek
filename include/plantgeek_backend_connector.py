import requests
import urllib3
from requests.exceptions import Timeout, ConnectionError
from datetime import datetime

# Disable SSL warnings for self-signed certificates (development only, TODO!!!!) 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class PlantGeekBackendConnector:
    def __init__(self):
        self.data_url = 'https://writesysteminfo-jimd7cggoa-uc.a.run.app'
        self.image_url = 'https://uploadimage-jimd7cggoa-uc.a.run.app'
        self.credentials = {
            'username': 'undefined',
            'api_key': 'undefined'
        }
        self.device_name = 'device_1234'  # Default device name
        self.timeout = 10  # Set a timeout of 10 seconds

    def updateCredentials(self, username, api_key):
        self.credentials = {
            'username': username,
            'api_key': api_key
        }
        
    def updateDeviceName(self, device_name):
        self.device_name = device_name

    def sendImageToPlantGeekBackend(self, sc, mqtt_interface, camera):

        # Don't send image if light is off (it is night)
        if not mqtt_interface.getLightState():
            print("Light is off, skipping image upload")
            sc.enter(3600, 1, self.sendImageToPlantGeekBackend, (sc,mqtt_interface,camera,))
            return

        try:
            headers = {
                "x-api-key": self.credentials['api_key'],
                "x-user-id": self.credentials['username'],
                "x-device-name": self.device_name,
                "Content-Type": "image/jpeg"
            }

            # Read the file as binary data
            image_data = camera.get_latest_image()
                
            # Send the POST request with raw image data
            response = requests.post(
                self.image_url,
                headers=headers,
                data=image_data,  # Send raw image data instead of using files
                timeout=self.timeout,
                verify=False
            )
            
            if response.status_code == 200:
                print("Image uploaded successfully:", response.text)
            else:
                print("Image upload failed:", response.status_code, response.text)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while uploading image: {str(e)}")
            
        finally:
            # here we set the image upload interval ( this is limited in the backend as well ;) Just in case you wanted to increase it)
            sc.enter(3600, 1, self.sendImageToPlantGeekBackend, (sc,mqtt_interface,camera,))

    def sendDataToPlantGeekBackend(self, sc, sensorData, mqtt_interface):
            
        if sensorData.currentTemperature is None or sensorData.currentHumidity is None or sensorData.currentCO2 is None:
            print('Data not ready yet')
            sc.enter(5, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface,))
            return

        try:
            # Headers including the API key
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.credentials['api_key'],
                "x-user-id": self.credentials['username']
            }

            # Data payload with extended values
            data = {
                "temperature": sensorData.currentTemperature,  # example temperature value
                "co2ppm": sensorData.currentCO2,      # example CO2 ppm value
                "humidity": sensorData.currentHumidity,     # example humidity valuecu
                "light_state": mqtt_interface.getLightState(),  # example state boolean
                "fridge_state": mqtt_interface.getFridgeState(),
                "co2valve_state": mqtt_interface.getCO2State(),
                "timestamp": datetime.utcnow().isoformat(),
                "device_name": self.device_name,  # example device ID/name,
                "heater_state": mqtt_interface.getHeaterState()
            }

            print("Sending data to PlantGeek backend:", data)
            print("username:", self.credentials['username'])

            # Send the POST request
            response = requests.post(self.data_url, headers=headers, json=data)

            # Print the response (for debugging)
            # if response.status_code == 200:
            #     print("Success:", response.text)
            # else:
            #     print("Failed:", response.status_code, response.text)

        except (Timeout, ConnectionError) as e:
            print(f"Connection error or timeout: {str(e)}")
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        finally:
            # here we set the data upload interval ( this is limited in the backend as well ;) Just in case you wanted to increase it)
            backend_update_interval = 60*1
            sc.enter(backend_update_interval, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface,))
