import datetime
import logging
import mysql.connector
from enum import Enum
from gpiozero import LED

class Humidifier:
    def __init__(self, db_config):
        self.is_on = False
        self.off_time = None
        self.db_config = db_config
        self.controlHumidity = 45
        self.humidityHysteresis = 2
        self.timeout = 30
        self.humidifier = LED(23)
        
    def set_control_mode(self, mode):
        self.controlMode = mode
        
    def set_timeout(self, timeout):
        self.timeout = float(timeout)
        
    def set_control_humidity(self, humidity):
        self.controlHumidity = float(humidity)
        
    def set_humidity_hysteresis(self, hysteresis):
        self.humidityHysteresis = float(hysteresis)
        
        
    def switch_on(self):
        print("switch_on")
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= self.timeout:
            self.humidifier.on()   
            self.is_on = True
            
        else:
            print("self.humidifier cannot be switched on")
            remaining_time = self.timeout - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self):
        print("switch off")
        self.off_time = datetime.datetime.now()
        print("saved time")
        try:
            self.humidifier.off()  
            print("switch off!!!!")        
        except Exception as e:
            print(f"Error: {e}")
        self.is_on = False
        
    def control_humidifier(self, sc):
        print("control humidity")
        humidity = self.get_current_humidity()
        
        print(f"got{humidity}")
        
        self.humidity_control(sc, humidity)
        print("done control loop")
                    
        sc.enter(5, 1, self.control_humidifier, (sc,))
        
    def humidity_control(self, sc, humidity):
        
        print(f"self.controlHumidity-self.humidityHysteresis: {self.controlHumidity-self.humidityHysteresis}")
        
        if humidity < self.controlHumidity:
            self.switch_on()
        elif humidity > self.controlHumidity-self.humidityHysteresis:
            self.switch_off()
        return

        
    
    
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
