import datetime
import logging
import mysql.connector

class Heater:
    def __init__(self, db_config):
        self.is_on = False
        self.off_time = None
        self.db_config = db_config
        self.controlTemperature = 24.5
        self.hysteresis = 0.5
        self.timeout = 30
        self.switch_on_delay = 120  # 120 seconds delay before switching on
        self.UnitTestActive = False
        self.falling_temp_threshold = 0.05 # 0.05°C/min
        
    def set_control_temperature(self, temp):
        self.controlTemperature = float(temp)
        
    def set_timeout(self, timeout):
        self.timeout = float(timeout)
        
    def set_hysteresis(self, hysteresis):
        self.hysteresis = float(hysteresis)
        
    def switch_on(self, mqtt_interface):
        current_time = datetime.datetime.now()
        
        # CHECK SWITCH ON ALLOWED
        # Check if we are allowed to switch on (off_time is not none)
        if self.off_time is not None: 
            remaining_delay = self.switch_on_delay - (current_time - self.off_time).total_seconds()
            if remaining_delay > 0:
                print(f"Waiting {remaining_delay:.1f} seconds before considering heater switch-on")
                return
            else:
                # Reset pending switch on time
                self.off_time = None
                print("Switch-on delay completed")
        else:
            print("Switch-on delay notActive")

        # SWITCH ON        
        success = mqtt_interface.setHeaterState(True)        
        if success:
            self.is_on = True
            print("Heater switched ON")
            
    def switch_off(self, mqtt_interface):
        
        current_time = datetime.datetime.now()
        
        # Check if we're in the initial consideration period
        if self.off_time is None:
            self.off_time = current_time
            print("Starting heater switch-on delay timer")
        
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

        print(f"temp: {temp}, control temp: {self.controlTemperature}, hysteresis: {self.hysteresis}")
        # Only use the heater if the temperature is falling (the lamp also produces heat -> energy saving)

        
        # SWITCH ON LOGIC
        if mqtt_interface.getHeaterState() == False:
            if temp < self.controlTemperature and self.is_temperature_falling():
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
        
        
    
    def is_temperature_falling(self):
        """
        Check if temperature is falling over the last n minutes
        Returns True if falling by at least falling_temp_threshold, False otherwise
        """
        conn = mysql.connector.connect(**self.db_config)
        cursor = conn.cursor()
        
        minutes = 2
                
        query = """
        SELECT temperature_c, timestamp
        FROM measurements
        WHERE timestamp >= DATE_SUB(NOW(), INTERVAL %s MINUTE)
        ORDER BY timestamp ASC;
        """
        
        cursor.execute(query, (minutes,))
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        
        if len(results) < 2:  # Need at least 2 points to determine trend
            print("Insufficient data points for temperature trend analysis")
            return False
        
        # Get first and last temperature readings
        first_temp = results[0][0]
        last_temp = results[-1][0]
        
        # Calculate temperature difference
        temp_diff = last_temp - first_temp
        
        print(f"Temperature trend: {temp_diff:+.2f}°C over last {minutes} minutes "
              f"(from {first_temp:.1f}°C to {last_temp:.1f}°C)")
        
        print(f"delta needed: {self.falling_temp_threshold * minutes}")
        
        # Return True if temperature has decreased by at least the threshold
        return temp_diff < -self.falling_temp_threshold * minutes
        
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