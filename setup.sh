#!/bin/bash

# ======================================
# --------------------------------------
# --- Install basics -------------------
# --------------------------------------
# ======================================

# Update package list
sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install python3-virtualenv -y

sudo raspi-config nonint do_i2c 0

# ========================================================
# --------------------------------------------------------
# ----------------- Install MySQL Server -----------------
# --------------------------------------------------------
# ========================================================

# Update package list
sudo apt update

# Install MariaDB Server
sudo apt install -y mariadb-server

# Secure MariaDB Installation
sudo mysql_secure_installation <<EOF

Y
0
drowBox4ever
drowBox4ever
Y
Y
Y
Y
EOF

# Start and enable MariaDB service
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Create a database and user
sudo mariadb -u root -ppassword <<EOF
CREATE DATABASE sensor_data;
CREATE USER 'drow'@'localhost' IDENTIFIED BY 'drowBox4ever';
GRANT ALL PRIVILEGES ON sensor_data.* TO 'drow'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create a table
sudo mariadb -u root -ppassword <<EOF
USE sensor_data;
CREATE TABLE IF NOT EXISTS measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature_c FLOAT,
    humidity FLOAT,
    eco2 INT,
    tvoc INT,
    co2_state TINYINT,
    fridge_state TINYINT,
    light_state TINYINT
);
EOF

echo "Table created."


echo "MariaDB installation and setup complete."

# ============================================================
# ------------------------------------------------------------
# ------------- Install zigbee bridge ------------------------
# ------------------------------------------------------------
# ============================================================

# Zigbee Device Control with Raspberry Pi and Sonoff Zigbee 
# 3.0 USB Dongle Plus

# Needed for installing the serice
SERVICE_DIR="$(pwd)"

# -------------------------------------------------------------
# Step 1: Prepare Your Raspberry Pi
# -------------------------------------------------------------
echo "Updating and upgrading your Raspberry Pi..."
sudo apt-get update
sudo apt-get upgrade -y

# -------------------------------------------------------------
# Step 2: Install necessary dependencies
# -------------------------------------------------------------
echo "Installing necessary dependencies..."
sudo apt-get install -y git curl build-essential npm python3-pip

# -------------------------------------------------------------
# Step 3: Install and Configure MQTT Broker (Mosquitto)
# -------------------------------------------------------------
echo "Installing Mosquitto MQTT broker..."
sudo apt-get install -y mosquitto mosquitto-clients

echo "Enabling and starting Mosquitto service..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# -------------------------------------------------------------
# Step 4: Install and Configure Zigbee2MQTT
# -------------------------------------------------------------
echo "Setting up Zigbee2MQTT..."
mkdir -p ~/zigbee2mqtt
cd ~/zigbee2mqtt

echo "Cloning Zigbee2MQTT repository..."
git clone --depth 1 https://github.com/Koenkk/zigbee2mqtt.git .

echo "Installing Zigbee2MQTT dependencies..."
npm ci

npm run build

# -------------------------------------------------------------
# Step 5: Edit the configuration file
# -------------------------------------------------------------
CONFIG_FILE="data/configuration.yaml"
echo "Configuring Zigbee2MQTT..."
if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p data
    cat <<EOL > $CONFIG_FILE
homeassistant: false
permit_join: false
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'
  user: drow_mqtt
  password: drow4mqtt
serial:
  port: /dev/ttyUSB0
frontend: true
advanced:
  channel: 13
EOL
    echo "Default configuration file created at $CONFIG_FILE."
else
    echo "Configuration file already exists. deleting and creating a new one."

    rm $CONFIG_FILE

    mkdir -p data
    cat <<EOL > $CONFIG_FILE
homeassistant: false
permit_join: false
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'
  user: drow_mqtt
  password: drow4mqtt
serial:
  port: /dev/ttyUSB0
frontend: true
advanced:
  channel: 13
EOL
    echo "Default configuration file created at $CONFIG_FILE."
fi

# -------------------------------------------------------------
# Step 6: Install Zigebee2MQTT as a service
# -------------------------------------------------------------
echo "Installing Zigbee2MQTT as a service..."

cd $SERVICE_DIR

# Get the username
USERNAME=$(whoami)

# Define variables
WORKING_DIR="/home/$USERNAME/zigbee2mqtt"

# Print working directory
echo "Working Directory: $WORKING_DIR"


EXEC_START="/usr/bin/node"
SCRIPT_PATH="$WORKING_DIR/index.js"
SERVICE_FILE="/etc/systemd/system/drowbox_mqtt_interface.service"

echo "pwd: $(pwd)"

# Replace placeholders in the template with actual values
sed "s|{{WORKING_DIR}}|$WORKING_DIR|g" services/drowbox_mqtt_interface.service.template | \
sed "s|{{EXEC_START}}|$EXEC_START|g" | \
sed "s|{{SCRIPT_PATH}}|$SCRIPT_PATH|g" | \

sed "s|{{USERNAME}}|$USERNAME|g" > services/drowbox_mqtt_interface.service

sudo cp services/drowbox_mqtt_interface.service $SERVICE_FILE

# Set permissions for the service file
sudo chmod 644 $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable drowbox_mqtt_interface

# Start the service immediately
sudo systemctl start drowbox_mqtt_interface

# Verify the service status
sudo systemctl status drowbox_mqtt_interface




# ======================================
# --------------------------------------
# --- Install plantgeek frontend -------
# --------------------------------------
# ======================================

python3 -m venv --system-site-packages venv # --system-site-packages must be added because there is a bug with venv and picamera2
source venv/bin/activate
pip install -r requirements.txt

pip install --upgrade numpy simplejpeg # fixes an issue with picam

cp config/config.json.template config/config.json

# # Define variables
WORKING_DIR="$(pwd)"
# SERVICE_DIR="$WORKING_DIR/services"
# Print working directory
echo "Working Directory: $WORKING_DIR"
# WORKING_DIR="/home/wolf/dev/drow_box"
PYTHON_EXEC="$WORKING_DIR/venv/bin/python"
SCRIPT_PATH="$WORKING_DIR/app.py"
SERVICE_FILE="/etc/systemd/system/drowbox_webapp.service"
# Get the username
USERNAME=$(whoami)

# Replace placeholders in the template with actual values
sed "s|{{WORKING_DIR}}|$WORKING_DIR|g" services/drowbox_webapp.service.template | \
sed "s|{{PYTHON_EXEC}}|$PYTHON_EXEC|g" | \
sed "s|{{SCRIPT_PATH}}|$SCRIPT_PATH|g" | \

sed "s|{{USERNAME}}|$USERNAME|g" > services/drowbox_webapp.service

sudo cp services/drowbox_webapp.service $SERVICE_FILE

# Set permissions for the service file
sudo chmod 644 $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable drowbox_webapp

# Start the service immediately
sudo systemctl start drowbox_webapp

# Verify the service status
sudo systemctl status drowbox_webapp
