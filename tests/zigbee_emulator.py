import paho.mqtt.client as mqtt
import json
import time
import random
import sys

class ZigbeeEmulator:
    def __init__(self, device_to_fail=None, fail_after_seconds=3):
        # MQTT setup
        try:
            self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION1)
        except:
            self.client = mqtt.Client()
        
        self.client.username_pw_set("mqtt", "mqtt")
        self.client.connect("localhost", 1883, 60)
        
        self.device_to_fail = device_to_fail
        self.fail_after_seconds = fail_after_seconds
        self.start_time = time.time()
        
        # Define emulated devices
        self.devices = [
            {
                "friendly_name": "light_socket",
                "ieee_address": "0xf0d1b8be240845b1",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0,
                "active": True
            },
            {
                "friendly_name": "fridge_socket",
                "ieee_address": "0xf0d1b8be24085e85",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0,
                "active": True
            },
            {
                "friendly_name": "co2_socket",
                "ieee_address": "0xf0d1b8be24085c50",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0,
                "active": True
            },
            {
                "friendly_name": "heater_socket",
                "ieee_address": "0xf0d1b8be24084fb6",
                "type": "Router",
                "state": "OFF",
                "voltage": 230,
                "power": 0,
                "active": True
            }
        ]

    def publish_device_list(self):
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
            if device["active"]:
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
            if device["active"]:
                topic = f"zigbee2mqtt/{device['ieee_address']}/availability"
                self.client.publish(topic, "online")

    def start(self):
        self.client.loop_start()
        while True:
            try:
                # Check if it's time to fail the specified device
                if self.device_to_fail is not None:
                    if time.time() - self.start_time > self.fail_after_seconds:
                        self.devices[self.device_to_fail]["active"] = False
                
                self.publish_device_list()
                self.publish_device_states()
                self.publish_availability()
                
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
    device_to_fail = int(sys.argv[1]) if len(sys.argv) > 1 else None
    emulator = ZigbeeEmulator(device_to_fail)
    emulator.start()