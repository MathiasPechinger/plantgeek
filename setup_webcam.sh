#!/bin/bash

# Update package list
cd ip_cam
npm install
cd ..

# ----------------- Install Nginx -----------------
# # Define variables
WORKING_DIR="$(pwd)/ip_cam"
# SERVICE_DIR="$WORKING_DIR/services"
# Print working directory
echo "Working Directory: $WORKING_DIR"
# WORKING_DIR="/home/wolf/dev/drow_box"
EXEC_START="/usr/bin/node"
SCRIPT_PATH="$WORKING_DIR/server.js"
SERVICE_FILE="/etc/systemd/system/drowbox_camera.service"
# Get the username
USERNAME=$(whoami)

# Replace placeholders in the template with actual values
sed "s|{{WORKING_DIR}}|$WORKING_DIR|g" services/drowbox_camera.service.template | \
sed "s|{{EXEC_START}}|$EXEC_START|g" | \
sed "s|{{SCRIPT_PATH}}|$SCRIPT_PATH|g" | \

sed "s|{{USERNAME}}|$USERNAME|g" > services/drowbox_camera.service

sudo cp services/drowbox_camera.service $SERVICE_FILE

# Set permissions for the service file
sudo chmod 644 $SERVICE_FILE

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable the service to start on boot
sudo systemctl enable drowbox_camera

# Start the service immediately
sudo systemctl start drowbox_camera

# Verify the service status
sudo systemctl status drowbox_camera
