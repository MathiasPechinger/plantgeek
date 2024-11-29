import requests
import urllib3
from requests.exceptions import Timeout, ConnectionError
from datetime import datetime

class PlantGeekBackendConnector:
    def __init__(self):
        self.data_url = 'https://writesysteminfo-jimd7cggoa-uc.a.run.app'
        self.image_url = 'https://uploadimage-jimd7cggoa-uc.a.run.app'
        self.health_url = 'https://receivehealtherrors-jimd7cggoa-uc.a.run.app'
        self.warning_url = 'https://receivehealthwarnings-jimd7cggoa-uc.a.run.app'
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
                verify=True
            )
            
            if response.status_code == 200:
                # print("Image uploaded successfully:", response.text)
                pass
            else:
                print("Image upload failed:", response.status_code, response.text)

        except requests.exceptions.RequestException as e:
            print(f"An error occurred while uploading image: {str(e)}")
            
        finally:
            # here we set the image upload interval ( this is limited in the backend as well ;) Just in case you wanted to increase it)
            sc.enter(3600, 1, self.sendImageToPlantGeekBackend, (sc,mqtt_interface,camera,))

    def sendDataToPlantGeekBackend(self, sc, sensorData, mqtt_interface, health_monitor):
        if sensorData.currentTemperature is None or sensorData.currentHumidity is None or sensorData.currentCO2 is None:
            sc.enter(5, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface, health_monitor))
            return

        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.credentials['api_key'],
                "x-user-id": self.credentials['username']
            }

            # Get active warnings
            active_warnings = health_monitor.get_active_warnings()
            has_warnings = len(active_warnings) > 0

            # Data payload with extended values and warning status
            data = {
                "temperature": sensorData.currentTemperature,  
                "co2ppm": sensorData.currentCO2,    
                "humidity": sensorData.currentHumidity,     
                "light_state": mqtt_interface.getLightState(),  
                "fridge_state": mqtt_interface.getFridgeState(),
                "co2valve_state": mqtt_interface.getCO2State(),
                "timestamp": datetime.utcnow().isoformat(),
                "device_name": self.device_name,
                "heater_state": mqtt_interface.getHeaterState(),
                "system_healthy": health_monitor.get_status(),
                "has_warnings": has_warnings  
            }

            # print("Sending data to PlantGeek backend:", data)
            # print("username:", self.credentials['username'])

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
            sc.enter(backend_update_interval, 1, self.sendDataToPlantGeekBackend, (sc, sensorData, mqtt_interface, health_monitor))

    def sendHealthErrorsToBackend(self, sc, health_monitor):
        # print("Sending health errors to PlantGeek backend")
        active_errors = health_monitor.get_active_errors()
        if not active_errors:
            # print("No active errors")
            sc.enter(60, 1, self.sendHealthErrorsToBackend, (sc, health_monitor,))
            return

        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.credentials['api_key'],
                "x-user-id": self.credentials['username']
            }
            
            error_data = {
                "device_name": self.device_name,
                "timestamp": datetime.utcnow().isoformat(),
                "errors": [
                    {
                        "code": error.code.value,
                        "message": error.message,
                        "timestamp": error.timestamp.isoformat()
                    }
                    for error in active_errors
                ]
            }
            
            # print("Sending health errors to PlantGeek backend:")
            # print(error_data)
            response = requests.post(
                self.health_url,
                headers=headers,
                json=error_data,
                timeout=self.timeout
            )
            
            # Clear error history after successful send
            health_monitor.clear_error_history()
            
        except Exception as e:
            print(f"Error sending health data: {str(e)}")
        finally:
            sc.enter(60, 1, self.sendHealthErrorsToBackend, (sc, health_monitor,))

    def sendWarningsToBackend(self, sc, warning_monitor):
        # Get active warnings from the warning monitor
        active_warnings = warning_monitor.get_active_warnings()
        
        if not active_warnings:
            sc.enter(60, 1, self.sendWarningsToBackend, (sc, warning_monitor,))
            return

        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.credentials['api_key'],
                "x-user-id": self.credentials['username']
            }
            
            warning_data = {
                "device_name": self.device_name,
                "timestamp": datetime.utcnow().isoformat(),
                "warnings": [
                    {
                        "code": warning.code.value,
                        "message": warning.message,
                        "timestamp": warning.timestamp.isoformat()
                    }
                    for warning in active_warnings
                ]
            }
            
            response = requests.post(
                self.warning_url,  
                headers=headers,
                json=warning_data,
                timeout=self.timeout
            )

            
        except Exception as e:
            print(f"Error sending warning data: {str(e)}")
        finally:
            sc.enter(60, 1, self.sendWarningsToBackend, (sc, warning_monitor,))
