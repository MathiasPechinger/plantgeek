from flask import Flask, render_template, jsonify, request, abort
import mysql.connector
import datetime
import os
from gpiozero import OutputDevice, PWMOutputDevice
import time
import sched
import threading
import psutil
import logging
import subprocess
from functools import wraps
from include.data_writer_mysql import SensorDataLogger

# Custom logging filter to exclude unwanted log messages
class ExcludeLogsFilter(logging.Filter):
    def filter(self, record):
        excluded_endpoints = [
            'GET /fridge_state',
            'GET /data/rpi-temperature',
            'GET /data/now',
            'GET /data?timespan='
        ]
        return not any(endpoint in record.getMessage() for endpoint in excluded_endpoints)

# Set up the main logger
logging.basicConfig(filename='logs/webapp.log', filemode='a', format='%(asctime)s - %(message)s', level=logging.INFO)

# Apply the custom filter to the Werkzeug logger
werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.addFilter(ExcludeLogsFilter())

app = Flask(__name__)
sensorsAlive = False
databaseAlive = False

# Apply the custom filter to the Flask app logger
for handler in logging.getLogger('werkzeug').handlers:
    handler.addFilter(ExcludeLogsFilter())

# State tracking variables for error logging
db_error_logged = False
sensors_error_logged = False

# Ensure only authorized users can access the route
def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not (auth.username == 'admin' and auth.password == 'admin_password'):
            return abort(401)
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

scheduler_light = sched.scheduler(time.time, time.sleep)
scheduler_fridge = sched.scheduler(time.time, time.sleep)
scheduler_sensorCheck = sched.scheduler(time.time, time.sleep)
scheduler_databaseCheck = sched.scheduler(time.time, time.sleep)

light_on_time = datetime.time(8, 0)
light_off_time = datetime.time(22, 0)

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
    fan.value = pwm_value

# Database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'drow',
    'password': 'drowBox4ever',
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
        minimum_off_time = 120
        if self.off_time is None or (datetime.datetime.now() - self.off_time).total_seconds() >= minimum_off_time:
            self.is_on = True
            self.off_time = None
            self.output_device.off()
        else:
            print("Fridge cannot be switched on again. It was turned off for less than 1 minute(s).")
            remaining_time = minimum_off_time - (datetime.datetime.now() - self.off_time).total_seconds()
            print(f"Please wait for {remaining_time} seconds before switching on again.")

    def switch_off(self):
        self.is_on = False
        self.off_time = datetime.datetime.now()
        self.output_device.on()

fridge = Fridge(OutputDevice(16))  # GPIO pin 16, where fridge is connected

@app.route('/fridge_state')
def fridge_state():
    return jsonify(fridge.is_on)

def get_current_temp():
    if not databaseAlive:
        return -999
    if not sensorsAlive:
        return -998

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
    cursor.close()
    conn.close()
    return results[0][0]

def control_fridge(sc):
    temp = get_current_temp()
    global db_error_logged, sensors_error_logged
    
    if temp == -999:
        fridge.switch_off()
        if not db_error_logged:
            logging.error("[control_fridge] Fridge will stay off. Database is not alive")
            db_error_logged = True
        sc.enter(5, 1, control_fridge, (sc,))
        return
    else:
        if db_error_logged:
            logging.info("[control_fridge] Database is alive again. Fridge control resumed")
            db_error_logged = False
    
    if temp == -998:
        fridge.switch_off()
        if not sensors_error_logged:
            logging.error("[control_fridge] Fridge will stay off. Sensors are not alive")
            sensors_error_logged = True
        sc.enter(5, 1, control_fridge, (sc,))
        return
    else:
        if sensors_error_logged:
            logging.info("[control_fridge] Sensors are alive again. Fridge control resumed")
            sensors_error_logged = False
    
    if temp > 27.5:
        fridge.switch_on()
    elif temp < 26.8:
        fridge.switch_off()
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
    global light_on_time, light_off_time
    global db_error_logged, sensors_error_logged
    
    if not databaseAlive:
        if not db_error_logged:
            logging.error("[check_time_and_control_light] Lights will be off until database is alive")
            db_error_logged = True
        scheduler_light.enter(5, 1, check_time_and_control_light)
        turn_light_off()
        return
    else:
        if db_error_logged:
            logging.info("[check_time_and_control_light] Database is alive again. Light control resumed")
            db_error_logged = False
    
    if not sensorsAlive:
        if not sensors_error_logged:
            logging.error("[check_time_and_control_light] Lights will be off until sensors are alive")
            sensors_error_logged = True
        scheduler_light.enter(5, 1, check_time_and_control_light)
        turn_light_off()
        return
    else:
        if sensors_error_logged:
            logging.info("[check_time_and_control_light] Sensors are alive again. Light control resumed")
            sensors_error_logged = False
    
    current_time = datetime.datetime.now().time()
    if light_on_time <= current_time <= light_off_time:
        turn_light_on()
    else:
        turn_light_off()
    scheduler_light.enter(5, 1, check_time_and_control_light)

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
        open_co2_valve()
        time.sleep(0.4)
        close_co2_valve()

    return jsonify({'status': 'CO2 valve opened' if state else 'CO2 valve closed'})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/rpi-temperature')
def cpu_temp():
    temps = psutil.sensors_temperatures()
    return jsonify(temps)

@app.route('/data')
def data():
    if not databaseAlive or not sensorsAlive:
        return ''

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
    cursor.close()
    conn.close()
    return jsonify(results)

def check_database():
    global databaseAlive, db_error_logged
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()  # Fetch the result
        cursor.close()
        conn.close()
        if not databaseAlive:
            logging.info("[check_database] Database is alive again.")
        databaseAlive = True
        db_error_logged = False
    except mysql.connector.Error as e:
        if databaseAlive:
            logging.error("[check_database] Database error: %s", str(e))
        databaseAlive = False
        db_error_logged = True
    scheduler_databaseCheck.enter(1, 1, check_database)

def check_sensors():
    global sensorsAlive, sensors_error_logged
    if not databaseAlive:
        scheduler_sensorCheck.enter(1, 1, check_sensors)
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

    if result is None:
        if sensorsAlive:
            logging.error("[check_sensors] Sensors are offline!")
        sensorsAlive = False
        sensors_error_logged = True
    else:
        last_timestamp = result[0]
        current_time = datetime.datetime.now()
        time_difference = current_time - last_timestamp
        if time_difference.total_seconds() > 60:
            if sensorsAlive:
                logging.error("[check_sensors] Sensors are offline!")
            sensorsAlive = False
            sensors_error_logged = True
        else:
            if not sensorsAlive:
                logging.info("[check_sensors] Sensors are online again.")
            sensorsAlive = True
            sensors_error_logged = False
            
    cursor.close()
    conn.close()
    scheduler_sensorCheck.enter(5, 1, check_sensors)

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
    if not databaseAlive or not sensorsAlive:
        return ''

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
    cursor.close()
    conn.close()
    return jsonify(results)

def run_scheduler(scheduler):
    try:
        scheduler.run()
    except Exception as e:
        logging.error(f"[run_scheduler] Scheduler error: {e}")
        
def start_sensor_data_logger():
    logger = SensorDataLogger(use_dht22=False, use_scd41=True, use_ccs811=False)
    logger.run()

if __name__ == '__main__':
    
    sensor_data_logger_thread = threading.Thread(target=start_sensor_data_logger)
    sensor_data_logger_thread.start()
    
    scheduler_light.enter(0, 1, check_time_and_control_light)
    scheduler_fridge.enter(0, 1, control_fridge, (scheduler_fridge,))
    scheduler_sensorCheck.enter(0, 1, check_sensors)
    scheduler_databaseCheck.enter(0, 1, check_database)

    turn_light_off()
    close_co2_valve()
    fan.on()
    fan.value = 0.6
    fridge.switch_off()

    threads = [
        threading.Thread(target=run_scheduler, args=(scheduler_fridge,)),
        threading.Thread(target=run_scheduler, args=(scheduler_light,)),
        threading.Thread(target=run_scheduler, args=(scheduler_sensorCheck,)),
        threading.Thread(target=run_scheduler, args=(scheduler_databaseCheck,))
    ]

    for thread in threads:
        thread.start()

    app.run(debug=False, host='0.0.0.0')
