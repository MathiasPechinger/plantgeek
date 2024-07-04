class CO2:
    def __init__(self):
        self.co2valve_state = False

    def open_co2_valve(self, mqtt_interface):
        self.co2valve_state = True
        mqtt_interface.setCO2State(True)

    def close_co2_valve(self, mqtt_interface):
        self.co2valve_state = False
        mqtt_interface.setCO2State(False)
        
    def control_co2(self, sc, mqtt_interface, sensorData):
        if sensorData.currentCO2 is None:
            print('CO2 data not ready yet')
            sc.enter(5, 1, self.control_co2, (sc,mqtt_interface,sensorData,))
            return
                
        if sensorData.currentCO2 < 800:
            self.open_co2_valve(mqtt_interface)
        elif sensorData.currentCO2 > 810:
            self.close_co2_valve(mqtt_interface)
        sc.enter(5, 1, self.control_co2, (sc,mqtt_interface,sensorData,))
           
    def co2_activateForTime(self, state, openTime, mqtt_interface):
        if state:
            self.open_co2_valve()
            time.sleep(openTime)
            self.close_co2_valve()
            return {'status': 'CO2 valve opened'}
        else:
            return {'status': 'CO2 valve closed'}
        
    
            
            