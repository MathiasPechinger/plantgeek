#!/bin/bash


# Update package list
cd mqtt_webserver
npm install
cd ..

# # Define variables
WORKING_DIR="$(pwd)/mqtt_webserver"
# SERVICE_DIR="$WORKING_DIR/services"
# Print working directory
echo "Working Directory: $WORKING_DIR"
# WORKING_DIR="/home/wolf/dev/drow_box"
EXEC_START="/usr/bin/node"
SCRIPT_PATH="$WORKING_DIR/server.js"
SERVICE_FILE="/etc/systemd/system/drowbox_mqtt_dataserver.service"
# Get the username
USERNAME=$(whoami)

# Replace placeholders in the template with actual values
sed "s|{{WORKING_DIR}}|$WORKING_DIR|g" services/drowbox_mqtt_dataserver.service.template | \
sed "s|{{EXEC_START}}|$EXEC_START|g" | \
sed "s|{{SCRIPT_PATH}}|$SCRIPT_PATH|g" | \

sed "s|{{USERNAME}}|$USERNAME|g" > services/drowbox_mqtt_dataserver.service

sudo cp services/drowbox_mqtt_dataserver.service $SERVICE_FILE

# Set permissions for the service file
sudo chmod 644 $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable drowbox_mqtt_dataserver

# Start the service immediately
sudo systemctl start drowbox_mqtt_dataserver

# Verify the service status
sudo systemctl status drowbox_mqtt_dataserver
