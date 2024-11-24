import time
from datetime import datetime
from typing import List, Optional
from .health_monitoring_errors import HealthError, HealthErrorCode

class HealthMonitor:
    def __init__(self):
        self.systemHealthy = False
        self.systemOverheated = False
        self.initDone = False
        self.previousTemperature = None
        self.temperatureFrozenTimeout = 300  # 5 minutes
        self.temperatureFrozenCounter = 0
        self.overheatTemperature = 33.5
        self.overheatHysteresis = 1.0
        self.active_errors: List[HealthError] = []
        self.error_history: List[HealthError] = []
        
    def add_error(self, code: HealthErrorCode, message: str) -> None:
        # Check if error with same code already exists in active errors
        for existing_error in self.active_errors:
            if existing_error.code == code:
                return  # Skip adding if error code already exists
        
        # Create new error and add to lists
        error = HealthError(
            code=code,
            message=message,
            timestamp=datetime.now()
        )
        self.active_errors.append(error)
        self.error_history.append(error)
        
    def resolve_error(self, code: HealthErrorCode) -> None:
        for error in self.active_errors:
            if error.code == code and not error.resolved:
                error.resolved = True
                error.resolved_timestamp = datetime.now()
                self.active_errors.remove(error)
                
    def get_active_errors(self) -> List[HealthError]:
        return self.active_errors
    
    def get_error_history(self) -> List[HealthError]:
        return self.error_history

    def check_status(self, sc, mqtt_interface, sensorData, zigbeeActivated):
        
        # print("Checking system status")
        if not self.initDone:
            self.initDone = True
            self.systemHealthy = True
            self.previousTemperature = sensorData.currentTemperature
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
        
        self.systemHealthy = True
        
        # Check sensor data availability
        if sensorData.currentTemperature is None:
            self.systemHealthy = False
            self.add_error(
                HealthErrorCode.TEMPERATURE_SENSOR_INVALID,
                "Temperature sensor data invalid"
            )
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
        else:
            self.resolve_error(HealthErrorCode.TEMPERATURE_SENSOR_INVALID)
            
        if sensorData.lastTimestamp is None:
            self.systemHealthy = False
            self.add_error(
                HealthErrorCode.TIMESTAMP_MISSING,
                "Sensor data timestamp missing"
            )
        else:
            self.resolve_error(HealthErrorCode.TIMESTAMP_MISSING)
        
        if zigbeeActivated and not mqtt_interface.devicesHealthy:
            self.systemHealthy = False
            self.add_error(
                HealthErrorCode.ZIGBEE_DEVICES_UNHEALTHY,
                "Zigbee devices not healthy"
            )
        elif zigbeeActivated:
            self.resolve_error(HealthErrorCode.ZIGBEE_DEVICES_UNHEALTHY)
        
        # Check sensor data freshness
        current_time = time.time()
        if sensorData.lastTimestamp and current_time - sensorData.lastTimestamp > 120:
            self.systemHealthy = False
            self.add_error(
                HealthErrorCode.SENSOR_DATA_NOT_UPDATED,
                "Sensor data not updated for more than 120 seconds"
            )
        else:
            self.resolve_error(HealthErrorCode.SENSOR_DATA_NOT_UPDATED)
        
        # Detect frozen sensor data
        if sensorData.currentTemperature == self.previousTemperature:
            self.temperatureFrozenCounter += 1
            if self.temperatureFrozenCounter > self.temperatureFrozenTimeout:
                self.systemHealthy = False
                self.add_error(
                    HealthErrorCode.TEMPERATURE_SENSOR_FROZEN,
                    "Temperature sensor data frozen"
                )
        else:
            self.temperatureFrozenCounter = 0
            self.previousTemperature = sensorData.currentTemperature
            self.resolve_error(HealthErrorCode.TEMPERATURE_SENSOR_FROZEN)
            
        # Check system temperature
        if sensorData.currentTemperature > self.overheatTemperature:
            self.systemOverheated = True
            self.add_error(
                HealthErrorCode.SYSTEM_OVERHEATED,
                f"System overheated! Temperature: {sensorData.currentTemperature}°C"
            )
        elif self.systemOverheated and sensorData.currentTemperature < self.overheatTemperature - self.overheatHysteresis:
            self.systemOverheated = False
            self.resolve_error(HealthErrorCode.SYSTEM_OVERHEATED)

        # print("System healthy:", self.systemHealthy)
        sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
        return

    def get_status(self):
        return self.systemHealthy

    # def set_status(self, status):
    #     self.status = status

    def clear_error_history(self) -> None:
        """Clear the error history while preserving active errors"""
        # Create a new list with only unresolved errors
        new_history = [error for error in self.error_history if not error.resolved]
        self.error_history = new_history