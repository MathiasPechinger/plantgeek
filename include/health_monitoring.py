import time
from datetime import datetime
from typing import List, Optional
from .health_monitoring_errors import HealthError, HealthErrorCode, HealthWarningCode, HealthWarning
import os

class ControlAccuracyMonitor:
    def __init__(self, config):
        # Check if we're in testing mode
        self.testing = os.environ.get('TESTING', '0') == '1'
        # Set window size based on testing mode
        self.window_size = 5 if self.testing else 60  # 5 readings for testing, 60 for production
        
        self.temp_threshold = 2.5  # °C deviation threshold
        self.co2_threshold = 1000   # ppm deviation threshold
        self.humidity_threshold = 10 # % deviation threshold
        
        # Load target values from config
        self.target_temp_day = float(config['TemperatureControl']['targetDayTemperature'])
        self.target_temp_night = float(config['TemperatureControl']['targetNightTemperature'])
        self.target_co2 = float(config['CO2Control']['targetValue'])
        self.target_humidity = float(config['HumidityControl']['targetHumidity'])
        
        # Initialize rolling windows
        self.temp_values = []
        self.co2_values = []
        self.humidity_values = []
        
    def add_measurement(self, temperature, co2, humidity):
        """Add new measurements to the rolling windows"""
        
        if temperature is not None:
            self.temp_values.append(temperature)
        if co2 is not None:
            self.co2_values.append(co2)
        if humidity is not None:
            self.humidity_values.append(humidity)
            
        # Keep window size fixed
        if len(self.temp_values) > self.window_size:
            self.temp_values.pop(0)
        if len(self.co2_values) > self.window_size:
            self.co2_values.pop(0)
        if len(self.humidity_values) > self.window_size:
            self.humidity_values.pop(0)
            
            
    def check_control_accuracy(self, is_day_time):
        """Check control accuracy and return list of (warning_code, message) tuples"""
        warnings = []
        
        # Temperature control check
        if len(self.temp_values) >= self.window_size:
            target_temp = self.target_temp_day if is_day_time else self.target_temp_night
            avg_temp = sum(self.temp_values) / len(self.temp_values)
            deviation = avg_temp - target_temp
            
            if deviation < -self.temp_threshold:
                warnings.append((HealthWarningCode.TEMPERATURE_CONTROL_LOW,
                             f"Temperature control below target: {avg_temp:.1f}°C vs target {target_temp}°C"))
            elif deviation > self.temp_threshold:
                warnings.append((HealthWarningCode.TEMPERATURE_CONTROL_HIGH,
                             f"Temperature control above target: {avg_temp:.1f}°C vs target {target_temp}°C"))
                
        # CO2 control check (only reasnabloe during day time)
        # if is_day_time:
        if len(self.co2_values) >= self.window_size:
            avg_co2 = sum(self.co2_values) / len(self.co2_values)
            deviation = avg_co2 - self.target_co2
            
            if deviation < -self.co2_threshold:
                warnings.append((HealthWarningCode.CO2_CONTROL_LOW,
                            f"CO2 control below target: {avg_co2:.0f}ppm vs target {self.target_co2}ppm"))
            elif deviation > self.co2_threshold:
                warnings.append((HealthWarningCode.CO2_CONTROL_HIGH,
                            f"CO2 control above target: {avg_co2:.0f}ppm vs target {self.target_co2}ppm"))
                
        # Humidity control check
        if len(self.humidity_values) >= self.window_size:
            avg_humidity = sum(self.humidity_values) / len(self.humidity_values)
            deviation = avg_humidity - self.target_humidity
            
            if deviation < -self.humidity_threshold:
                warnings.append((HealthWarningCode.HUMIDITY_CONTROL_LOW,
                             f"Humidity control below target: {avg_humidity:.1f}% vs target {self.target_humidity}%"))
            elif deviation > self.humidity_threshold:
                warnings.append((HealthWarningCode.HUMIDITY_CONTROL_HIGH,
                             f"Humidity control above target: {avg_humidity:.1f}% vs target {self.target_humidity}%"))
                
        return warnings

class HealthMonitor:
    def __init__(self, config):
        self.systemHealthy = False
        self.systemOverheated = False
        self.initDone = False
        self.previousTemperature = None
        # Check if we're in testing mode
        self.testing = os.environ.get('TESTING', '0') == '1'
        # Set timeout based on testing mode
        self.temperatureFrozenTimeout = 10 if self.testing else 300  # 20s for testing, 5 minutes for production
        self.temperatureFrozenCounter = 0
        self.overheatTemperature = 33.5
        self.overheatHysteresis = 1.0
        self.active_errors: List[HealthError] = []
        self.error_history: List[HealthError] = []
        self.warnings = []
        self.control_monitor = ControlAccuracyMonitor(config)
        self.debug = False  # Add debug flag
        
    def set_debug(self, debug_state: bool):
        """Enable or disable debug printing"""
        self.debug = debug_state
        
    def debug_print(self, message: str):
        """Print debug messages if debug is enabled"""
        if self.debug:
            print(f"[HealthMonitor Debug] {message}")

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
        self.debug_print(f"New error added: {code.name} - {message}")
        
    def resolve_error(self, code: HealthErrorCode) -> None:
        for error in self.active_errors:
            if error.code == code and not error.resolved:
                error.resolved = True
                error.resolved_timestamp = datetime.now()
                self.active_errors.remove(error)
                self.debug_print(f"Error resolved: {code.name}")

    def get_active_errors(self) -> List[HealthError]:
        return self.active_errors
    
    def get_error_history(self) -> List[HealthError]:
        return self.error_history

    def add_warning(self, code: HealthWarningCode, message: str):
        """Add or update a warning"""
        # Check if warning already exists
        existing_warning = next(
            (w for w in self.warnings if w.code == code and not w.resolved), 
            None
        )
        
        if existing_warning:
            # Update existing warning with new message and timestamp
            existing_warning.message = message
            existing_warning.timestamp = datetime.now()
            self.debug_print(f"Warning updated: {code.name} - {message}")
            return existing_warning
        else:
            # Create new warning if none exists
            warning = HealthWarning(
                code=code,
                message=message,
                timestamp=datetime.now()
            )
            self.warnings.append(warning)
            self.debug_print(f"New warning added: {code.name} - {message}")
            return warning
        return existing_warning

    def resolve_warning(self, code: HealthWarningCode):
        for warning in self.warnings:
            if warning.code == code and not warning.resolved:
                warning.resolved = True
                warning.resolved_timestamp = datetime.now()
                self.debug_print(f"Warning resolved: {code.name}")

    def get_active_warnings(self):
        return [w for w in self.warnings if not w.resolved]

    def check_status(self, sc, mqtt_interface, sensorData, zigbeeActivated):
        
        # print("Checking system status")
        if not self.initDone:
            self.initDone = True
            self.systemHealthy = True
            self.previousTemperature = sensorData.currentTemperature
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
        
        
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
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
        else:
            self.resolve_error(HealthErrorCode.TIMESTAMP_MISSING)
        
        if zigbeeActivated and not mqtt_interface.devicesHealthy:
            self.systemHealthy = False
            self.add_error(
                HealthErrorCode.ZIGBEE_DEVICES_UNHEALTHY,
                "Zigbee devices not healthy"
            )
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
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
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
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
                sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
                return
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
            sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
            return
        elif self.systemOverheated and sensorData.currentTemperature < self.overheatTemperature - self.overheatHysteresis:
            self.systemOverheated = False
            self.resolve_error(HealthErrorCode.SYSTEM_OVERHEATED)

        
        self.systemHealthy = True

        # Add current measurements to control monitor
        self.control_monitor.add_measurement(
            sensorData.currentTemperature,
            sensorData.currentCO2,
            sensorData.currentHumidity
        )

        # Check control accuracy (use light state to determine day/night)
        is_day_time = mqtt_interface.getLightState()
        control_warnings = self.control_monitor.check_control_accuracy(is_day_time)

        # Process any control accuracy warnings
        for warning_code, message in control_warnings:
            self.add_warning(warning_code, message)

        # Print current warnings (Debug)
        # self.print_active_warnings()

        # Resolve control warnings if they're not present in the current check
        all_control_codes = [
            HealthWarningCode.TEMPERATURE_CONTROL_LOW,
            HealthWarningCode.TEMPERATURE_CONTROL_HIGH,
            HealthWarningCode.CO2_CONTROL_LOW,
            HealthWarningCode.CO2_CONTROL_HIGH,
            HealthWarningCode.HUMIDITY_CONTROL_LOW,
            HealthWarningCode.HUMIDITY_CONTROL_HIGH
        ]

        current_warning_codes = [code for code, _ in control_warnings]
        for code in all_control_codes:
            if code not in current_warning_codes:
                self.resolve_warning(code)

        # print("System healthy:", self.systemHealthy)
        sc.enter(1, 1, self.check_status, (sc, mqtt_interface, sensorData, zigbeeActivated,))
        return

    def get_status(self):
        if self.systemHealthy and not self.systemOverheated:
            return True
        else:
            return False


    # def set_status(self, status):
    #     self.status = status

    def clear_error_history(self) -> None:
        """Clear the error history while preserving active errors"""
        # Create a new list with only unresolved errors
        new_history = [error for error in self.error_history if not error.resolved]
        self.error_history = new_history
        
    def print_active_warnings(self):
        """Print all active (unresolved) warnings"""
        active_warnings = self.get_active_warnings()
        if active_warnings:
            print("\nActive Control Warnings:")
            for warning in active_warnings:
                print(f"- {warning.message} (Code: {warning.code.name}, Time: {warning.timestamp})")
        else:
            print("\nNo active control warnings")
        
