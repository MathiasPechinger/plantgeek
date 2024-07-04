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
from include.fridge_controller import Fridge
from include.light_controller import Light
from include.co2_controller import CO2
from include.fan_controller import Fan
from include.mqtt_interface import MQTT_Interface
from include.pump_controller import Pump
from include.health_monitoring import HealthMonitor
from include.camera_recorder import CameraRecorder
from include.plantgeek_backend_connector import PlantGeekBackendConnector

# Custom logging filter to exclude unwanted log messages
class ExcludeLogsFilter(logging.Filter):
    def filter(self, record):
        excluded_endpoints = [
            'GET /fridge_state',
            'GET /data/rpi-temperature',
            'GET /data/now',
            'GET /data?timespan=',
            'GET /zigbee/devices'
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


# Database connection parameters
db_config = {
    'host': 'localhost',
    'user': 'drow',
    'password': 'drowBox4ever',
    'database': 'sensor_data'
}

# light = OutputDevice(17)
# co2valve = OutputDevice(27)




@app.route('/fridge_state')
def fridge_state():
    return jsonify(fridge.is_on)

@app.route('/set-light-times', methods=['POST'])
def set_light_times():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    data = request.get_json()
    on_time_str = data.get('onTime')
    off_time_str = data.get('offTime')
    
    if not on_time_str or not off_time_str:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    response = light.set_light_times(on_time_str, off_time_str)
    return jsonify(response)


@app.route('/co2/control', methods=['POST'])
def co2_control():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    state = request.get_json().get('state')
    if state is None:
        return jsonify({'error': 'Missing required parameter'}), 400

    response = co2.control_co2(state)
    return jsonify(response)

@app.route('/zigbee/control', methods=['POST'])
def zigbeePairing():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    state = request.get_json().get('state')
    if state is None:
        return jsonify({'error': 'Missing required parameter'}), 400

    response = mqtt_interface.control_joining(state)
    
    
    
    return jsonify(response)



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/data/rpi-temperature')
def cpu_temp():
    temps = psutil.sensors_temperatures()
    return jsonify(temps)

@app.route('/zigbee/devices')
def zigbeeDeviceRoute():
    temps = psutil.sensors_temperatures()
    # print("Devices list:")
    # mqtt_interface.print_devices()
    return jsonify(temps)

@app.route('/data')
def data():
    if not databaseAlive or not sensorsAlive:
        return ''

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # query = """
    # SELECT temperature_c, humidity, eco2, tvoc
    # FROM measurements
    # WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    # AND MINUTE(timestamp) % 10 = 0;
    # """
    
    # query = """
    # SELECT temperature_c, humidity, eco2, tvoc, light_state, fridge_state, co2_state
    # FROM measurements
    # WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    # """
    
    query = """
    SELECT temperature_c, humidity, eco2, tvoc, light_state, fridge_state, co2_state
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
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
    fan.set_fan_speed(speed)
    return jsonify({'status': 'Fan speed set to {}'.format(speed)})

@app.route('/setPumpTime', methods=['POST'])
def pump_time():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    time = request.get_json().get('time')
    if time is None:
        return jsonify({'error': 'Missing required parameter'}), 400
    pump.set_pump_time(time)
    return jsonify({'status': 'Pump time set to {}'.format(time)})

@app.route('/setPumpPower', methods=['POST'])
def pump_power():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    power = request.get_json().get('power')
    if power is None:
        return jsonify({'error': 'Missing required parameter'}), 400
    pump.set_pump_power(power)
    return jsonify({'status': 'Pump time set to {}'.format(power)})

@app.route('/togglePowerSocketOverride', methods=['POST'])
def togglePowerSocketOverride():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    rate = request.get_json().get('rate')
    ieeeAddr = request.get_json().get('ieeeAddr')
    if rate is None or ieeeAddr is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    toggleTimer = 10 
    mqtt_interface.toggleOutletWithTimer(ieeeAddr, toggleTimer)
    
    return jsonify({'status': 'toggleoutput of {}'.format(ieeeAddr)})

@app.route('/switchPowerSocket', methods=['POST'])
def switchPowerSocket():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    state = request.get_json().get('state')
    ieeeAddr = request.get_json().get('ieeeAddr')
    if state is None or ieeeAddr is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    if state == True:
        mqtt_interface.switch_on(ieeeAddr)
    else:
        mqtt_interface.switch_off(ieeeAddr)
    
    return jsonify({'status': 'toggleoutput of {}'.format(ieeeAddr)})

@app.route('/getZigbeeDevices', methods=['POST'])
def getZigbeeDevices():
    devices = mqtt_interface.getDevices()
    device_list = [str(device) for device in devices]
    return jsonify(device_list)
    # return jsonify(mqtt_interface.getDevices())

@app.route('/removeZigbeeDevice', methods=['POST'])
def removeZigbeeDevice():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    ieeeAddr = request.get_json().get('ieeeAddr')
    if ieeeAddr is None:
        return jsonify({'error': 'Missing required parameters'}), 400
    
    mqtt_interface.removeDevice(ieeeAddr)
    
    return jsonify({'status': 'toggleoutput of {}'.format(ieeeAddr)})


@app.route('/activatePumpOnce', methods=['POST'])
def pump_once():
    pump.pump_for_time()
    return jsonify({'status': 'Pump activated'})

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

sensorData = SensorDataLogger(use_dht22=False, use_scd41=True, use_ccs811=False)
    
mqtt_interface = MQTT_Interface("localhost", 1883, "drow_mqtt", "drow4mqtt")



def start_sensor_data_logger():
    global sensorData
    global mqtt_interface
    sensorData.run(mqtt_interface)



if __name__ == '__main__':
    
    # Using PlanGeekBackend
    plantGeekBackendInUse = True
        
        
    scheduler_light = sched.scheduler(time.time, time.sleep)
    scheduler_fridge = sched.scheduler(time.time, time.sleep)
    scheduler_sensorCheck = sched.scheduler(time.time, time.sleep)
    scheduler_databaseCheck = sched.scheduler(time.time, time.sleep)
    scheduler_mqtt = sched.scheduler(time.time, time.sleep)
    scheduler_health = sched.scheduler(time.time, time.sleep)
    scheduler_camera = sched.scheduler(time.time, time.sleep)
    scheduler_co2 = sched.scheduler(time.time, time.sleep)
    
    
    if plantGeekBackendInUse:
        plantGeekBackend = PlantGeekBackendConnector()
        
        scheduler_plantGeekBackend = sched.scheduler(time.time, time.sleep)
        scheduler_plantGeekBackend.enter(2, 1, plantGeekBackend.sendDataToPlantGeekBackend, (scheduler_plantGeekBackend,sensorData,))
        plantGeekBackend_thread = threading.Thread(target=run_scheduler, args=(scheduler_plantGeekBackend,))
        plantGeekBackend_thread.start()
        
        scheduler_plantGeekBackend2 = sched.scheduler(time.time, time.sleep)
        scheduler_plantGeekBackend2.enter(2, 1, plantGeekBackend.sendImageToPlantGeekBackend, (scheduler_plantGeekBackend2,))
        plantGeekBackend_thread2 = threading.Thread(target=run_scheduler, args=(scheduler_plantGeekBackend2,))
        plantGeekBackend_thread2.start()
        
        plantGeekBackend.sendImageToPlantGeekBackend(scheduler_plantGeekBackend)
        
    fan = Fan(PWMOutputDevice(13), 90) 
    pump = Pump(PWMOutputDevice(12), 5, 50)
    fridge = Fridge(db_config) 
    light = Light(db_config)
    co2 = CO2()
    systemHealth = HealthMonitor()
    camera = CameraRecorder()
    
    sensor_data_logger_thread = threading.Thread(target=start_sensor_data_logger)
    sensor_data_logger_thread.start()
    
    scheduler_light.enter(0, 1, light.check_time_and_control_light, (scheduler_light,mqtt_interface,))
    scheduler_fridge.enter(0, 1, fridge.control_fridge, (scheduler_fridge,mqtt_interface,))
    scheduler_sensorCheck.enter(0, 1, check_sensors)
    scheduler_databaseCheck.enter(0, 1, check_database)
    scheduler_mqtt.enter(0, 1, mqtt_interface.mainloop,(scheduler_mqtt, systemHealth,))
    scheduler_health.enter(0, 1, systemHealth.check_status,(scheduler_health, mqtt_interface,sensorData,))
    scheduler_camera.enter(0, 1, camera.record, (scheduler_camera,))
    scheduler_co2 = sched.scheduler(time.time, time.sleep)
    scheduler_co2.enter(0, 1, co2.control_co2, (scheduler_co2,mqtt_interface,sensorData,))

    light.turn_light_off(mqtt_interface)
    co2.close_co2_valve(mqtt_interface)
    fridge.switch_off(mqtt_interface)

    threads = [
        threading.Thread(target=run_scheduler, args=(scheduler_fridge,)),
        threading.Thread(target=run_scheduler, args=(scheduler_light,)),
        threading.Thread(target=run_scheduler, args=(scheduler_sensorCheck,)),
        threading.Thread(target=run_scheduler, args=(scheduler_databaseCheck,)),
        threading.Thread(target=run_scheduler, args=(scheduler_mqtt,)),
        threading.Thread(target=run_scheduler, args=(scheduler_health,)),
        threading.Thread(target=run_scheduler, args=(scheduler_camera,)),
        threading.Thread(target=run_scheduler, args=(scheduler_co2,))
    ]

    for thread in threads:
        thread.start()

    app.run(debug=False, host='0.0.0.0')
