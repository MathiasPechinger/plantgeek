import paho.mqtt.client as mqtt
import json
import time
import requests
import sched

class MQTT_Interface:
    def __init__(self, broker, port, user, password):
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.devices = []
        self.client = mqtt.Client()
        self.client.username_pw_set(user, password)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.manualOverrideTimer = 0
        self.manualOverrideActive = False
        self.lightSocketID = ""
        self.fridgeSocketID = ""
        self.CO2SocketID = ""
        self.zigbeeState = ""
        self.zigbeeDevices = ""
        self.zigbeeDevicesAlive = False
        self.availabiltyCheckCounter = 0
        self.scheduler = sched.scheduler(time.time, time.sleep)

    def fetch_zigbee_state(self):
        try:
            response = requests.get('http://localhost:5010/zigbee/state')
            response.raise_for_status()
            self.zigbeeState = response.json()
        except requests.exceptions.RequestException as error:
            print(f'Error fetching Zigbee state: {error}')

    def fetch_zigbee_devices(self):
        try:
            response = requests.get('http://localhost:5010/zigbee/devices')
            response.raise_for_status()
            self.zigbeeDevices = response.json()
        except requests.exceptions.RequestException as error:
            print(f'Error fetching Zigbee devices: {error}')

    def update_database_list(self):
        try:
            matching_devices = []
            for device in self.zigbeeDevices:
                ieee_address = device.get("ieeeAddr")
                for state_addr in self.zigbeeState:
                    if state_addr == ieee_address:
                        matching_devices.append(device)
                        break

            self.lightSocketID = matching_devices[0].get("ieeeAddr")
            self.fridgeSocketID = matching_devices[1].get("ieeeAddr")
        except Exception as e:
            print(f"Error in update_database_list: {e}")

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_publish(self, client, userdata, mid):
        print("Message published")

    def on_message(self, client, userdata, msg):
        print("Receiving message")
        try:
            if "availability" in msg.topic:
                device_name = msg.topic.split('/')[1]
                status = msg.payload.decode()
                # print(f"Device {device_name} is {status}")
                for device in self.devices:
                    if device['friendly_name'] == device_name:
                        device['availability'] = status
                        break
                else:
                    self.devices.append({'friendly_name': device_name, 'availability': status})
                print(self.devices)
        except Exception as e:
            print(f"Error in on_message: {e}, Topic: {msg.topic}, Payload: {msg.payload}")

    def mainloop(self,scheduler_mqtt):
        print("Mainloop")
        if self.availabiltyCheckCounter <= 0:
            self.client.subscribe("zigbee2mqtt/+/availability")
            self.client.subscribe("zigbee2mqtt/+/state")
            self.availabiltyCheckCounter = 2
        else:
            self.availabiltyCheckCounter -= 1

        self.fetch_zigbee_state()
        self.fetch_zigbee_devices()
        self.update_database_list()

        if self.manualOverrideTimer > 0:
            self.manualOverrideTimer -= 1
        else:
            self.manualOverrideTimer = 0
            self.manualOverrideActive = False

        self.client.loop(timeout=1.0)  # Handle MQTT network events

        scheduler_mqtt.enter(1, 1, self.mainloop, (scheduler_mqtt,))

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def control_joining(self, enable):
        TOPIC = "zigbee2mqtt/bridge/request/permit_join"
        payload = '{"value": true}' if enable else '{"value": false}'
        self.client.publish(TOPIC, payload)

    def toggleOutletWithTimer(self, ieee_address, timer):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = f'{{"state": "TOGGLE"}}'
        self.client.publish(TOPIC, payload)
        for i in range(timer):
            time.sleep(1)
            self.client.publish(TOPIC, payload)

    def switch_on(self, ieee_address):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = '{"state": "ON"}'
        self.manualOverrideTimer = 10
        self.client.publish(TOPIC, payload)
        self.manualOverrideActive = True

    def switch_off(self, ieee_address):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = '{"state": "OFF"}'
        self.manualOverrideTimer = 10
        self.client.publish(TOPIC, payload)
        self.manualOverrideActive = True

    def setFridgeState(self, state):
        TOPIC = f"zigbee2mqtt/{self.fridgeSocketID}/set"
        payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
        self.client.publish(TOPIC, payload)

    def setLightState(self, state):
        if self.manualOverrideActive:
            return
        else:
            TOPIC = f"zigbee2mqtt/{self.lightSocketID}/set"
            payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
            self.client.publish(TOPIC, payload)

    def get_devices(self):
        return self.devices

# # Usage Example
# mqtt_interface = MQTT_Interface("broker.hivemq.com", 1883, "user", "password")
# mqtt_interface.scheduler.enter(1, 1, mqtt_interface.mainloop)
# mqtt_interface.scheduler.run()
