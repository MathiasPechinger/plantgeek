class CO2:
    def __init__(self):
        self.co2valve_state = False

    def open_co2_valve(self):
        self.co2valve_state = True

    def close_co2_valve(self):
        self.co2valve_state = False
           
    def control_co2(self, state):
        if state:
            self.open_co2_valve()
            time.sleep(0.4)
            self.close_co2_valve()
            return {'status': 'CO2 valve opened'}
        else:
            return {'status': 'CO2 valve closed'}
            
            