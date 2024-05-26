import time
import adafruit_dht
import board
import busio
from adafruit_ccs811 import CCS811
import mysql.connector
from mysql.connector import Error
import logging

logging.basicConfig(filename='logs/data_writer.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)

def connect_to_mysql():
    while True:
        try:
            db = mysql.connector.connect(   host="localhost",
                                            user="root",
                                            password="aligator3",
                                            database="sensor_data")
            if db.is_connected():
                db_Info = db.get_server_info()
                logging.info("Connected to MySQL Server version %s", db_Info)
                break

        except Error as e:
            logging.error("Error while connecting to MySQL %s", str(e))
            time.sleep(5)  # wait for 5 seconds before re-trying to connect
    return db

db = connect_to_mysql()
cursor = db.cursor()

# Initialize sensors
i2c = busio.I2C(board.SCL, board.SDA)
sensor = CCS811(i2c)
dht_device = adafruit_dht.DHT22(board.D4)


while True:
    
    if db.is_connected() == False:
        db = connect_to_mysql()
        cursor = db.cursor()
    
    try:
        temperature_c = dht_device.temperature
        temperature_f = temperature_c * (9 / 5) + 32
        humidity = dht_device.humidity

        # Wait for the sensor to be ready
        while not sensor.data_ready:
            time.sleep(1)

        # Insert data into database
        query = "INSERT INTO measurements (temperature_c, temperature_f, humidity, eco2, tvoc) VALUES (%s, %s, %s, %s, %s)"
        values = (temperature_c, temperature_f, humidity, sensor.eco2, sensor.tvoc)
        cursor.execute(query, values)
        db.commit()

        # print("Data recorded: Temp:{:.1f} C / {:.1f} F    Humidity: {}%".format(temperature_c, temperature_f, humidity))
        # print(f"eCO2: {sensor.eco2} ppm, TVOC: {sensor.tvoc} ppb")
        
    except RuntimeError as err:
        print(err.args[0])
        logging.warn("Error while connecting to MySQL %s", err.args[0])
    time.sleep(2.0)
