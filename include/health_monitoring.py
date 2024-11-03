import time

class HealthMonitor:
    def __init__(self):
        self.systemHealthy = False
        self.systemOverheated = False
        self.initDone = False
        self.previousTemperature = None
        self.temperatureFrozenTimeout = 300 #5 minutes
        self.temperatureFrozenCounter = 0
        self.overheatTemperature = 33.5
        self.overheatHysteresis = 1.0
        
    def check_status(self, sc, mqtt_interface, sensorData, zigbeeActivated):
        # Add your health check logic here
        # For example, you can check the status of various components or services
        # and update the self.status accordingly
        
        if not self.initDone:
            self.initDone = True
            self.systemHealthy = True
            self.previousTemperature = sensorData.currentTemperature
            sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData, zigbeeActivated,))
            return
        
        # print("Checking system status...")
        
        self.systemHealthy = True
        
        # check sensor data availability
        if sensorData.currentTemperature == None:
            self.systemHealthy = False
            print("Temperature sensor data invalid.")
            sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData, zigbeeActivated,))
            return
            
        if sensorData.lastTimestamp == None:
            self.systemHealthy = False
            print("Sensor data no timestamp not updated.")
            sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData, zigbeeActivated,))
            return
        
        if zigbeeActivated:
            if not mqtt_interface.devicesHealthy:
                self.systemHealthy = False
                print("Zigbee devices not healthy.")
            
        current_time = time.time()
        if sensorData.lastTimestamp == None:
            self.systemHealthy = False
            print("Sensor data not updated.")
        elif current_time - sensorData.lastTimestamp > 120:
            self.systemHealthy = False
            print("Sensor data not updated for more than 60 seconds.")
        
        # detect frozen sensor data
        if sensorData.currentTemperature == self.previousTemperature:
            self.temperatureFrozenCounter += 1
            if self.temperatureFrozenCounter > self.temperatureFrozenTimeout:
                self.systemHealthy = False
                print("Temperature sensor data frozen.")
        else:
            self.temperatureFrozenCounter = 0
            self.previousTemperature = sensorData.currentTemperature
            
            
        if sensorData.currentTemperature > self.overheatTemperature:
            self.systemOverheated = True
            
        if self.systemOverheated:
            print("WARNTING: System overheated! Reduce energy input (light, dehumidifier)!")
            if sensorData.currentTemperature < self.overheatTemperature - self.overheatHysteresis:
                self.systemOverheated = False
            
        # print("System healthy: ", self.systemHealthy)
        sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData, zigbeeActivated,))
        return

    def get_status(self):
        return self.systemHealthy

    # def set_status(self, status):
    #     self.status = status