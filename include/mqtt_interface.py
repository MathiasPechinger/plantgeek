import paho.mqtt.client as mqtt
import json
import time
import requests
import sched
import threading

from enum import Enum

class DeviceType(Enum):
    LIGHT = 0
    FRIDGE = 1
    CO2 = 2

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
        self.lightSocket = SocketDevice(DeviceType.LIGHT)
        self.fridgeSocket = SocketDevice(DeviceType.FRIDGE)
        self.co2Socket = SocketDevice(DeviceType.CO2)
        self.devices = [self.lightSocket, self.fridgeSocket, self.co2Socket]
        self.initDone = False
        self.devicesHealthy = False

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

    # This function is used to update the list of devices in the database
    # todo this is not modular, it should be done in a better way
    def update_database_list(self):
        # print("Updating database list")
        try:
            matching_devices = []
            for device in self.zigbeeDevices:
                ieee_address = device.get("ieeeAddr")
                for state_addr in self.zigbeeState:
                    if state_addr == ieee_address:
                        matching_devices.append(device)
                        break


            states = {device_id: info['state'] for device_id, info in self.zigbeeState.items()}
            print("States: ", states)


            if len(matching_devices) == 1:
                self.devices[0].friendly_name = matching_devices[0].get("ieeeAddr")
            elif len(matching_devices) == 2:
                self.devices[0].friendly_name = matching_devices[0].get("ieeeAddr")
                self.devices[1].friendly_name = matching_devices[1].get("ieeeAddr")
            elif len(matching_devices) == 3:
                self.devices[0].friendly_name = matching_devices[0].get("ieeeAddr")
                self.devices[1].friendly_name = matching_devices[1].get("ieeeAddr")
                self.devices[2].friendly_name = matching_devices[2].get("ieeeAddr")

        except Exception as e:
            print(f"Error in update_database_list: {e}")
            
    def requestDeviceStateUpdate(self, friendly_name):
        TOPIC = f"zigbee2mqtt/{friendly_name}/get"
        payload = '{"state": ""}'
        self.publish(TOPIC, payload)
        SUB_TOPIC = f"zigbee2mqtt/{friendly_name}"
        # SUB_TOPIC = "#" # good for debugging, check all messages
        self.client.subscribe(SUB_TOPIC)
        
        
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
                    # print("Time diffrence: ", timeDiffrence)
                    if device.internalLastSeen is not None and timeDiffrence > TIMEOUT_THRESHOLD:
                        device.availability = False
                    else:
                        device.availability = True
                    # print("Device: ", device.friendly_name, "Availability: ", device.availability)
                else:
                    device.availability = False
                    
                # print("Device: ", device.friendly_name, "Availability: ", device.availability)
                    
                
        return None
    
    def checkBridgeHealth(self):
        for device in self.devices:
            if not device.availability:
                self.devicesHealthy = False
                return False
            elif self.devices[0].availability == True and self.devices[1].availability == True and self.devices[2].availability == True:
                self.devicesHealthy = True
                return True
                    

    def mainloop(self, scheduler_mqtt):
        if self.availabiltyCheckCounter <= 0:
            # self.client.subscribe("zigbee2mqtt/+/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.devices[0].friendly_name}/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.devices[1].friendly_name}/availability")
            self.client.subscribe(f"zigbee2mqtt/{self.devices[2].friendly_name}/availability")
            # self.client.subscribe("zigbee2mqtt/bridge/devices") # get device information

            self.availabiltyCheckCounter = 2
        else:
            self.availabiltyCheckCounter -= 1

        self.requestDeviceStateUpdate(self.devices[0].friendly_name)
        self.requestDeviceStateUpdate(self.devices[1].friendly_name)
        self.requestDeviceStateUpdate(self.devices[2].friendly_name)
        
        self.checkDeviceAvailability(self.devices[0].friendly_name)
        self.checkDeviceAvailability(self.devices[1].friendly_name)
        self.checkDeviceAvailability(self.devices[2].friendly_name)
        
        # add checks for this some other time
        # self.publish('zigbee2mqtt/bridge/request/health_check', '')
        # self.client.subscribe('zigbee2mqtt/bridge/response/health_check')
        
        # # Print last seen for all devices
        # for device in self.devices:
            # print(f"{device.friendly_name} - Last Seen: {device.internalLastSeen}")
        
        

        self.fetch_zigbee_state()
        self.fetch_zigbee_devices()
        
        if not self.initDone:
            self.update_database_list()
            self.initDone = True

        # Check if manual override is active
        for device in self.devices:
            if device.manualOverrideTimer > 0:
                device.manualOverrideTimer -= 1
            else:
                device.manualOverrideTimer = 0
                device.manualOverrideActive = False
                
        healthy = self.checkBridgeHealth()
        if not healthy:
            print("Bridge is not healthy!")
            print("Shutting down alle sockets, with manual override")
            self.switch_off(self.devices[0].friendly_name)
            self.switch_off(self.devices[1].friendly_name)
            self.switch_off(self.devices[2].friendly_name)
            # todo restart the system in correct states!!
        
        print("--------------------------------------------------")
        print("Devices healthy: ", self.devicesHealthy)
        print("Devices availability: ", self.devices[0].availability, self.devices[1].availability, self.devices[2].availability)
        print("Devices state: ", self.devices[0].state, self.devices[1].state, self.devices[2].state)
        print("Devices manual override: ", self.devices[0].manualOverrideActive, self.devices[1].manualOverrideActive, self.devices[2].manualOverrideActive)
        print("Devices manual override timer: ", self.devices[0].manualOverrideTimer, self.devices[1].manualOverrideTimer, self.devices[2].manualOverrideTimer)
        print("Devices friendly name: ", self.devices[0].friendly_name, self.devices[1].friendly_name, self.devices[2].friendly_name)
        print("--------------------------------------------------")
        
            

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
        deviceFound = False
        for device in self.devices:
            if device.friendly_name == ieee_address:
                device.state = True
                device.manualOverrideTimer = 10
                device.manualOverrideActive = True
                self.client.publish(TOPIC, payload)
                deviceFound = True
        if not deviceFound:
            print("ERROR: Device not found")

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
            print("ERROR: Device not found")

    def setFridgeState(self, state):
        if self.devices[1].friendly_name == "":
            # No light socket found, intializing
            print("No fridge socket found")
            return False
        else:
            if self.devices[1].manualOverrideActive:
                # Light is in manual override mode
                print("Fridge is in manual override mode")
                pass
            else:
                TOPIC = f"zigbee2mqtt/{self.devices[1].friendly_name}/set"
                payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
                self.client.publish(TOPIC, payload)
                self.devices[1].state = state
            return True

    def getFridgeState(self):
        return self.devices[1].state

    def getLightState(self):
        return self.devices[0].state

    def setLightState(self, state):
        if self.devices[0].friendly_name == "":
            # No light socket found, intializing
            print("No light socket found")
            return False
        else:
            if self.devices[0].manualOverrideActive:
                # Light is in manual override mode
                print("Light is in manual override mode")
                pass
            else:
                TOPIC = f"zigbee2mqtt/{self.devices[0].friendly_name}/set"
                payload = '{"state": "ON"}' if state else '{"state": "OFF"}'
                self.client.publish(TOPIC, payload)
                self.devices[0].state = state
            return True

    # def get_devices(self):
    #     return self.devices
