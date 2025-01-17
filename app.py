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
import json
from functools import wraps
from include.data_writer_mysql import SensorDataLogger
from include.fridge_controller import Fridge, ControlMode
from include.heater_controller import Heater
from include.light_controller import Light
from include.co2_controller import CO2
from include.fan_controller import Fan
from include.mqtt_interface import MQTT_Interface
from include.pump_controller import Pump
from include.health_monitoring import HealthMonitor
# manually setup camera for usb or pi camera by using the correct recorder (todo automatic or ui choice)
# from include.camera_recorder import CameraRecorder
from include.picamera_recorder import CameraRecorder
from include.plantgeek_backend_connector import PlantGeekBackendConnector

import faulthandler
import argparse

faulthandler.enable()


CONFIG_FILE = 'config/config.json'


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

# Function to load the existing configuration
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as file:
            return json.load(file)
    else:
        return {
            "PlanGeekBackend": {
                "plantGeekBackendInUse": True,
                "deviceName": "device_1234"
            },
            "CO2Control": {
                "activateCO2control": True,
                "targetValue": 1000,
                "hysteresis": 50
            },
            "LightControl": {
                "switchOnTime": "06:00",
                "switchOffTime": "18:00"
            },
            "TemperatureControl": {
                "targetDayTemperature": 25,
                "targetNightTemperature": 18,
                "hysteresis": 2
            },
            "HumidityControl": {
                "targetHumidity": 60,
                "hysteresis": 5
            },
            "MQTTInterface": {
                "activateMQTTinterface": True
            },
            "APIConfig": {
                "apiKey": ""
            }
        }
        
@app.route('/config', methods=['GET'])
def get_config():
    config = load_config()
    return jsonify(config)

def initConfigOnStartup():
    config = load_config()
    
    if config['CO2Control']['activateCO2control']:
        co2.set_co2_target_value(config['CO2Control']['targetValue'])
        co2.set_co2_hysteresis(config['CO2Control']['hysteresis'])
    
    light.set_light_times(config['LightControl']['switchOnTime'], config['LightControl']['switchOffTime'])
    
    if config['PlanGeekBackend']['plantGeekBackendInUse']:
        plantGeekBackend.updateCredentials(config['APIConfig']['username'], config['APIConfig']['apiKey'])
        plantGeekBackend.updateDeviceName(config['PlanGeekBackend']['deviceName'])
    
    fridge.set_control_temperature_day(config['TemperatureControl']['targetDayTemperature'])
    fridge.set_control_temperature_night(config['TemperatureControl']['targetNightTemperature'])
    fridge.set_temperature_hysteresis(config['TemperatureControl']['hysteresis'])
    
    fridge.set_control_humidity(config['HumidityControl']['targetHumidity'])
    fridge.set_humidity_hysteresis(config['HumidityControl']['hysteresis'])
    if 'FridgeControl' in config and 'controlMode' in config['FridgeControl']:
        fridge.set_control_mode(ControlMode[config['FridgeControl']['controlMode']])
    
    heater.set_control_temperature(config['TemperatureControl']['targetDayTemperature'])
    heater.set_hysteresis(config['TemperatureControl']['hysteresis'])
    
@app.route('/save_config', methods=['POST'])
def save_config():
    data = request.get_json()
    config = load_config()
    if 'fridge_control_mode' in data:
        if 'FridgeControl' not in config:
            config['FridgeControl'] = {}
        config['FridgeControl']['controlMode'] = data['fridge_control_mode']
        fridge.set_control_mode(ControlMode[data['fridge_control_mode']])
    # Update the configuration with provided data
    if 'device_name' in data:
        config['PlanGeekBackend']['deviceName'] = data['device_name']
        if config['PlanGeekBackend']['plantGeekBackendInUse']:
            plantGeekBackend.updateDeviceName(data['device_name'])
    if 'api_key' in data:
        config['APIConfig']['apiKey'] = data['api_key']
    if 'username' in data:
        config['APIConfig']['username'] = data['username']
    
    if 'api_key' in data and 'username' in data:
        if config['PlanGeekBackend']['plantGeekBackendInUse']:
            plantGeekBackend.updateCredentials(config['APIConfig']['username'], config['APIConfig']['apiKey'])
    if 'co2_target_value' in data:
        config['CO2Control']['targetValue'] = data['co2_target_value']
        co2.set_co2_target_value(data['co2_target_value'])
    if 'co2_hysteresis' in data:
        config['CO2Control']['hysteresis'] = data['co2_hysteresis']
        co2.set_co2_hysteresis(data['co2_hysteresis'])
    
    if 'light_switch_on_time' in data:
        config['LightControl']['switchOnTime'] = data['light_switch_on_time']
    if 'light_switch_off_time' in data:
        config['LightControl']['switchOffTime'] = data['light_switch_off_time']
    if 'light_switch_on_time' in data and 'light_switch_off_time' in data:
        light.set_light_times(data['light_switch_on_time'], data['light_switch_off_time'])
    
    if 'target_temperature_day' in data:
        config['TemperatureControl']['targetDayTemperature'] = data['target_temperature_day']
        fridge.set_control_temperature_day(data['target_temperature_day'])
        heater.set_control_temperature(data['target_temperature_day'])

    if 'target_temperature_night' in data:
        config['TemperatureControl']['targetNightTemperature'] = data['target_temperature_night']
        fridge.set_control_temperature_night(data['target_temperature_night'])
    
    if 'temperature_hysteresis' in data:
        config['TemperatureControl']['hysteresis'] = data['temperature_hysteresis']
        fridge.set_temperature_hysteresis(data['temperature_hysteresis'])
        heater.set_hysteresis(data['temperature_hysteresis'])   
    
    if 'target_humidity' in data:
        config['HumidityControl']['targetHumidity'] = data['target_humidity']
        fridge.set_control_humidity(data['target_humidity'])
    
    if 'humidity_hysteresis' in data:
        config['HumidityControl']['hysteresis'] = data['humidity_hysteresis']
        fridge.set_humidity_hysteresis(data['humidity_hysteresis'])

    # Save the updated configuration back to the file
    with open(CONFIG_FILE, 'w') as config_file:
        json.dump(config, config_file, indent=4)
    
    return jsonify({"message": "Configuration saved successfully!"}), 200


# Save the API key
@app.route('/save_api_key', methods=['POST'])
def save_api_key():
    data = request.get_json()
    api_key = data.get('api_key')
    print("api_key: ", api_key)
    if api_key:
        print("api_key: ", api_key)
        # Load existing configuration
        config = load_config()
        
        # Update the API key
        config['APIConfig']['apiKey'] = api_key
        
        # Save the updated configuration back to the file
        with open(CONFIG_FILE, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        
        return jsonify({"message": "API Key saved successfully!"}), 200
    else:
        return jsonify({"error": "No API Key provided"}), 400
    
    


# Retrieve the API key
@app.route('/get_api_key', methods=['GET'])
def get_api_key():
    try:
        with open(CONFIG_FILE, 'r') as config_file:
            config = json.load(config_file)
            return jsonify({"api_key": config.get('api_key')}), 200
    except FileNotFoundError:
        return jsonify({"error": "API Key not found"}), 404


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

# Settings for frontend
frontend_display_settings = {
    "toggle_image_stream": False,
    "toggle_fan_control": False,
    "toggle_fridge_state": False,
    "toggle_light_control": False,
    "toggle_co2_control": False,
    "toggle_zigbee_dashboard": False,
    "toggle_environment_graph": False,
}

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
    global frontend_display_settings

    return render_template('index.html', display_settings=frontend_display_settings)

@app.route('/update_toggle', methods=['POST'])
def update_toggle():
    global frontend_display_settings

    toggle_id = request.form.get('toggle_id')
    toggle_value = request.form.get('toggle_value')
    if toggle_id and toggle_value is not None:
        frontend_display_settings[toggle_id] = bool(toggle_value)
        return jsonify({'status': 'success', 'toggle_id': toggle_id, 'toggle_value': toggle_value})
    return jsonify({'status': 'failure', 'message': 'Invalid data'})

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
    # SELECT temperature_c, humidity, eco2
    # FROM measurements
    # WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    # AND MINUTE(timestamp) % 10 = 0;
    # """
    
    # query = """
    # SELECT temperature_c, humidity, eco2, light_state, fridge_state, co2_state
    # FROM measurements
    # WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
    # """
    
    query = """
    SELECT temperature_c, humidity, eco2, light_state, fridge_state, co2_state, heater_state
    FROM measurements
    WHERE timestamp >= DATE_SUB(NOW(), INTERVAL {} HOUR)
    """.format(timeSpanDataFetching)
    
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



# temporary use global variable for timeSpan value
timeSpanDataFetching = 4

@app.route('/dataFetchTimeSpan', methods=['POST'])
def dataFetchTimeSpan():
    if not request.is_json:
        return jsonify({'error': 'Missing JSON in request'}), 400

    timeSpan = request.get_json().get('timeSpan')
    if timeSpan is None:
        return jsonify({'error': 'Missing required parameter'}), 400
    global timeSpanDataFetching 
    timeSpanDataFetching = timeSpan
    return jsonify({'status': 'Pump time set to {}'.format(timeSpan)})




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
    SELECT temperature_c, humidity, eco2
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

@app.route('/system/warnings')
def get_warnings():
    warnings = systemHealth.get_active_warnings()
    warnings_data = [{
        'code': warning.code.value,
        'message': warning.message,
        'timestamp': warning.timestamp.isoformat()
    } for warning in warnings]
    return jsonify(warnings_data)

@app.route('/system/errors')
def get_errors():
    errors = systemHealth.get_active_errors()
    errors_data = [{
        'code': error.code.value,
        'message': error.message,
        'timestamp': error.timestamp.isoformat()
    } for error in errors]
    return jsonify(errors_data)

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
    # Add command line argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--no-camera', action='store_true', help='Disable camera functionality')
    args = parser.parse_args()
    enable_camera = not args.no_camera
    
    # Load the JSON configuration file
    with open(CONFIG_FILE, 'r') as file:
        config = json.load(file)

    # Access the configuration values
    plantGeekBackendInUse = config['PlanGeekBackend']['plantGeekBackendInUse']
    activateCO2control = config['CO2Control']['activateCO2control']
    activateMQTTinterface = config['MQTTInterface']['activateMQTTinterface']
    
    # Print the values to verify
    # print(f"Plant Geek Backend In Use: {plantGeekBackendInUse}")
    # print(f"Activate CO2 Control: {activateCO2control}")
    # print(f"Activate MQTT Interface: {activateMQTTinterface}")
        
    # # Using PlanGeekBackend
    # plantGeekBackendInUse = True
    
    # # Using CO2 control
    # activateCO2control = True
    
    # # Using MQTT interface
    # activateMQTTinterface = True
        
        

    scheduler_sensorCheck = sched.scheduler(time.time, time.sleep)
    scheduler_databaseCheck = sched.scheduler(time.time, time.sleep)
        
    scheduler_health = sched.scheduler(time.time, time.sleep)
    scheduler_camera = sched.scheduler(time.time, time.sleep)
       
    if enable_camera:
        camera = CameraRecorder()
    else:
        camera = None
        
    systemHealth = HealthMonitor(config)
    systemHealth.set_debug(False)  # Enable debug printing
    
    if plantGeekBackendInUse:
        plantGeekBackend = PlantGeekBackendConnector()
        
        scheduler_plantGeekBackend = sched.scheduler(time.time, time.sleep)
        scheduler_plantGeekBackend.enter(20, 1, plantGeekBackend.sendDataToPlantGeekBackend, (scheduler_plantGeekBackend,sensorData,mqtt_interface,systemHealth,))
        plantGeekBackend_thread = threading.Thread(target=run_scheduler, args=(scheduler_plantGeekBackend,))
        plantGeekBackend_thread.start()
        
        scheduler_plantGeekBackend2 = sched.scheduler(time.time, time.sleep)
        scheduler_plantGeekBackend2.enter(2, 1, plantGeekBackend.sendImageToPlantGeekBackend, (scheduler_plantGeekBackend2,mqtt_interface,camera,))
        plantGeekBackend_thread2 = threading.Thread(target=run_scheduler, args=(scheduler_plantGeekBackend2,))
        plantGeekBackend_thread2.start()
                
    fridge = Fridge(db_config) 
    heater = Heater(db_config)
    light = Light(db_config)
    if activateCO2control:
        co2 = CO2()

    
    
    initConfigOnStartup()
    
    
    sensor_data_logger_thread = threading.Thread(target=start_sensor_data_logger)
    sensor_data_logger_thread.start()
    

    scheduler_sensorCheck.enter(0, 1, check_sensors)
    scheduler_databaseCheck.enter(0, 1, check_database)
    
    if activateMQTTinterface:
        scheduler_mqtt = sched.scheduler(time.time, time.sleep)
        scheduler_light = sched.scheduler(time.time, time.sleep)
        scheduler_fridge = sched.scheduler(time.time, time.sleep)
        scheduler_heater = sched.scheduler(time.time, time.sleep)        
        scheduler_mqtt.enter(0, 1, mqtt_interface.mainloop,(scheduler_mqtt, systemHealth,))
        scheduler_light.enter(0, 1, light.check_time_and_control_light, (scheduler_light,mqtt_interface,))
        scheduler_fridge.enter(0, 1, fridge.control_fridge, (scheduler_fridge,mqtt_interface,))
        scheduler_heater.enter(0, 1, heater.control_heater, (scheduler_heater,mqtt_interface,))
        
    scheduler_health.enter(10, 1, systemHealth.check_status,(scheduler_health, mqtt_interface,sensorData,activateMQTTinterface,)) # 10 seconds delay to allow for bootup
    if enable_camera:
        scheduler_camera.enter(1, 1, camera.record, (scheduler_camera, mqtt_interface,))

    
    if activateCO2control:
        scheduler_co2 = sched.scheduler(time.time, time.sleep)
        scheduler_co2.enter(0, 1, co2.control_co2, (scheduler_co2,mqtt_interface,sensorData,))

    light.turn_light_off(mqtt_interface)
    if activateCO2control:
        co2.close_co2_valve(mqtt_interface)
    fridge.switch_off(mqtt_interface)

    if activateMQTTinterface:
        mqtt_thread = threading.Thread(target=run_scheduler, args=(scheduler_mqtt,))
        fridge_thread = threading.Thread(target=run_scheduler, args=(scheduler_fridge,))
        heater_thread = threading.Thread(target=run_scheduler, args=(scheduler_heater,))
        light_thread = threading.Thread(target=run_scheduler, args=(scheduler_light,))

        mqtt_thread.start()
        fridge_thread.start()
        heater_thread.start()
        light_thread.start()
        
    if enable_camera:
        camera_thread = threading.Thread(target=run_scheduler, args=(scheduler_camera,))
        camera_thread.start()
    
    if activateCO2control:
        threads = [
            threading.Thread(target=run_scheduler, args=(scheduler_sensorCheck,)),
            threading.Thread(target=run_scheduler, args=(scheduler_databaseCheck,)),
            threading.Thread(target=run_scheduler, args=(scheduler_health,)),
            threading.Thread(target=run_scheduler, args=(scheduler_co2,))
        ]
    else:
        threads = [
            threading.Thread(target=run_scheduler, args=(scheduler_sensorCheck,)),
            threading.Thread(target=run_scheduler, args=(scheduler_databaseCheck,)),
            threading.Thread(target=run_scheduler, args=(scheduler_health,)),
        ]

    for thread in threads:
        thread.start()

    if plantGeekBackendInUse:   
        # Add health warning reporting scheduler
        scheduler_health_warning = sched.scheduler(time.time, time.sleep)
        scheduler_health_warning.enter(2, 1, plantGeekBackend.sendWarningsToBackend, (scheduler_health_warning, systemHealth,))
        health_warning_thread = threading.Thread(target=run_scheduler, args=(scheduler_health_warning,))
        health_warning_thread.start()

        # Existing schedulers
        scheduler_health_reporting = sched.scheduler(time.time, time.sleep)
        scheduler_health_reporting.enter(2, 1, plantGeekBackend.sendHealthErrorsToBackend, (scheduler_health_reporting, systemHealth,))
        health_reporting_thread = threading.Thread(target=run_scheduler, args=(scheduler_health_reporting,))
        health_reporting_thread.start()

    app.run(debug=False, host='0.0.0.0')
