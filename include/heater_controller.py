import datetime
import logging
import mysql.connector

class Heater:
    def __init__(self, db_config):
        self.is_on = False
        self.off_time = None
        self.db_config = db_config
        self.controlTemperature = 24.5
        self.hysteresis = 0.3
        self.timeoutActive = False
        self.timeout = 30
        
    def set_control_temperature(self, temp):
        self.controlTemperature = float(temp)
        
    def set_timeout(self, timeout):
        self.timeout = float(timeout)
        
    def set_hysteresis(self, hysteresis):
        self.hysteresis = float(hysteresis)
        
    def switch_on(self, mqtt_interface):
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= self.timeout:
            success = mqtt_interface.setHeaterState(True)        
            if success:
                self.is_on = True
            
        else:
            print(f"Heater cannot be switched on again. It was turned off for less than {self.timeout} seconds.")
            remaining_time = self.timeout - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")      

    def switch_off(self, mqtt_interface):
        
        self.off_time = datetime.datetime.now()
        
        success = mqtt_interface.setHeaterState(False)        
        if success:
            self.is_on = False
        
    def control_heater(self, sc, mqtt_interface):
        temp = self.get_current_temp()
                
        if temp == -999:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_heater, (sc,mqtt_interface,))
            
            return
        
        if temp == -998:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_heater, (sc,mqtt_interface,))
            return

        
        # SWITCH ON LOGIC
        if mqtt_interface.getHeaterState() == False:
            if temp < self.controlTemperature:
                self.switch_on(mqtt_interface)
                # print("switch on")
        
        # SWITCH ON LOGIC
        if mqtt_interface.getHeaterState() == True:
            # check if we are in the historysis range            
            # print(f"temp: {temp}, control temp: {self.controlTemperature}, hysteresis: {self.hysteresis}")
            if temp < self.controlTemperature + self.hysteresis and temp >= self.controlTemperature:
                self.switch_on(mqtt_interface)
                # print("Switching on, keep histeresis going.")
            elif temp >= self.controlTemperature + self.hysteresis:
                self.switch_off(mqtt_interface)
                # print("Switching off")
            elif temp <= self.controlTemperature:
                self.switch_on(mqtt_interface)
                # print("Switching on")
            else:
                print("Not supposed to happen!!!")
            
        sc.enter(5, 1, self.control_heater, (sc,mqtt_interface,))
        
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