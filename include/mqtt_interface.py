import paho.mqtt.client as mqtt
import json
import time
import requests
import sched
import threading
import os

from enum import Enum

class DeviceType(Enum):
    LIGHT = 0
    FRIDGE = 1
    CO2 = 2
    HEATER = 3

class SocketDevice:
    def __init__(self, device_type):
        self.device_type = device_type
        self.friendly_name = ""
        self.availability = False
        self.state = False
        self.internalLastSeen = None
        self.manualOverrideTimer = 0
        self.manualOverrideActive = False

    def __str__(self):
        return f"Device: {self.friendly_name}, Availability: {self.availability}"

class MQTT_Interface:
    def __init__(self, broker, port, user, password):
        self.broker = broker
        self.port = port
        self.user = user
        self.password = password
        self.client = mqtt.Client()
        self.client.username_pw_set(user, password)
        self.client.on_connect = self.on_connect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
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
        self.start_mqtt_loop()
        
        # Load device configuration before creating socket devices
        self.device_config = self.load_device_config()
        
        # Create socket devices with configured friendly names
        self.lightSocket = self.create_socket_device(DeviceType.LIGHT)
        self.fridgeSocket = self.create_socket_device(DeviceType.FRIDGE)
        self.co2Socket = self.create_socket_device(DeviceType.CO2)
        self.heater = self.create_socket_device(DeviceType.HEATER)
        self.devices = [self.lightSocket, self.fridgeSocket, self.co2Socket, self.heater]
        self.initDone = False
        self.devicesHealthy = False
        
        # Add a list to store all discovered devices
        self.discovered_devices = []

    def start_mqtt_loop(self):
        mqtt_thread = threading.Thread(target=self.client.loop_forever)
        mqtt_thread.start()

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("Connected to MQTT Broker")
            self.client.subscribe("zigbee2mqtt/+/availability")
            self.client.subscribe("zigbee2mqtt/+/state")
        else:
            print(f"Failed to connect, return code {rc}")

    def on_disconnect(self, client, userdata, rc):
        print("Disconnected from MQTT Broker. Attempting to reconnect...")
        while True:
            try:
                self.client.reconnect()
                break
            except:
                time.sleep(5)

    def on_publish(self, client, userdata, mid):
        # print("Message published")
        pass

    def on_message(self, client, userdata, msg):
        try:
            # print(f"Received `{msg.payload.decode()}` from `{msg.topic}` topic")
            
            if msg.topic == "zigbee2mqtt/bridge/devices":
                payload = msg.payload.decode()
                devices = json.loads(payload)
                
                # Clear existing discovered devices
                self.discovered_devices = []
                
                # Store all non-coordinator devices
                for device in devices:
                    if device['type'] != 'Coordinator':
                        device_info = {
                            'friendly_name': device.get('friendly_name', ''),
                            'ieee_address': device.get('ieee_address', ''),
                            'type': device.get('type', ''),
                            'model': device.get('model', ''),
                            'manufacturer': device.get('manufacturer', ''),
                            'description': device.get('description', '')
                        }
                        self.discovered_devices.append(device_info)
                        
                # Verify that configured devices exist in discovered devices
                self.verify_configured_devices()
                
            # Availability messages
            if "availability" in msg.topic:
                device_name = msg.topic.split('/')[1]
                status = msg.payload.decode()
                if status == "online":
                    statusBool = True
                else:
                    statusBool = False
                for device in self.devices:
                    if device.friendly_name == device_name:
                        # THIS DOES NOT WORK, I DONT KNOW WHY
                        # THE MQTT BACKEND DOES NOT GIVE THE CORRECT AVAILABILITY STATUS
                        # device.availability = statusBool
                        # print(f"Device: {device.friendly_name}, Availability: {device.availability}")
                        break
            else:
                # process other messages
                # my sockets do not attach the "/state" so i have to check for the device name
                messagePayload = msg.payload.decode()
                device_name = msg.topic.split('/')[1]
                for device in self.devices:
                    if device.friendly_name == device_name:
                        state = json.loads(messagePayload).get("state")
                        if state is not None:
                            if state == "ON":
                                device.state = True
                            else:
                                device.state = False
                            device.internalLastSeen = time.time()
                            # print(f"Device: {device.friendly_name}, State: {device.state}, Last seen: {device.internalLastSeen}")
                        else:
                            print("Error: No state found in payload")
                        break
        except Exception as e:
            print(f"Error in on_message: {e}, Topic: {msg.topic}, Payload: {msg.payload}")
            
    def fetchZigbeeDevicesFromBridge(self):
        TOPIC = f"zigbee2mqtt/bridge/request/devices"
        payload = '{" "}'
        self.publish(TOPIC, payload)
        SUB_TOPIC = f"zigbee2mqtt/bridge/devices"
        # SUB_TOPIC = "#" # good for debugging, check all messages
        # code for extraction here
        self.client.subscribe(SUB_TOPIC)
            
    def requestDeviceStateUpdate(self, friendly_name):
        TOPIC = f"zigbee2mqtt/{friendly_name}/get"
        payload = '{"state": ""}'
        self.publish(TOPIC, payload)
        SUB_TOPIC = f"zigbee2mqtt/{friendly_name}"
        # SUB_TOPIC = "#" # good for debugging, check all messages
        self.client.subscribe(SUB_TOPIC)
        
    def getDevices (self):
        return self.devices
    
    def getDiscoveredDevices(self):
        return self.discovered_devices
        
    def getDeviceState(self, friendly_name):
        for device in self.devices:
            if device.friendly_name == friendly_name:
                return device.state
        return None
    
    def checkDeviceAvailability(self, friendly_name):
        for device in self.devices:
            TIMEOUT_THRESHOLD = 20
            if device.friendly_name == friendly_name:
                current_time = time.time()
                if device.internalLastSeen is not None:
                    timeDiffrence = current_time - device.internalLastSeen
                    if device.internalLastSeen is not None and timeDiffrence > TIMEOUT_THRESHOLD:
                        device.availability = False
                    else:
                        device.availability = True
                    # print("Device: ", device.friendly_name, "Availability: ", device.availability)
                else:
                    device.availability = False
                    
                # print("Device: ", device.friendly_name, "Availability: ", device.availability)
        return None
    
    
    def updateBridgeHealth(self):
        for device in self.devices:
            if not device.availability:
                self.devicesHealthy = False
            elif (self.lightSocket.availability == True and 
                  self.fridgeSocket.availability == True and 
                  self.co2Socket.availability == True and 
                  self.heater.availability == True):
                self.devicesHealthy = True
                
                    
    def mainloop(self, scheduler_mqtt, systemHealth):
        if self.availabiltyCheckCounter <= 0:
            # self.client.subscribe("zigbee2mqtt/+/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.lightSocket.friendly_name}/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.fridgeSocket.friendly_name}/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.co2Socket.friendly_name}/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.heater.friendly_name}/availability")
            # self.client.subscribe("zigbee2mqtt/bridge/devices") # get device information
            self.fetchZigbeeDevicesFromBridge()
            self.availabiltyCheckCounter = 2
        else:
            self.availabiltyCheckCounter -= 1

        self.requestDeviceStateUpdate(self.lightSocket.friendly_name)
        self.requestDeviceStateUpdate(self.fridgeSocket.friendly_name)
        self.requestDeviceStateUpdate(self.co2Socket.friendly_name)
        self.requestDeviceStateUpdate(self.heater.friendly_name)
        
        self.checkDeviceAvailability(self.lightSocket.friendly_name)
        self.checkDeviceAvailability(self.fridgeSocket.friendly_name)
        self.checkDeviceAvailability(self.co2Socket.friendly_name)
        self.checkDeviceAvailability(self.heater.friendly_name)
        
        if not self.initDone:
            self.fetchZigbeeDevicesFromBridge()
            self.initDone = True
        
        # Check if manual override is active
        for device in self.devices:
            if device.manualOverrideTimer > 0:
                device.manualOverrideTimer -= 1
            else:
                device.manualOverrideTimer = 0
                device.manualOverrideActive = False
        
        
        self.updateBridgeHealth()
        
        if not systemHealth.systemHealthy:
            self.switch_off(self.lightSocket.friendly_name)
            self.switch_off(self.fridgeSocket.friendly_name)
            self.switch_off(self.co2Socket.friendly_name)
            self.switch_off(self.heater.friendly_name)
            
        if systemHealth.systemOverheated:
            self.switch_off(self.lightSocket.friendly_name)
            self.switch_off(self.heater.friendly_name)
        
        mqttInterfaceDebugging = False
        if (mqttInterfaceDebugging):
            print("--------------------------------------------------")
            print("Devices healthy: ", self.devicesHealthy)
            print("System oveheated: ", systemHealth.systemOverheated)
            print("Devices availability: ", self.lightSocket.availability, self.fridgeSocket.availability, self.co2Socket.availability, self.heater.availability)
            print("Devices state: ", self.lightSocket.state, self.fridgeSocket.state, self.co2Socket.state , self.heater.state)
            print("Devices manual override: ", self.lightSocket.manualOverrideActive, self.fridgeSocket.manualOverrideActive, self.co2Socket.manualOverrideActive, self.heater.manualOverrideActive)
            print("Devices manual override timer: ", self.lightSocket.manualOverrideTimer, self.fridgeSocket.manualOverrideTimer, self.co2Socket.manualOverrideTimer, self.heater.manualOverrideTimer)
            print("Devices friendly name: ", self.lightSocket.friendly_name, self.fridgeSocket.friendly_name, self.co2Socket.friendly_name, self.heater.friendly_name)
            print("--------------------------------------------------")
        
        scheduler_mqtt.enter(1, 1, self.mainloop, (scheduler_mqtt, systemHealth,))

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
        deviceFound = False
        print("-------> switch_on")
        for device in self.devices:
            if device.friendly_name == ieee_address:
                device.state = True
                device.manualOverrideTimer = 10
                device.manualOverrideActive = True
                self.client.publish(TOPIC, payload)
                deviceFound = True
        if not deviceFound:
            self.client.publish(TOPIC, payload)
            print("WARN: Device not assigned or not found")

    def switch_off(self, ieee_address):
        TOPIC = f"zigbee2mqtt/{ieee_address}/set"
        payload = '{"state": "OFF"}'
        deviceFound = False
        for device in self.devices:
            if device.friendly_name == ieee_address:
                device.state = False
                device.manualOverrideTimer = 10
                device.manualOverrideActive = True
                self.client.publish(TOPIC, payload)
                deviceFound = True
        if not deviceFound:
            self.client.publish(TOPIC, payload)
            print("WARN: Device not assigned or not found")

    def setFridgeState(self, state):
        if self.fridgeSocket.friendly_name == "":
            # No light socket found, intializing
            # print("No fridge socket found")
            return False
        else:
            if self.fridgeSocket.manualOverrideActive:
                # print("Fridge is in manual override mode")
                pass
            else:
                self.switchLedvanceSocket_4058075729261(self.fridgeSocket.friendly_name, state, "60", "10")
            return True
        
    def setHeaterState(self, state):
        if self.heater.friendly_name == "":
            # No light socket found, intializing
            print("No heater socket found")
            return False
        else:
            if self.heater.manualOverrideActive:
                # print("Heater is in manual override mode")
                pass
            else:
                self.switchLedvanceSocket_4058075729261(self.heater.friendly_name, state, "60", "10")
            return True
        
    def getHeaterState(self):
        return self.heater.state

    def getFridgeState(self):
        return self.fridgeSocket.state
    
    def getCO2State(self):
        return self.co2Socket.state
    
    def setCO2State(self, state):
        if self.co2Socket.friendly_name == "":
            # print("No co2 socket found")
            return False
        else:
            if self.co2Socket.manualOverrideActive:
                # print("CO2 is in manual override mode")
                pass
            else:
                # TOPIC = f"zigbee2mqtt/{self.co2Socket.friendly_name}/set"
                # payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
                # self.client.publish(TOPIC, payload)
                # self.co2Socket.state = state
                self.switchLedvanceSocket_4058075729261(self.co2Socket.friendly_name, state, "60", "10")
            return True
        
    # Source: https://www.zigbee2mqtt.io/devices/4058075729261.html
    # When setting the state to ON, it might be possible to specify an automatic shutoff after a certain amount of time. 
    # To do this add an additional property on_time to the payload which is the time in seconds the state should remain on. 
    # Additionnaly an off_wait_time property can be added to the payload to specify the cooldown time in seconds when the 
    # switch will not answer to other on with timed off commands. Support depend on the switch firmware. Some devices might 
    # require both on_time and off_wait_time to work Examples : 
    # {"state" : "ON", "on_time": 300}, 
    # {"state" : "ON", "on_time": 300, "off_wait_time": 120}   
    
    def switchLedvanceSocket_4058075729261(self, friendly_name, state, on_time, off_wait_time):
        # TOPIC = f"zigbee2mqtt/{self.co2Socket.friendly_name}/set"
        # payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
        
        
        
        TOPIC = f"zigbee2mqtt/{friendly_name}/set"
        if state:
            # payload = '{"state": "ON", "on_time": 10, "off_wait_time": 10}' #  on_time prevents sleeping error if system is not healthy
            payload = '{"state": "ON", "on_time":' + on_time + ', "off_wait_time":' + off_wait_time + '}' #  on_time prevents sleeping error if system is not healthy
            # print("CO2 valve opened")
        else:
            # print("CO2 valve closed")
            payload = '{"state": "OFF"}'
        self.client.publish(TOPIC, payload)
        
    def switchNousSocket_A1Z(self, friendly_name, state, off_wait_time):
        # TOPIC = f"zigbee2mqtt/{self.co2Socket.friendly_name}/set"
        # payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
        TOPIC = f"zigbee2mqtt/{friendly_name}/set"
        if state:
            payload = '{"state": "ON"}' 
        else:
            payload = '{"state": "OFF"}'
        self.client.publish(TOPIC, payload)
        
        # Automatic shutdown if no message is received after 10 seconds // todo reimplementation if this is ever used again
        # self.setDeviceAutoOffCountdownSocketA1Z(friendly_name, off_wait_time)

    def getLightState(self):
        return self.lightSocket.state

    def setLightState(self, state):
        if self.lightSocket.friendly_name == "":
            # No light socket found, intializing
            # print("No light socket found")
            return False
        else:
            if self.lightSocket.manualOverrideActive:
                print("System Startup/Manual Override")
                pass
            else:
                self.switchLedvanceSocket_4058075729261(self.lightSocket.friendly_name, state, "60", "10")
            return True

    def load_device_config(self):
        try:
            config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'device_setup.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config['devices']
        except Exception as e:
            print(f"Error loading device configuration: {e}")
            return {}
            
    def create_socket_device(self, device_type: DeviceType) -> SocketDevice:
        device = SocketDevice(device_type)
        try:
            # Get friendly name from config
            friendly_name = self.device_config[device_type.name]['friendly_name']
            device.friendly_name = friendly_name
        except KeyError:
            print(f"Warning: No configuration found for {device_type.name}")
            device.friendly_name = ""
        return device

    def verify_configured_devices(self):
        discovered_addresses = [device['ieee_address'] for device in self.discovered_devices]
        
        for device in self.devices:
            if device.friendly_name:
                if device.friendly_name not in discovered_addresses:
                    print(f"Warning: Configured device {device.device_type.name} "
                          f"with address {device.friendly_name} not found in network")

    def reload_device_config(self):
        # Load new device configuration
        self.device_config = self.load_device_config()
        
        # Update friendly names for existing socket devices
        for device in self.devices:
            device_type = device.device_type.name  # Get the enum name (LIGHT, FRIDGE, etc.)
            if device_type in self.device_config:
                device.friendly_name = self.device_config[device_type]['friendly_name']
            else:
                device.friendly_name = ""
                device.availability = False
                device.state = False
                device.internalLastSeen = None
                device.manualOverrideTimer = 0
                device.manualOverrideActive = False

    # def get_devices(self):
    #     return self.devices
