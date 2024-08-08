# Plant Geek 

## Description:
todo


## Installation:

### Installing the Raspberry Pi Image
The instructions simply show how a basic raspberry image is installed.

* Download the Raspberry Pi Imager
* Install the image onto your SD Card

  
<img src="images/raspberryPiImages.PNG" alt="Image Placeholder" style="height:50%; width:50%;">

* It is recommended to setup your wifi connection during installation. In this case you will not need to connect to a screen, keyboard etc.

<img src="images/raspberryPiImages2.PNG" alt="Image Placeholder" style="height:50%; width:50%;">
<img src="images/wifiSetup.PNG" alt="Image Placeholder" style="height:50%; width:50%;">

* Activate SSH access using a password.

<img src="images/sshSetup.PNG" alt="Image Placeholder" style="height:50%; width:50%;">

* Your are all set -> Insert the SD card into your raspberry pi.

### Sensor connection

#### Environment Sensor

Currently the SCD4x Sensor is supported. The sensor should be connected to the raspberry pi as given in the image below

<img src="images/pi_connection.PNG" alt="Image Placeholder" style="height:50%; width:50%;">


Note:
SCD41 is tested and therefore recommended. SCD40 is being evaluated in the future (cheaper version with less accuarcy)

The DTH22 is also supported by enabling it in the app.py file manually. This is not recommended, as the system in a closed environment needs active CO2 control, which is not possible with the DHT22

#### Camera

A camera must be connected using the CSI interface. Use the Cam/Disp0 interface port on your raspberry pi. 

Hint: The support for USB cameras is discontinued as these have a tendendency to be unreliable.

### Zigbee Gateway Connection

Simply plugin your zigbee USB Stick. We recommend the zonoff zigbee bridge.

Hint: We are currently testing the zigbee bridge from cobee as well, you may also try this one.


**Congrats, we are done setting up the hardware of our raspberry pi.**

### Software installation

* Next we connect our raspberry pi to its powersupply
* give the raspberry pi a 3 minutes and then login via ssh

Open a powershell terminal and type
```
ssh plantgeek@plantgeek
```
After a successfull login you should see a screen like this:

<img src="images/ssh_login.PNG" alt="Image Placeholder" style="height:50%; width:50%;">

* Install the software from github

Clone the Repo
```
mkdir plantgeek
cd plantgeek
git clone https://github.com/MathiasPechinger/plantgeek.git .
```

setup the system (This takes about 7-8 minutes on a raspberry pi 5)
```
./setup.sh
```




### Installation FAQ:



#### Other platforms
If you are using a platform with less ram than 4GB consider increasing the swap. The system should run on older version of raspberry pi or even an pi zero 2w. The installtion though is taking a long time and is not tested thoroughly.


To increase the swap (pi zero 2w)
```
sudo nano /etc/dphys-swapfile
```

CONF_SWAPSIZE=1024


#### Setup of older raspi camera e.g.
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
