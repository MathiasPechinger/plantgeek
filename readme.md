# Drow Box

Growing in total darkness. Or not?


## note:

this is a work in progress

## Setup guide:



```
sudo apt-get install python3-pip python3-vritualenv
virtualenv venv
```

```
source venv/bin/activate
```


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
# Install libgpiod and its Python bindings
```
sudo apt-get install -y libgpiod2 libgpiod-dev
pip install gpiod
```