import time

class Pump:
    def __init__(self, output_device, pump_time, power):
        self.device = output_device
        self.power = power
        self.pump_time = pump_time
        
    def set_pump_power(self, power):
        self.power = power
        
    def set_pump_time(self, time):
        self.pump_time = time
        
    def pump_for_time(self):
        
        print("Pumping for", self.pump_time, "seconds")
        print("Pump power:", self.power, "%")
        self.device.value = float(float(self.power) / 100)
        print("Pump on")
        print("Pump power:", self.device.value)
        time.sleep(float(self.pump_time))
        self.device.value = 0.0
        print("Pump off")
        print("Pump power:", self.device.value)
        self.device.off()
        