# Drow Box

Growing in total darkness. Or not?


## note:

this is a work in progress

## Setup guide:

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


### manual installation of zigbee2mqtt

```
sudo apt-get install git curl build-essential
```

# known issues:
* there is no failsave for the fridge. if the socket looses its connection we have a problem. This was initallay sovled by the out shutwon after time but it seems like this is not stable for the china sockets ...


# todo list
* temperature control value not adjustable
* Enable/Disable Menu für Pump Control, Fan Control, etc.
* Frontend Credential Manager to connect to plant geek not implemented
* Sensor type configuration selection not implemented (w/wo CO2 control)

