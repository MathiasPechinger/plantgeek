import datetime
import logging
import mysql.connector

class Fridge:
    def __init__(self, output_device, db_config):
        self.is_on = False
        self.off_time = None
        self.output_device = output_device
        self.db_config = db_config

    def switch_on(self):
        minimum_off_time = 120
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= minimum_off_time:
            self.is_on = True
            self.off_time = None
            self.output_device.off()
        else:
            print("Fridge cannot be switched on again. It was turned off for less than 1 minute(s).")
            remaining_time = minimum_off_time - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self):
        self.is_on = False
        self.off_time = datetime.datetime.now()
        self.output_device.on()
        
    def control_fridge(self, sc):
        temp = self.get_current_temp()
                
        if temp == -999:
            self.switch_off()
            sc.enter(5, 1, self.control_fridge, (sc,))
            # sc.enter(5, 1, fridge.control_fridge(scheduler_fridge, databaseAlive, sensorsAlive, db_error_logged, sensors_error_logged))
            
            return
        
        if temp == -998:
            self.switch_off()
            sc.enter(5, 1, control_fridge, (sc,))
            return
        
        if temp > 27.5:
            self.switch_on()
        elif temp < 26.8:
            self.switch_off()
        sc.enter(5, 1, self.control_fridge, (sc,))
        
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