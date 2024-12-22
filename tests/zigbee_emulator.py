import paho.mqtt.client as mqtt
import json
import time
import random

class ZigbeeEmulator:
    def __init__(self):
        # MQTT setup
        self.client = mqtt.Client()
        self.client.username_pw_set("mqtt", "mqtt")  # Update with your credentials
        self.client.connect("localhost", 1883, 60)
        
        # Define emulated devices
        self.devices = [
            {
                "friendly_name": "light_socket",
                "ieee_address": "0x00124b00250c256f",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0
            },
            {
                "friendly_name": "fridge_socket",
                "ieee_address": "0x00124b00250c257a",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0
            },
            {
                "friendly_name": "co2_socket",
                "ieee_address": "0x00124b00250c258b",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0
            },
            {
                "friendly_name": "heater_socket",
                "ieee_address": "0x00124b00250c259c",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0
            }
        ]

    def publish_device_list(self):
        # Add coordinator to the list
        full_list = [
            {
                "friendly_name": "Coordinator",
                "ieee_address": "0x00124b00250c2500",
                "type": "Coordinator"
            }
        ] + self.devices
        
        self.client.publish("zigbee2mqtt/bridge/devices", json.dumps(full_list))

    def publish_device_states(self):
        for device in self.devices:
            topic = f"zigbee2mqtt/{device['ieee_address']}"
            state = {
                "state": device["state"],
                "voltage": device["voltage"],
                "power": device["power"],
                "linkquality": random.randint(0, 100)
            }
            self.client.publish(topic, json.dumps(state))

    def publish_availability(self):
        for device in self.devices:
            topic = f"zigbee2mqtt/{device['ieee_address']}/availability"
            self.client.publish(topic, "online")

    def start(self):
        self.client.loop_start()
        
        while True:
            try:
                # Publish device list periodically
                self.publish_device_list()
                
                # Publish device states
                self.publish_device_states()
                
                # Publish availability
                self.publish_availability()
                
                # Random state changes to simulate activity
                if random.random() < 0.1:  # 10% chance of state change
                    device = random.choice(self.devices)
                    device["state"] = "ON" if device["state"] == "OFF" else "OFF"
                    device["power"] = random.randint(0, 100) if device["state"] == "ON" else 0
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                print("Stopping emulator...")
                self.client.loop_stop()
                self.client.disconnect()
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(5)

if __name__ == "__main__":
    emulator = ZigbeeEmulator()
    emulator.start() 