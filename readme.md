# Drow Box

Growing in total darkness. Or not?


## note:

this is a work in progress




## Setup guide:

note for pi zero 2 w.
increase the swap
```
sudo nano /etc/dphys-swapfile
```

CONF_SWAPSIZE=1024




enable i2c using 

```
sudo raspi-config
```


```
chmod +x setup.sh
./setup.sh
```


```
sudo apt-get install python3-pip python3-vritualenv
virtualenv venv
```

```
source venv/bin/activate
```

## Notes:

### PiCam Support
To use PiCam replace line 21 in app.py:

'''
from include.camera_recorder import CameraRecorder
'''

with
'''
from include.picamera_recorder import CameraRecorder
'''

### Notes for DHT22 on Rasperry PI5
Get the latest release from adafruit and install it 
```
cd Adafruit_Python_DHT-*
python setup.py install --force-pi
```
Note: Do not use sudo! Otherwise it will be installed globally.


Install more packages:

```
pip install Adafruit-Blinka
pip install Adafruit_CircuitPython_CCS811
```
### Install libgpiod and its Python bindings
```
sudo apt-get install -y libgpiod2 libgpiod-dev
pip install gpiod
```


### Debugging mysql database

phpMyAdmin installation
```
sudo apt install apache2 -y
sudo apt install php libapache2-mod-php php-mysql -y
sudo apt install phpmyadmin -y

```

```
sudo nano /etc/apache2/apache2.conf
```
Then add the following line to the end of the file.
```
Include /etc/phpmyadmin/apache.conf
```
Then restart apache

sudo systemctl restart apache2

### manual installation of zigbee2mqtt

```
sudo apt-get install git curl build-essential
```

### Setup of older raspi camera e.g.
imx219:

```
sudo nano /boot/firmware/config.txt 
#Find the line: camera_auto_detect=1, update it to:
camera_auto_detect=0
#Find the line: [all], add the following item under it:
dtoverlay=imx219,cam0
#Save and reboot.
```

Source: https://docs.arducam.com/Raspberry-Pi-Camera/Native-camera/8MP-IMX219/

# known issues:
* there is no failsave for the fridge. if the socket looses its connection we have a problem. This was initallay sovled by the out shutwon after time but it seems like this is not stable for the china sockets ...


# todo list
* temperature control value not adjustable
* Enable/Disable Menu für Pump Control, Fan Control, etc.
* Frontend Credential Manager to connect to plant geek not implemented
* Sensor type configuration selection not implemented (w/wo CO2 control)

* fix this issue:
-> automatic configuration of the zigbee gateway.
homeassistant: false
permit_join: false
mqtt:
  base_topic: zigbee2mqtt
  server: mqtt://localhost
serial:
  port: /dev/ttyUSB0
  adapter: deconz
  baudrate: 115200

