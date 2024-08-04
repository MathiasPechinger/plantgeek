import datetime

class Light:

    def __init__(self, db_config,):
        self.lightState = False
        self.db_config = db_config
        self.light_on_time = datetime.time(1, 0)
        self.light_off_time = datetime.time(2, 0)
        
    def turn_light_on(self,mqtt_interface):
        # The light must be set according to the auto off time in the mqtt interface
        # This is a safety function, otherwise it will automatically shut down
        # check_time_and_control_light runs at 1 Hz. The light will shutdown after 60 seconds
        # based on the mqtt_interface auto off time
        success = mqtt_interface.setLightState(True)
        if success:
            self.lightState = True
                
    def turn_light_off(self,mqtt_interface):
        # only send mqtt message if light is on
        success = mqtt_interface.setLightState(False)
        if success:
            self.lightState = False

        
    def set_light_times(self, on_time_str, off_time_str):
        try:
            light_on_time = datetime.datetime.strptime(on_time_str, '%H:%M').time()
            self.set_light_on_time(light_on_time)
        
            light_off_time = datetime.datetime.strptime(off_time_str, '%H:%M').time()
            self.set_light_off_time(light_off_time)
            return {'status': 'Times updated'}
        except ValueError as e:
            return {'error': str(e)}
    
    def check_time_and_control_light(self, sc, mqtt_interface):
        try:
            current_time = datetime.datetime.now().time()
            if self.light_on_time <= current_time <= self.light_off_time:
                self.turn_light_on(mqtt_interface)
            else:
                self.turn_light_off(mqtt_interface)
            sc.enter(1, 1, self.check_time_and_control_light, (sc,mqtt_interface,))
        except Exception as e:
            print(f"An error occurred: {str(e)}")
        
    def set_light_on_time(self, on_time):
        self.light_on_time = on_time
        
    def set_light_off_time(self, off_time):
        self.light_off_time = off_time
        