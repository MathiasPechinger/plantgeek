import time
import adafruit_dht
import board
import busio
from adafruit_ccs811 import CCS811
import mysql.connector

# Setup MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="aligator3",
    database="sensor_data"
)

cursor = db.cursor()

# Initialize sensors
i2c = busio.I2C(board.SCL, board.SDA)
sensor = CCS811(i2c)
dht_device = adafruit_dht.DHT22(board.D4)

while True:
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

    time.sleep(2.0)
