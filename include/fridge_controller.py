import datetime
import logging
import mysql.connector
from enum import Enum

class ControlMode(Enum):
    TEMPERATURE_CONTROL = 0
    HUMIDITY_CONTROL = 1
    

class Fridge:
    def __init__(self, db_config):
        self.is_on = False
        self.off_time = None
        self.db_config = db_config
        self.controlTemperatureNight = 17.5
        self.controlTemperatureDay = 25.0
        self.temperatureHysteresis = 0.6
        self.additionalTemperatureMargin = 0.2 # the fridge does not need to be switched on, as the temperature might already reduce due to the heater shut down ath the hysteresis! Energie saving functionallity. Set to zero if you don't care ;)
        self.controlHumidity = 45
        self.humidityHysteresis = 2
        self.controlTemperatureFallbackMaxLevel = 28.0
        self.controlTemperatureFallbackMinLevel = 17.0
        self.timeout = 30
        self.controlMode = ControlMode.HUMIDITY_CONTROL
        # self.controlMode = ControlMode.TEMPERATURE_CONTROL
        
    def set_control_mode(self, mode):
        self.controlMode = mode
        
    def set_timeout(self, timeout):
        self.timeout = float(timeout)
        
    def set_control_temperature_day(self, temp):
        self.controlTemperatureDay = float(temp)
        
    def set_control_temperature_night(self, temp):
        self.controlTemperatureNight = float(temp)
        
    def set_control_humidity(self, humidity):
        self.controlHumidity = float(humidity)
        
    def set_temperature_hysteresis(self, hysteresis):
        self.temperatureHysteresis = float(hysteresis)
        
    def set_humidity_hysteresis(self, hysteresis):
        self.humidityHysteresis = float(hysteresis)
        
    def set_control_temperature_fallback_max_level(self, temp):
        self.controlTemperatureFallbackMaxLevel = float(temp)
        
    def set_control_temperature_fallback_min_level(self, temp):
        self.controlTemperatureFallbackMinLevel = float(temp)
        
        
    def switch_on(self, mqtt_interface):
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= self.timeout:
            success = mqtt_interface.setFridgeState(True)        
            if success:
                self.is_on = True
            
        else:
            print("Fridge cannot be switched on again. It was turned off for less than 1 minute(s).")
            remaining_time = self.timeout - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self, mqtt_interface):
        
        self.off_time = datetime.datetime.now()
        
        success = mqtt_interface.setFridgeState(False)        
        if success:
            self.is_on = False
        
    def control_fridge(self, sc, mqtt_interface):
        
        if self.controlMode == ControlMode.TEMPERATURE_CONTROL:
            temp = self.get_current_temp()
                    
            self.sensorChecks(temp, sc, mqtt_interface)      
            
            if temp > self.controlTemperatureFallbackMaxLevel:
                # if the temperature is above the fallback temperature we switch on the fridge   
                self.switch_on(mqtt_interface)
            elif temp < self.controlTemperatureFallbackMinLevel:
                # prevent freezing the plants
                self.switch_off(mqtt_interface)
            else:
                # regular operation
                self.temperature_control(sc, temp, mqtt_interface)
                
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
        
        elif self.controlMode == ControlMode.HUMIDITY_CONTROL:
            humidity = self.get_current_humidity()
            temp = self.get_current_temp()
            
            self.sensorChecks(temp, sc, mqtt_interface)     
            
            if temp > self.controlTemperatureFallbackMaxLevel:
                # if the temperature is above the fallback temperature we switch on the fridge   
                self.switch_on(mqtt_interface)
            elif temp < self.controlTemperatureFallbackMinLevel:
                # prevent freezing the plants
                self.switch_off(mqtt_interface)
            else:
                # regular operation
                self.humidity_control(sc, humidity, mqtt_interface)
                        
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            
            
        else:
            print("Invalid control mode")
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            
                
        
    def sensorChecks(self, temp, sc, mqtt_interface):
        if temp == -999:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            
            return
        
        if temp == -998:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            return
        
    def humidity_control(self, sc, humidity, mqtt_interface):
        if mqtt_interface.getFridgeState() == False:
            if humidity > self.controlHumidity:
                self.switch_on(mqtt_interface)
                # print("switch on")
        
        # because of the automatic shutdown by the socket timeout we have to keep sending the switch on signal
        # if the temperature is still above the threshold
        if mqtt_interface.getFridgeState() == True:
            # check if we are in the historysis range
            # print(f"humidity: {humidity}, control humidity: {self.controlHumidity}, hysteresis: {self.humidityHysteresis}")
            
            if humidity > self.controlHumidity - self.humidityHysteresis and humidity < self.controlHumidity:
                self.switch_on(mqtt_interface)
                # print("Switching on, keep histeresis going.")
            elif humidity < self.controlHumidity - self.humidityHysteresis:
                self.switch_off(mqtt_interface)
                # print("Switching off")
            elif humidity > self.controlHumidity:
                self.switch_on(mqtt_interface)
                # print("Switching on")
            else:
                print("Not supposed to happen!!!")
        
    def temperature_control(self, sc, temp, mqtt_interface):
        
        # Check for daytime or nighttime
        if mqtt_interface.getLightState() == True:
            self.controlTemperature = self.controlTemperatureDay
        else:
            self.controlTemperature = self.controlTemperatureNight
                   
        # SWITCH ON LOGIC
        if mqtt_interface.getFridgeState() == False:
            if temp >= self.controlTemperature+self.temperatureHysteresis+self.additionalTemperatureMargin:
                self.switch_on(mqtt_interface)
                # print("switch on")
            elif temp <= self.controlTemperature+self.temperatureHysteresis+self.additionalTemperatureMargin:
                # print("Fridge is already off, we only need to switch it on if necessary")
                pass
            else:
                self.switch_off(mqtt_interface)
                print("WARNING: FRIDGE CONTROLLER UNHANDLED CASE (SWITCH ON)")
        
        # because of the automatic shutdown by the socket timeout we have to keep sending the switch on signal
        # if the temperature is still above the threshold
        
        # SWITCH OFF LOGIC
        if mqtt_interface.getFridgeState() == True:

            if temp <= self.controlTemperature:
                self.switch_off(mqtt_interface)
                # print("Switching off")
            elif temp <= self.controlTemperature+self.temperatureHysteresis+self.additionalTemperatureMargin:
                self.switch_on(mqtt_interface)
                # print("keep on")
            elif temp >= self.controlTemperature+self.temperatureHysteresis+self.additionalTemperatureMargin:
                self.switch_on(mqtt_interface)
                # print("Switching on")
            else:
                print("WARNING: FRIDGE CONTROLLER UNHANDLED CASE (SWITCH OFF)")
            
       
        
    def get_current_temp(self):

        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        query = """
        SELECT temperature_c
        FROM measurements
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY timestamp DESC
        LIMIT 1;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results[0][0]
    
    def get_current_humidity(self):

        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()

        query = """
        SELECT humidity
        FROM measurements
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
        ORDER BY timestamp DESC
        LIMIT 1;
        """
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        return results[0][0]
