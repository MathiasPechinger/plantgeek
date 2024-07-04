import requests
# Disable SSL warnings for self-signed certificates (development only, TODO!!!!) 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class PlantGeekBackendConnector:
    def __init__(self):

        # Define the URLs for login and data endpoints
        self.login_url = 'https://plantgeek.de:5000/login'
        self.data_url = 'https://plantgeek.de:5000/api/data'
        self.image_url = 'https://plantgeek.de:5000/api/image'
        
        self.credentials = {
            'username': 'mathiaspechinger_iut8g5oo',
            'api_key': '2114aadec64001c77d394845971f63dc'
        }
        

    def sendImageToPlantGeekBackend(self, sc):
        try:
            # Send the login request
            login_response = requests.post(self.login_url, json=self.credentials, verify=False)

            if login_response.status_code == 200:
                # Retrieve the access token
                access_token = login_response.json().get('access_token')

                # Prepare the file to be sent
                file_path = 'static/cameraImages/latest/lastFrame.jpg'
                files = {'file': open(file_path, 'rb')}


                # print('Sending image to PlantGeek backend')
                # print(files)

                # Set the Authorization header with the JWT token
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }

                # Send the POST request with the token
                data_response = requests.post(self.image_url, headers=headers, files=files, verify=False)

                # Check the response status
                if data_response.status_code == 200:
                    # print('Data sent successfully!')
                    pass
                else:
                    print(f'Failed to send data. Status code: {data_response.status_code}')
                    print('Response:', data_response.text)
            else:
                print(f'Failed to log in. Status code: {login_response.status_code}')
                print('Response:', login_response.text)
                
            sc.enter(300, 1, self.sendImageToPlantGeekBackend, (sc,))
        except Exception as e:
            sc.enter(300, 1, self.sendImageToPlantGeekBackend, (sc,))
            print(f"An error occurred: {str(e)}")

    def sendDataToPlantGeekBackend(self, sc, sensorData):
        try:
            # Send the login request
            login_response = requests.post(self.login_url, json=self.credentials, verify=False)

            if login_response.status_code == 200:
                # Retrieve the access token
                access_token = login_response.json().get('access_token')

                if sensorData.currentTemperature is None or sensorData.currentHumidity is None or sensorData.currentCO2 is None:
                    print('Data not ready yet')
                    sc.enter(5, 1, self.sendDataToPlantGeekBackend, (sc,sensorData,))
                    return

                # Prepare the data to be sent
                data = {
                    'temperature_c': sensorData.currentTemperature,
                    'humidity': sensorData.currentHumidity,
                    'co2': sensorData.currentCO2,
                }


                # Set the Authorization header with the JWT token
                headers = {
                    'Authorization': f'Bearer {access_token}'
                }

                # Send the POST request with the token
                data_response = requests.post(self.data_url, json=data, headers=headers, verify=False)

                # Check the response status
                if data_response.status_code == 200:
                    # print('Data sent successfully!')
                    pass
                else:
                    print(f'Failed to send data. Status code: {data_response.status_code}')
                    print('Response:', data_response.text)
            else:
                print(f'Failed to log in. Status code: {login_response.status_code}')
                print('Response:', login_response.text)
                
            sc.enter(60, 1, self.sendDataToPlantGeekBackend, (sc,sensorData,))
        except Exception as e:
            sc.enter(60, 1, self.sendDataToPlantGeekBackend, (sc,sensorData,))
            print(f"An error occurred: {str(e)}")
