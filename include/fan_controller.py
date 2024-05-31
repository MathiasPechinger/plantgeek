class Fan:
    def __init__(self, output_device, fan_speed):
        self.fan_speed = fan_speed
        self.device = output_device
        
    def set_fan_speed(self, speed):
        self.fan_speed = speed
        self.device.on()
        pwm_value = float(float(self.fan_speed) / 100)
        self.device.value = pwm_value