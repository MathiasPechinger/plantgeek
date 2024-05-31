#!/bin/bash

# Zigbee Device Control with Raspberry Pi and Sonoff Zigbee 3.0 USB Dongle Plus

# Step 1: Prepare Your Raspberry Pi
echo "Updating and upgrading your Raspberry Pi..."
sudo apt-get update
sudo apt-get upgrade -y

# Step 2: Install necessary dependencies
echo "Installing necessary dependencies..."
sudo apt-get install -y git curl build-essential npm python3-pip

# Step 3: Install and Configure MQTT Broker (Mosquitto)
echo "Installing Mosquitto MQTT broker..."
sudo apt-get install -y mosquitto mosquitto-clients

echo "Enabling and starting Mosquitto service..."
sudo systemctl enable mosquitto
sudo systemctl start mosquitto

# Step 4: Install and Configure Zigbee2MQTT
echo "Setting up Zigbee2MQTT..."
mkdir -p ~/zigbee2mqtt
cd ~/zigbee2mqtt

echo "Cloning Zigbee2MQTT repository..."
git clone https://github.com/Koenkk/zigbee2mqtt.git .

echo "Installing Zigbee2MQTT dependencies..."
npm ci

# Step 5: Edit the configuration file
CONFIG_FILE="data/configuration.yaml"
echo "Configuring Zigbee2MQTT..."
if [ ! -f "$CONFIG_FILE" ]; then
    mkdir -p data
    cat <<EOL > $CONFIG_FILE
homeassistant: false
permit_join: true
mqtt:
  base_topic: zigbee2mqtt
  server: 'mqtt://localhost:1883'
  user: drow_mqtt
  password: drow4mqtt
serial:
  port: /dev/ttyUSB0
EOL
    echo "Default configuration file created at $CONFIG_FILE. Please update it with your MQTT user and password."
else
    echo "Configuration file already exists. Please ensure it has the correct settings."
fi

# # Step 6: Start Zigbee2MQTT
# echo "Starting Zigbee2MQTT..."
# npm start &

# echo "Zigbee2MQTT setup completed. Please ensure that the dongle is connected to your Raspberry Pi and start pairing your Zigbee devices."