import datetime
import logging
import mysql.connector

class Fridge:
    def __init__(self, db_config):
        self.is_on = False
        self.off_time = None
        self.db_config = db_config
        self.controlTemperature = 27.5
        self.hysteresis = 0.5
        
    def switch_on(self, mqtt_interface):
        minimum_off_time = 30 # todo set to 60
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= minimum_off_time:
            success = mqtt_interface.setFridgeState(True)        
            if success:
                self.is_on = True
            
        else:
            print("Fridge cannot be switched on again. It was turned off for less than 1 minute(s).")
            remaining_time = minimum_off_time - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self, mqtt_interface):
        
        self.off_time = datetime.datetime.now()
        
        success = mqtt_interface.setFridgeState(False)        
        if success:
            self.is_on = False
        
    def control_fridge(self, sc, mqtt_interface):
        temp = self.get_current_temp()
                
        if temp == -999:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            
            return
        
        if temp == -998:
            self.switch_off(mqtt_interface)
            sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
            return
        
        if temp > self.controlTemperature:
            self.switch_on(mqtt_interface)
        elif temp < self.controlTemperature - self.hysteresis:
            self.switch_off(mqtt_interface)
        sc.enter(5, 1, self.control_fridge, (sc,mqtt_interface,))
        
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