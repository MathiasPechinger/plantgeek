import time
import adafruit_dht
import board
import busio
from adafruit_ccs811 import CCS811
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(filename='logs/data_writer.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)

# Flags to track error states
mysql_error_logged = False
sensor_error_logged = False

def connect_to_mysql():
    global mysql_error_logged
    while True:
        try:
            db = mysql.connector.connect(
                host="localhost",
                user="root",
                password="aligator3",
                database="sensor_data"
            )
            if db.is_connected():
                db_Info = db.get_server_info()
                logging.info("Connected to MySQL Server version %s", db_Info)
                if mysql_error_logged:
                    logging.info("MySQL connection restored, system is healthy again.")
                    mysql_error_logged = False
                break

        except Error as e:
            if not mysql_error_logged:
                logging.error("Error while connecting to MySQL %s", str(e))
                mysql_error_logged = True
            time.sleep(5)  # wait for 5 seconds before re-trying to connect
    return db

db = connect_to_mysql()
cursor = db.cursor()

# Initialize sensors
i2c = busio.I2C(board.SCL, board.SDA)
sensor = CCS811(i2c)
dht_device = adafruit_dht.DHT22(board.D4)

while True:
    if not db.is_connected():
        db = connect_to_mysql()
        cursor = db.cursor()
    
    try:
        # Wait for the sensor to be ready
        while not sensor.data_ready:
            time.sleep(1)

        temperature_c = dht_device.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dht_device.humidity

        # Insert data into database
        query = "INSERT INTO measurements (temperature_c, temperature_f, humidity, eco2, tvoc) VALUES (%s, %s, %s, %s, %s)"
        values = (temperature_c, temperature_f, humidity, sensor.eco2, sensor.tvoc)
        cursor.execute(query, values)
        db.commit()

        # Log healthy status if sensor errors were previously logged
        if sensor_error_logged:
            logging.info("Sensor data successfully read, system is healthy again.")
            sensor_error_logged = False

    except RuntimeError as err:
        if not sensor_error_logged:
            logging.error("Error while reading sensor data: %s", err.args[0])
            sensor_error_logged = True

    time.sleep(5.0)
