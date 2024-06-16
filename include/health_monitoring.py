import time

class HealthMonitor:
    def __init__(self):
        self.systemHealthy = False
        self.initDone = False
        self.previousTemperature = None
        self.temperatureFrozenTimeout = 60
        self.temperatureFrozenCounter = 0
        
    def check_status(self, sc, mqtt_interface, sensorData):
        # Add your health check logic here
        # For example, you can check the status of various components or services
        # and update the self.status accordingly
        
        if not self.initDone:
            self.initDone = True
            self.systemHealthy = True
            self.previousTemperature = sensorData.currentTemperature
            sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData,))
            return
        
        # print("Checking system status...")
        
        self.systemHealthy = True
        
        if not mqtt_interface.devicesHealthy:
            self.systemHealthy = False
            print("MQTT devices not healthy.")
            
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
            
        # print("System healthy: ", self.systemHealthy)
        sc.enter(1, 1, self.check_status,(sc,mqtt_interface, sensorData,))

    def get_status(self):
        return self.systemHealthy

    # def set_status(self, status):
    #     self.status = status