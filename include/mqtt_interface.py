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
        # self.client.on_message = self.on_message
        self.client.connect(broker, port, 60)
        self.client.loop_start()  # Start the loop in a separate thread
        self.manualOverrideTimer = 0

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            # Subscribe to the devices topic
            self.client.subscribe("zigbee2mqtt/bridge/devices")
            self.client.subscribe("zigbee2mqtt/+/availability")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_publish(self, client, userdata, mid):
        # print("Message Published")
        pass
        
    def on_message(self, client, userdata, msg):
        if "availability" in msg.topic:
            device_name = msg.topic.split('/')[1]
            status = msg.payload.decode()
            print(f"Device {device_name} is {status}")
            # Process the device status here (e.g., update your database)



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
    
    
    def mainloop(self,scheduler_mqtt):
        # self.publish("zigbee2mqtt/bridge/devices", "")
        self.client.publish("zigbee2mqtt/bridge/request/devices", "") # Request the devices list but it does not really work
        # self.publish("zigbee2mqtt/0xa4c138c6714a8120/set", '{"state": "ON"}')
        
        # If we want to control the sockets manually instead of using the schedule, we reste them here to normal schedule after some time
        if self.manualOverrideTimer > 0:
            self.manualOverrideTimer -= 1
            print(f"Manual Override Timer: {self.manualOverrideTimer}")
        else:
            self.manualOverrideTimer = 0
        
        scheduler_mqtt.enter(5, 1, self.mainloop,(scheduler_mqtt,))

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
        
    def toggleOutletWithTimer(self, ieee_address, timer):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = f'{{"state": "TOGGLE"}}'
        self.client.publish(TOPIC, payload)
        for i in range(timer):
            time.sleep(1)  # Wait for 1 second
            self.client.publish(TOPIC, payload)  # Publish the toggle command

    def switch_on(self, ieee_address):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = '{"state": "ON"}'
        self.manualOverrideTimer = 1
        self.client.publish(TOPIC, payload)
        
    def switch_off(self, ieee_address):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = '{"state": "OFF"}'
        self.manualOverrideTimer = 1
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

