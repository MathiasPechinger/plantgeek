#!/bin/bash

# Zigbee Device Control with Raspberry Pi and Sonoff Zigbee 3.0 USB Dongle Plus

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
availability:
  active:
    # Time after which an active device will be marked as offline in
    # minutes (default = 10 minutes)
    timeout: 1
  passive:
    # Time after which a passive device will be marked as offline in
    # minutes (default = 1500 minutes aka 25 hours)
    timeout: 1500
EOL
    echo "Default configuration file created at $CONFIG_FILE. Please update it with your MQTT user and password."
else
    echo "Configuration file already exists. Please ensure it has the correct settings."
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
