import paho.mqtt.client as mqtt
import json
import time

class MQTT_Interface:
    def __init__(self, broker, port, user, password):
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.devices = []  # Initialize devices list
        self.client = mqtt.Client()
        self.client.username_pw_set(user, password)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()  # Start the loop in a separate thread

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            # Subscribe to the devices topic
            self.client.subscribe("zigbee2mqtt/bridge/devices")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_publish(self, client, userdata, mid):
        print("Message Published")

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload)
            # print(f"Received message: {json.dumps(payload, indent=2)}")  # Print the received payload
            if msg.topic == "zigbee2mqtt/bridge/devices":
                # self.devices = self.extract_device_info(payload)
                self.devices = self.extract_device_info_extended(payload)
                print("Devices list updated")
        except json.JSONDecodeError as e:
            print(f"Failed to decode JSON: {e}")
        except Exception as e:
            print(f"Error in on_message: {e}")

    def extract_device_info(self, devices):
        extracted_info = []
        for device in devices:
            info = {
                "friendly_name": device.get("friendly_name")
            }
            extracted_info.append(info)
        return extracted_info
    
    def extract_device_info_extended(self, devices):
        extracted_info = []
        for device in devices:
            info = {
                "friendly_name": device.get("friendly_name"),
                "ieee_address": device.get("ieee_address"),
                "type": device.get("type"),
                "model": device.get("definition", {}).get("model"),
                "vendor": device.get("definition", {}).get("vendor"),
                "power_source": device.get("power_source"),
                "description": device.get("definition", {}).get("description")
            }
            extracted_info.append(info)
        return extracted_info

    def publish(self, topic, payload):
        self.client.publish(topic, payload)

    def loop_forever(self):
        try:
            self.client.loop_forever()
        except Exception as e:
            print(f"MQTT Interface error: {e}")

    def control_joining(self, enable):
        TOPIC = "zigbee2mqtt/bridge/request/permit_join"
        payload = '{"value": true}' if enable else '{"value": false}'
        self.client.publish(TOPIC, payload)

    def get_devices(self):
        return self.devices

    def print_devices(self):
        for device in self.devices:
            print(f"Friendly Name: {device['friendly_name']}")
            print(f"IEEE Address: {device['ieee_address']}")
            print(f"Type: {device['type']}")
            print(f"Model: {device['model']}")
            print(f"Vendor: {device['vendor']}")
            print(f"Power Source: {device['power_source']}")
            print(f"Description: {device['description']}")
            print("-----")

