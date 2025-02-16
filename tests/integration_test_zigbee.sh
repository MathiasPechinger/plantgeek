#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p logs

# Start the main application in the background
echo "Starting main application..."
source venv/bin/activate
TESTING=1 python app.py --ci-testing > logs/app.log 2>&1 &
APP_PID=$!

# Wait for app to initialize
sleep 10

# Function to test individual socket failure
test_socket_failure() {
    local socket_name=$1
    local socket_index=$2
    
    echo "Testing failure of $socket_name socket..."
    
    # Start the zigbee emulator with specified socket failing after 10 seconds
    python tests/zigbee_emulator.py $socket_index > logs/emulator.log 2>&1 &
    EMULATOR_PID=$!

    # Wait for initial healthy state
    sleep 5

    # Check if system is initially healthy
    INITIAL_HEALTH=$(curl -s http://localhost:5000/system/errors)
    if [[ $INITIAL_HEALTH == "[]" ]]; then
        echo "✓ System initially healthy"
    else
        echo "✗ System not healthy when it should be"
        kill $EMULATOR_PID
        return 1
    fi

    # Wait for device failure
    sleep 30 # detection takes about 20 seconds

    # Check if system detected the failure
    HEALTH_STATUS=$(curl -s http://localhost:5000/system/errors)
    echo "Health status: $HEALTH_STATUS"

    if [[ $HEALTH_STATUS == *"1003"* ]]; then
        echo "✓ System correctly detected $socket_name socket failure"
        kill $EMULATOR_PID
        return 0
    else
        echo "✗ System failed to detect $socket_name socket failure"
        kill $EMULATOR_PID
        return 1
    fi
}

# Test each socket individually
echo "=== Testing Light Socket ==="
test_socket_failure "Light" 0
LIGHT_TEST=$?
sleep 2  # Wait between tests

echo "=== Testing Fridge Socket ==="
test_socket_failure "Fridge" 1
FRIDGE_TEST=$?
sleep 2  # Wait between tests

echo "=== Testing CO2 Socket ==="
test_socket_failure "CO2" 2
CO2_TEST=$?
sleep 2  # Wait between tests

echo "=== Testing Heater Socket ==="
test_socket_failure "Heater" 3
HEATER_TEST=$?

# Cleanup
echo "Cleaning up..."
kill $APP_PID

# Check if all tests passed
if [ $LIGHT_TEST -eq 0 ] && [ $FRIDGE_TEST -eq 0 ] && [ $CO2_TEST -eq 0 ] && [ $HEATER_TEST -eq 0 ]; then
    echo "All integration tests completed successfully"
    exit 0
else
    echo "Some tests failed"
    exit 1
fi 