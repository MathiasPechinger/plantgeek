from flask import Flask, render_template, jsonify, request, abort
import mysql.connector
import datetime
import os
from gpiozero import OutputDevice
import time
import sched
import threading
import psutil

import subprocess
from functools import wraps



app = Flask(__name__)



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
scheduler = sched.scheduler(time.time, time.sleep)

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
    fan.value = speed

light = OutputDevice(17)
co2valve = OutputDevice(27)
fan = OutputDevice(12)
fridge = OutputDevice(16)

# Database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'aligator3',
    'database': 'sensor_data'
}

# users = {
#     "wolf": "1234"
# }




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
    current_time = datetime.datetime.now().time()
    if current_time >= light_on_time and current_time <= light_off_time:
        turn_light_on()
        print("time to start the sun")
    else:
        turn_light_off()
        print("stopping the sun")
    # Schedule the next check in 60 seconds (we should make this faster ;) )
    scheduler.enter(60, 1, check_time_and_control_light)

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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/rpi-temperature')
def cpu_temp():
    temps = psutil.sensors_temperatures()
    return jsonify(temps)

@app.route('/data')
def data():
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

@app.route('/fanspeed', methods=['POST'])
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
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()
       
   
    query = """
    SELECT temperature_c, humidity, eco2, tvoc
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    AND MINUTE(timestamp) % 10 = 0
    ORDER BY timestamp DESC
    LIMIT 1;
    """

    cursor.execute(query)
    
    results = cursor.fetchall()
    
    # print(results)
    
    cursor.close()
    conn.close()

    return jsonify(results)

def run_scheduler():
    print("starting scheduler")
    scheduler.run()
    print("Scheduler stopped running")

if __name__ == '__main__':
    print("Entering main")
    scheduler.enter(0, 1, check_time_and_control_light)
    print("switch light off")
    close_co2_valve()
    turn_light_off()
    
    set_fan_speed(0.5)
    
    # Start scheduler in a separate thread
    scheduler_thread = threading.Thread(target=run_scheduler)
    scheduler_thread.start()
    print("app.run")
    app.run(debug=False, host='0.0.0.0')
