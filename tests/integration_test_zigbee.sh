#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p logs

# Start the main application in the background
echo "Starting main application..."
source venv/bin/activate
python app.py > logs/app.log 2>&1 &
APP_PID=$!

# Wait for app to initialize
sleep 10

# Start the zigbee emulator in the background
echo "Starting Zigbee emulator..."
python tests/zigbee_emulator.py > logs/emulator.log 2>&1 &
EMULATOR_PID=$!

# Wait for emulator to initialize and connect
sleep 5

# Check if system is healthy (should be true at this point)
INITIAL_HEALTH=$(curl -s http://localhost:5000/system/errors)
if [[ $INITIAL_HEALTH == "[]" ]]; then
    echo "✓ System initially healthy"
else
    echo "✗ System not healthy when it should be"
    exit 1
fi

# Kill the zigbee emulator to simulate failure
echo "Killing Zigbee emulator to simulate failure..."
kill $EMULATOR_PID

# Wait for the system to detect the failure
sleep 30

# Check if system detected the zigbee error
HEALTH_STATUS=$(curl -s http://localhost:5000/system/errors)
echo "Health status: $HEALTH_STATUS"
if [[ $HEALTH_STATUS == *"1003"* ]]; then
    echo "✓ System correctly detected Zigbee failure"
else
    echo "✗ System failed to detect Zigbee failure"
    exit 1
fi

# Cleanup
echo "Cleaning up..."
kill $APP_PID

echo "Integration test completed successfully"
exit 0 