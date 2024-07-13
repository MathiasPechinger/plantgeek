#!/bin/bash

# Update package list
sudo apt update

sudo apt install python3-pip
sudo apt install python3-venv python3-full -y

# for picamera2 -> not sure if needed
# sudo apt-get install -y cmake libboost-python-dev libboost-system-dev libjpeg-dev libtiff-dev # not sure if needed
# sudo apt-get install -y libcamera-apps libcamera-dev
# sudo apt install -y python3-picamera2
# sudo apt-get install libcap-dev


python3 -m venv --system-site-packages venv # --system-site-packages must be added because there is a bug with venv and picamera2
source venv/bin/activate
pip install -r requirements.txt




# ----------------- Install Nginx -----------------
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
