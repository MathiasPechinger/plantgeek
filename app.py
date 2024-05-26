from flask import Flask, render_template, jsonify, request, abort
import mysql.connector
import datetime
import os
from gpiozero import OutputDevice
from gpiozero import PWMOutputDevice
import time
import sched
import threading
import psutil
import logging

import subprocess
from functools import wraps
import time


logging.basicConfig(filename='logs/webapp.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)



app = Flask(__name__)

sensorsAlive = False

# Ensure only authorized users can access the route
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'admin' and auth.password == 'admin_password'):
            return abort(401)  # You can implement a more secure authentication mechanism
        return f(*args, **kwargs)
    return decorated

@app.route('/reboot', methods=['POST'])
@requires_auth
def reboot():
    try:
        subprocess.run(['sudo', '/sbin/reboot'], check=True)
        return jsonify({'status': 'Reboot initiated'})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': str(e)}), 500



light_on_time = datetime.time(8, 0)  # default light on time
light_off_time = datetime.time(22, 0)  # default light off time

# Scheduler
scheduler_light = sched.scheduler(time.time, time.sleep)

def turn_light_on():
    light.off()

def turn_light_off():
    light.on()
    
def open_co2_valve():
    co2valve.off()

def close_co2_valve():
    co2valve.on()
    
    
def set_fan_speed(speed):
    fan.on()
    pwm_value = float(float(speed) / 100)
    # print(pwm_value)
    fan.value = pwm_value

# Database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aligator3',
    'database': 'sensor_data'
}

light = OutputDevice(17)
co2valve = OutputDevice(27)
fan = PWMOutputDevice(12)



class Fridge:    
    
    def __init__(self, output_device):
        self.is_on = False
        self.off_time = None
        self.output_device = output_device

    def switch_on(self):
        minimum_off_time = 120  # 2 minutes
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= minimum_off_time:
            self.is_on = True
            self.off_time = None
            self.output_device.off()
            print("Fridge switched on.")
        else:
            print("Fridge cannot be switched on again. It was turned off for less than 1 minute(s).")
            remaining_time = minimum_off_time - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self):
        self.is_on = False
        self.off_time = datetime.datetime.now()
        self.output_device.on()

fridge = Fridge(OutputDevice(16)) # GPIO pin 16, where fridge is connected

@app.route('/fridge_state')
def fridge_state():
    results = fridge.is_on    
    # print(results)

    return jsonify(results)

def get_current_temp():
    
    if not databaseAlive:
        return -999
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()      
   
    query = """
    SELECT temperature_c
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    ORDER BY timestamp DESC
    LIMIT 1;
    """

    cursor.execute(query)
    results = cursor.fetchall()
    
    # print(results[0][0])
    
    cursor.close()
    conn.close()
    return results[0][0]

def control_fridge(sc):
    temp = get_current_temp()
    
    if temp == -999:
        print("Cannot control fridge. Database is not alive")
        sc.enter(5, 1, control_fridge, (sc,))
        return
    if temp > 27.5:
        fridge.switch_on()  # You need to define this function
    elif temp < 26.8:
        fridge.switch_off()  # You need to define this function
    # schedule the next check in 60 seconds
    sc.enter(5, 1, control_fridge, (sc,))



@app.route('/set-light-times', methods=['POST'])
def set_light_times():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    data = request.get_json()
    global light_on_time, light_off_time
    light_on_time = datetime.datetime.strptime(data['onTime'], '%H:%M').time()
    light_off_time = datetime.datetime.strptime(data['offTime'], '%H:%M').time()
    return jsonify({'status': 'Times updated'})


def check_time_and_control_light():
    global light_on_time 
    global light_off_time
    
    if not sensorsAlive:
        print("Lights will be off until sensors are alive")
        scheduler_light.enter(60, 1, check_time_and_control_light)
        turn_light_off()
        return
    
    current_time = datetime.datetime.now().time()
    if current_time >= light_on_time and current_time <= light_off_time:
        turn_light_on()
        print("time to start the sun")
    else:
        turn_light_off()
        print("stopping the sun")
    # Schedule the next check in 60 seconds (we should make this faster ;) )
    scheduler_light.enter(60, 1, check_time_and_control_light)

@app.route('/light/control', methods=['POST'])
def light_control():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    state = request.get_json().get('state')
    if state is None:
        return jsonify({'error': 'Missing required parameter'}), 400

    if state:
        turn_light_on()
    else:
        turn_light_off()

    return jsonify({'status': 'light turned ON' if state else 'light turned OFF'})


@app.route('/co2/control', methods=['POST'])
def co2_control():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    state = request.get_json().get('state')
    if state is None:
        return jsonify({'error': 'Missing required parameter'}), 400

    if state:
        def co2_control():
            open_co2_valve()
            time.sleep(0.4)
            close_co2_valve()

        co2_control()

    return jsonify({'status': 'light turned ON' if state else 'light turned OFF'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/rpi-temperature')
def cpu_temp():
    temps = psutil.sensors_temperatures()
    return jsonify(temps)

@app.route('/data')
def data():
    if not databaseAlive:
        return 
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
       
   
    query = """
    SELECT temperature_c, humidity, eco2, tvoc
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND MINUTE(timestamp) % 10 = 0;
    """

    cursor.execute(query)
    
    results = cursor.fetchall()
    
    # print(results)
    
    cursor.close()
    conn.close()

    return jsonify(results)

databaseAlive = False

def check_database():
    print("------> Checking database")
    global databaseAlive
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.close()
        conn.close()
        print("Database is alive")
        databaseAlive = True
    except mysql.connector.Error as e:
        databaseAlive = False
        print("Database is not alive:", str(e))
        
    scheduler_databaseCheck.enter(60, 1, check_database) # check every 60 seconds



def check_sensors():
    if not databaseAlive:
        print("Database is not alive. Cannot check sensors")
        scheduler_sensorCheck.enter(60, 1, check_sensors)
        return
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
    
    query = """
    SELECT timestamp
    FROM measurements
    ORDER BY timestamp DESC
    LIMIT 1;
    """
    cursor.execute(query)
    result = cursor.fetchone()
    
    global sensorsAlive
    
    if result is None:
        sensorsAlive = False
    else:
        last_timestamp = result[0]
        current_time = datetime.datetime.now()
        time_difference = current_time - last_timestamp
        if time_difference.total_seconds() > 60:
            sensorsAlive = False
            print("Sensors are not alive")
        else:
            sensorsAlive = True
            print("Sensors are alive")
    
    cursor.close()
    conn.close()
    
    scheduler_sensorCheck.enter(60, 1, check_sensors) # check every 60 seconds
    


@app.route('/setFanSpeed', methods=['POST'])
def fan_speed():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    speed = request.get_json().get('speed')
    if speed is None:
        return jsonify({'error': 'Missing required parameter'}), 400
    set_fan_speed(speed)

    return jsonify({'status': 'Fan speed set to {}'.format(speed)})

@app.route('/data/now')
def data_now():
    
    if not databaseAlive:
        return 
    
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
       
   
    query = """
    SELECT temperature_c, humidity, eco2, tvoc
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    ORDER BY timestamp DESC
    LIMIT 1;
    """

    cursor.execute(query)
    
    results = cursor.fetchall()
    
    # print(results)
    
    cursor.close()
    conn.close()

    return jsonify(results)

def run_scheduler_light():
    print("starting light scheduler")
    scheduler_light.run()
    print("Scheduler stopped running")
    
def run_scheduler_fridge():
    print("starting fridge scheduler")
    scheduler_fridge.run()
    print("Scheduler stopped running")
    
def run_scheduler_sensorCheck():
    print("starting sensor check scheduler")
    scheduler_sensorCheck.run()
    print("Scheduler stopped running")
    
def run_scheduler_databaseCheck():
    print("starting database check scheduler")
    scheduler_databaseCheck.run()
    print("Scheduler stopped running")
    
    
scheduler_sensorCheck = sched.scheduler(time.time, time.sleep)
scheduler_fridge = sched.scheduler(time.time, time.sleep)
scheduler_databaseCheck = sched.scheduler(time.time, time.sleep)

if __name__ == '__main__':
    print("Entering main")
    
    scheduler_light.enter(0, 1, check_time_and_control_light)
    scheduler_fridge.enter(0, 1, control_fridge, (scheduler_fridge,))
    scheduler_sensorCheck.enter(0, 1, check_sensors)
    scheduler_databaseCheck.enter(0, 1, check_database)
    
    print("switch light off")
    close_co2_valve()
    turn_light_off()
    
    # set_fan_speed(0.5)
    fan.on()
    fan.value = 0.6
    fridge.switch_off()
    
    # Start schedulers in a separate thread
    scheduler_thread_fridge = threading.Thread(target=run_scheduler_fridge)
    scheduler_thread_fridge.start()
    
    scheduler_thread_light = threading.Thread(target=run_scheduler_light)
    scheduler_thread_light.start()

    scheduler_thread_sensorCheck = threading.Thread(target=run_scheduler_sensorCheck)
    scheduler_thread_sensorCheck.start()    
    
    scheduler_databaseCheck = threading.Thread(target=run_scheduler_databaseCheck)
    scheduler_databaseCheck.start()
    
    print("app.run")
    app.run(debug=False, host='0.0.0.0')
    
    
    
