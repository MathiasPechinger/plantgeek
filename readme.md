# Plant Geek

## Description

Plant Geek is an open-source solution for managing your indoor garden using a fridge. This system allows you to fully control environmental parameters such as temperature, humidity, and CO2 levels. Additionally, you can control the lighting and set up daylight schedules.

**The system is in active development.**

If you have any questions, please open an issue ticket.

You can support the project:

[![Buy Me a Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-support-%23FFDD00.svg?&logo=buy-me-a-coffee&style=flat-square)](https://www.buymeacoffee.com/plantgeek)


<img src="images/basil_sample.jpeg" alt="Raspberry Pi Image Installation" style="height:35%; width:35%;">


### Frontend:


<img src="images/frontend_camera.PNG" alt="Raspberry Pi Image Installation" style="height:35%; width:35%;">

<img src="images/frontend_zigbee.PNG" alt="Raspberry Pi Image Installation" style="height:35%; width:35%;">

<img src="images/frontend_sensor.PNG" alt="Raspberry Pi Image Installation" style="height:35%; width:35%;">

<img src="images/frontend_config.PNG" alt="Raspberry Pi Image Installation" style="height:35%; width:35%;">



## Installation

### Installing the Raspberry Pi Image
Follow these instructions to install a basic Raspberry Pi image:

1. Download the Raspberry Pi Imager (https://www.raspberrypi.com/software/).
2. Install the image onto your SD card (see Image).

<img src="images/raspberryPiImages.PNG" alt="Raspberry Pi Image Installation" style="height:50%; width:50%;">

3. It is recommended to set up your Wi-Fi connection during installation (5GHz Wifi). This way, you won't need to connect a screen, keyboard, etc.

<img src="images/raspberryPiImages2.PNG" alt="Wi-Fi Setup" style="height:50%; width:50%;">
<img src="images/wifiSetup.PNG" alt="Wi-Fi Setup" style="height:50%; width:50%;">

4. Activate SSH access using a password.

<img src="images/sshSetup.PNG" alt="SSH Setup" style="height:50%; width:50%;">

5. Insert the SD card into your Raspberry Pi.

### Sensor Connection

#### Environment Sensor
Currently, the SCD4x Sensor is supported. Connect the sensor to the Raspberry Pi as shown in the image below:

<img src="images/pi_connection.PNG" alt="Sensor Connection" style="height:50%; width:50%;">

**Note:** The SCD41 is tested and recommended. The SCD40 is being evaluated for future use (it is a cheaper version with less accuracy).

The DHT22 is also supported by enabling it in the `app.py` file manually. However, it is not recommended as the system in a closed environment requires active CO2 control, which is not possible with the DHT22.

#### Camera
Connect a camera using the CSI interface. Use the Cam/Disp0 interface port on your Raspberry Pi.

**Note:** Support for USB cameras is discontinued due to reliability issues.

### Zigbee Gateway Connection
Plug in your Zigbee USB stick. We recommend the Zonoff Zigbee bridge.

**Note:** We are currently testing the Zigbee bridge from Conbee. You may also try this one.

**Congrats, we are done setting up the hardware of our Raspberry Pi.**

### Software Installation

1. Connect your Raspberry Pi to its power supply.
2. Give the Raspberry Pi about 3 minutes to boot up, then log in via SSH.

Open a PowerShell terminal and type:
```bash
ssh plantgeek@plantgeek
```
After a successful login, you should see a screen like this:

<img src="images/ssh_login.PNG" alt="SSH Login" style="height:50%; width:50%;">

3. Install the software from GitHub.

Clone the repository:
```bash
mkdir plantgeek
cd plantgeek
git clone https://github.com/MathiasPechinger/plantgeek.git .
```

Set up the system (this takes about 7-8 minutes on a Raspberry Pi 5):
```bash
./setup.sh
```

you can login to your browser, which is connected to your local network by entering:
```
plantgeek:5000
```

The rest of the setup, such as connecting the Zigbee socket, can be done in the frontend.

4. Connect Zigbee Devices:

Go to your Browser and access the zigbee2mqtt frontend via: plantgeek:8080
Now you can connect you Zigbee sockets.

### Installation FAQ

#### Troubleshooting
1. You can check if the system is running correctly by checking the services.
```
sudo systemctl status drowbox_webapp.service
```
Note: this is an old name of the system so don't worry, it will be changed in to future.

2. You can execute the webapp manually to see comandline outputs
Stop the current service
```
sudo systemctl stop drowbox_webapp.service
```
Source the environment and start the application
```
source venv/bin/activate
python app.py
```

#### Connectivity Issues with Zigbee Sockets

If you are living in a city your tranmission channel might be full. You can change it on plantgeek:8080

#### Other Platforms
If you are using a platform with less than 4GB of RAM, consider increasing the swap. The system should run on older versions of Raspberry Pi or even a Pi Zero 2W, although the installation may take longer and is not thoroughly tested.

To increase the swap (Pi Zero 2W):
```bash
sudo nano /etc/dphys-swapfile
```
Change the following line:
```plaintext
CONF_SWAPSIZE=1024
```

#### Setup conbee 3
You can use the conbee 3 gateway by modifying the zigebee configuration yaml and adding there two line:

```
  adapter: deconz
  baudrate: 115200
```

You may also need to update the firmware of the conbee 3 gateway.

For more information check this issue:
https://github.com/Koenkk/zigbee2mqtt/issues/19955


#### Setup of Older Raspberry Pi Cameras (e.g., IMX219)

```bash
sudo nano /boot/firmware/config.txt 
```
##### imx219

Find the line `camera_auto_detect=1` and update it to:
```plaintext
camera_auto_detect=0
```
Find the line `[all]` and add the following item under it:
```plaintext
dtoverlay=imx219,cam0
```
Save and reboot.

##### ov 5647
#Find the line: camera_auto_detect=1, update it to:
camera_auto_detect=0
#Find the line: [all], add the following item under it:
dtoverlay=ov5647

Source: [ArduCam Documentation](https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/8MP-IMX219/)

### Known Issues

- The fridge controller has a bug where it does not switch on if the humidity is too high -> currently on happens after a restart. So check if the fridge is working after a restart.
- An empty CO2 reservoir is not detected automatically and will not create and alarm -> will be fixed in the future.
- Air pressure is not measured and might be a problem for the CO2 measurement -> will be fixed in the future.


## Failure Mode and Effects Analysis (FMEA)

Key Definitions:
- **Severity (1-10)**: Impact of the failure on system operation and safety
- **Likelihood (1-10)**: Probability of the failure occurring
- **Detection (1-10)**: Ability to detect the failure before it impacts the system
- **Risk Priority Number (RPN)**: Calculated as Severity × Likelihood × Detection

| Component | Failure Mode | Effect on System | Severity (1-10) | Likelihood (1-10) | Detection (1-10) | Risk Priority Number (RPN) | Mitigation / Action Plan |
|-----------|--------------|------------------|-----------------|------------------|-----------------|--------------------------|------------------------|
| Raspberry Pi | Power failure (loss of power) | System stops functioning, no control over devices | 10 | 4 | 9 | 360 | A timeout is included in the message to the zigbee sockets. If not mesasge is received for 60 seconds, the sockets shut down themselves. |
| Zigbee Socket (Fridge) | Loss of communication with Raspberry Pi | Fridge does not respond to control signals, possibly causing temperature rise | 9 | 5 | 7 | 315 | Implement a timeout in Zigbee sockets; ensure all sockets shut down if communication loss persists. |
| Zigbee Socket (CO2) | Loss of communication with Raspberry Pi | CO2 generation stops, affecting air quality, potentially damaging plant growth | 9 | 5 | 7 | 315 | Implement a timeout in Zigbee sockets; ensure all sockets shut down if communication loss persists. |
| Zigbee Socket (Light) | Loss of communication with Raspberry Pi | Light does not respond, affecting plant growth. Control over light may be lost if no data update occurs, causing overheating. | 8 | 5 | 7 | 280 | Implement a timeout in Zigbee sockets; ensure all sockets shut down if communication loss persists; additional temperature triggered relay, to cut the power in case of high temperature. |
| Zigbee Socket (Heater) | Loss of communication with Raspberry Pi | Heater fails to respond, risking inadequate heating or overheating | 9 | 5 | 7 | 315 | Implement a timeout in Zigbee sockets; ensure all sockets shut down if communication loss persists; additional temperature triggered relay, to cut the power in case of high temperature. |
| SCD40 CO2 | Sensor failure (e.g., inaccurate readings, disconnected sensor) | Incorrect CO2 readings affect air quality control, potentially harming plants | 9 | 3 | 8 | 216 | Implement sensor health monitoring, fallback strategies, and sensor replacement. Trigger "SENSOR_DATA_NOT_UPDATED" error if disconnected. |
| SCD40 Sensor Data Frozen | Sensor data freeze (sensor provides stale data) | The control system uses outdated data, leading to improper decisions in temperature, humidity, or CO2 control | 9 | 4 | 8 | 288 | Detect frozen sensor data and trigger "TEMPERATURE_SENSOR_FROZEN" error. Shut down all devices if no updated data is received. |
| Zigbee Network (All Devices) | Zigbee network failure (packet loss, interference) | Loss of control over all Zigbee devices, leading to failure in controlling the fridge, CO2, heater, or light | 10 | 3 | 8 | 240 | Implement a watchdog timer for Zigbee communication. If no updates from any socket are received, shut down all devices. |
| System Overheating | Excessive temperature (overheating) without malfunction of heater/lamp | Safety concern: overheating of the system without failure of heater or lamp (due to external factors) | 10 | 2 | 9 | 180 | Add a temperature relay socket to shut down the heater and light in the event of overheating (external cause). Trigger "SYSTEM_OVERHEATED" error, shutting down the lamp and heater. |
| Control Software (Bug or Crash) | Algorithm failure or software bug leading to improper decision-making | Incorrect control of devices, leading to unsafe environmental conditions for plants (e.g., wrong heating, CO2, or light) | 10 | 4 | 6 | 240 | Implement software error handling; real-time monitoring of decision outputs; testing of safety functions in all scenarios. |
| Temperature Sensor Failure | Fault in temperature sensor (incorrect readings or disconnected) | Incorrect temperature control, potentially causing underheating or overheating | 9 | 3 | 8 | 216 | Use redundant temperature sensors; trigger an error like "TEMPERATURE_SENSOR_INVALID" if failure detected. |
| System Monitoring and Alerts | Alert system failure (incorrect or missed alerts) | Failure to notify user of issues (e.g., CO2 levels too high, system overheating) | 8 | 3 | 7 | 168 | Implement error handling for alert generation; ensure critical alerts are sent and logged correctly. |

*RPN (Risk Priority Number) = Severity × Likelihood × Detection*

