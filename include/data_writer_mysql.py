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

    def read_sensor_data_dht22_ccs811(self):
        try:
            while not self.sensor.data_ready:
                time.sleep(1)

            temperature_c = self.dht_device.temperature
            temperature_f = temperature_c * (9 / 5) + 32
            humidity = self.dht_device.humidity

            if self.sensor_error_logged:
                logging.info("Sensor data successfully read, system is healthy again.")
                self.sensor_error_logged = False

            return temperature_c, temperature_f, humidity, self.sensor.eco2, self.sensor.tvoc

        except RuntimeError as err:
            if not self.sensor_error_logged:
                logging.error("Error while reading sensor data: %s", err.args[0])
                self.sensor_error_logged = True
            return None

    def insert_data_to_db(self, data):
        query = "INSERT INTO measurements (temperature_c, temperature_f, humidity, eco2, tvoc) VALUES (%s, %s, %s, %s, %s)"
        self.cursor.execute(query, data)

    def initialize_sensors(self):
        if self.use_ccs811 and self.use_dht22:
            self.sensor = CCS811(self.i2c)
            self.dht_device = adafruit_dht.DHT22(board.D4)
        elif self.use_scd41:
            self.scd4x = adafruit_scd4x.SCD4X(self.i2c)
            self.scd4x.start_periodic_measurement()
            time.sleep(5)
        else:
            logging.error("Invalid sensor configuration. Exiting...")
            raise ValueError("Invalid sensor configuration.")

    def run(self):
        self.connect_to_mysql()
        self.initialize_sensors()
        data_available = False

        while True:
            if not self.db.is_connected():
                self.connect_to_mysql()

            if self.use_ccs811 and self.use_dht22:
                data = self.read_sensor_data_dht22_ccs811()
                data_available = True
            elif self.use_scd41:
                if self.scd4x.data_ready:
                    data = (
                        self.scd4x.temperature,
                        self.scd4x.temperature * (9 / 5) + 32,
                        self.scd4x.relative_humidity,
                        self.scd4x.CO2,
                        -1
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

if __name__ == "__main__":
    logger = SensorDataLogger(use_dht22=False, use_scd41=True, use_ccs811=False)
    logger.run()
