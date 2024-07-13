#!/bin/bash

# Update package list
sudo apt-get update
sudo apt-get upgrade -y

sudo apt-get install python3-virtualenv -y


python3 -m venv --system-site-packages venv # --system-site-packages must be added because there is a bug with venv and picamera2
source venv/bin/activate
pip install -r requirements.txt

pip install --upgrade numpy simplejpeg # fixes an issue with picam

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
