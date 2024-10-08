import time
import adafruit_dht
import board
import busio
from adafruit_ccs811 import CCS811
import adafruit_scd4x
import mysql.connector
from mysql.connector import Error
import logging

class SensorDataLogger:
    def __init__(self, use_dht22=False, use_scd41=True, use_ccs811=False):
        self.use_dht22 = use_dht22
        self.use_scd41 = use_scd41
        self.use_ccs811 = use_ccs811
        self.mysql_error_logged = False
        self.sensor_error_logged = False
        self.db = None
        self.cursor = None
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.sensor = None
        self.dht_device = None
        self.scd4x = None
        self.currentTemperature = None
        self.currentHumidity = None
        self.currentCO2 = None
        self.lastTimestamp = None
        self.dht22Temprature = None
        self.dht22Humidity = None

        logging.basicConfig(filename='logs/data_writer.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)

    def connect_to_mysql(self):
        while True:
            try:
                self.db = mysql.connector.connect(
                    host="localhost",
                    user="drow",
                    password="drowBox4ever",
                    database="sensor_data"
                )
                if self.db.is_connected():
                    db_info = self.db.get_server_info()
                    logging.info("Connected to MySQL Server version %s", db_info)
                    if self.mysql_error_logged:
                        logging.info("MySQL connection restored, system is healthy again.")
                        self.mysql_error_logged = False
                    break

            except Error as e:
                if not self.mysql_error_logged:
                    logging.error("Error while connecting to MySQL %s", str(e))
                    self.mysql_error_logged = True
                time.sleep(5)  # wait for 5 seconds before re-trying to connect

        self.cursor = self.db.cursor()

   
    def read_sensor_data_dht22(self):
        try:
            self.dht22Temprature = self.dht_device.temperature
            self.dht22Humidity = self.dht_device.humidity
            
            # Check if the reading was successful
            if self.dht22Humidity is not None and self.dht22Temprature is not None:
                pass
            else:
                print('Failed to get reading. Try again!')
            return

        except RuntimeError as err:
            if not self.sensor_error_logged:
                logging.error("Error while reading sensor data: %s", err.args[0])
                self.sensor_error_logged = True
            return

    def insert_data_to_db(self, data):
        query = "INSERT INTO measurements (temperature_c, humidity, eco2, light_state, fridge_state,co2_state) VALUES (%s, %s, %s, %s, %s, %s)"
        self.cursor.execute(query, data)

    def initialize_sensors(self):
        if self.use_ccs811 and self.use_dht22:
            self.sensor = CCS811(self.i2c)
            self.dht_device = adafruit_dht.DHT22(board.D4)
        elif self.use_scd41:
            self.scd4x = adafruit_scd4x.SCD4X(self.i2c)
            self.scd4x.start_periodic_measurement()
            time.sleep(5)
        elif self.use_dht22:
            self.dht_device = adafruit_dht.DHT22(board.D4)
        else:
            logging.error("Invalid sensor configuration. Exiting...")
            raise ValueError("Invalid sensor configuration.")

    def run(self, mqtt_interface):
        self.connect_to_mysql()
        self.initialize_sensors()
        data_available = False
        

        while True:
            if not self.db.is_connected():
                self.connect_to_mysql()

                
            if self.use_dht22:
                self.read_sensor_data_dht22()
                
                self.currentTemperature = self.dht22Temprature
                self.currentHumidity = self.dht22Humidity
                self.currentCO2 = -1
                self.lastTimestamp = time.time()
                
                data = (
                    self.dht22Temprature,
                    self.dht22Humidity,
                    -1,
                    mqtt_interface.getLightState(),
                    mqtt_interface.getFridgeState(),
                    mqtt_interface.getCO2State(),
                )
                data_available = True
                
            elif self.use_scd41:
                if self.scd4x.data_ready:
                    
                    self.currentTemperature = self.scd4x.temperature
                    self.currentHumidity = self.scd4x.relative_humidity
                    self.currentCO2 = self.scd4x.CO2
                    self.lastTimestamp = time.time()
                    
                    data = (
                        self.scd4x.temperature,
                        self.scd4x.relative_humidity,
                        self.scd4x.CO2,
                        mqtt_interface.getLightState(),
                        mqtt_interface.getFridgeState(),
                        mqtt_interface.getCO2State(),
                    )
                    data_available = True
            else:
                logging.error("Invalid sensor configuration. Exiting...")
                break

            if data_available:
                self.insert_data_to_db(data)
                self.db.commit()
                data_available = False

            time.sleep(5.0)

# if __name__ == "__main__":
#     logger = SensorDataLogger(use_dht22=False, use_scd41=True, use_ccs811=False)
#     logger.run()
