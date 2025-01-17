#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p logs

# Function to start the application
start_app() {
    echo "Starting main application..."
    # Start zigbee emulator
    python tests/zigbee_emulator.py > logs/emulator.log 2>&1 &
    EMULATOR_PID=$!
    sleep 1  # Give emulator time to start
    
    # Start main app
    source venv/bin/activate
    TESTING=1 python app.py --no-camera > logs/app.log 2>&1 &
    APP_PID=$!
    sleep 1  # Wait for app to initialize
    echo "App started with PID $APP_PID"
}

# Function to stop the application
stop_app() {
    echo "Stopping application..."
    kill $APP_PID 2>/dev/null
    kill $EMULATOR_PID 2>/dev/null
    sleep 5  # Wait for app to fully stop
}

# Function to run a test with timeout
run_test_with_timeout() {
    local test_name=$1
    local test_command=$2
    local timeout_duration=$3
    local error_type=$4
    local expected_code=$5

    echo "=== Testing $test_name ==="
    
    # Extract mode from test command
    local mode=$(echo $test_command | awk '{print $NF}')
    
    # Start fresh app instance with mock sensor mode
    export MOCK_SENSOR_MODE=$mode
    sleep 1
    start_app
    
    echo "Waiting for $timeout_duration seconds..."
    # Wait for specified duration or until timeout
    local timeout_counter=0
    while [ $timeout_counter -lt $timeout_duration ]; do
        sleep 1
        timeout_counter=$((timeout_counter + 1))
        
        # Check if the error/warning is detected
        if check_error "$expected_code" "$error_type"; then
            unset MOCK_SENSOR_MODE
            stop_app
            return 0
        fi
    done
    
    # If we get here, the test timed out
    echo "✗ Test timed out after ${timeout_duration} seconds"
    kill $SENSOR_PID 2>/dev/null
    kill $TAIL_PID 2>/dev/null
    stop_app
    return 1
}

# Function to check for specific error or warning
check_error() {
    local expected_code=$1
    local error_type=$2  # "errors" or "warnings"
    
    HEALTH_STATUS=$(curl -s http://localhost:5000/system/$error_type)
    if [[ $HEALTH_STATUS == *"$expected_code"* ]]; then
        echo "✓ System correctly detected $error_type code $expected_code"
        return 0
    else
        return 1
    fi
}

# Run each test with its own timeout
run_test_with_timeout "Temperature Sensor Invalid" "python tests/mock_scd4x.py disconnect" 20 "errors" "1001"
TEMP_INVALID_TEST=$?

run_test_with_timeout "Temperature Sensor Frozen" "python tests/mock_scd4x.py freeze" 40 "errors" "1005"
TEMP_FROZEN_TEST=$?

run_test_with_timeout "Temperature Control High Warning" "python tests/mock_scd4x.py high_temp" 30 "warnings" "2002"
TEMP_HIGH_TEST=$?

run_test_with_timeout "CO2 Control High Warning" "python tests/mock_scd4x.py high_co2" 30 "warnings" "2004"
CO2_HIGH_TEST=$?

# run_test_with_timeout "Missing Timestamp" "python tests/mock_scd4x.py missing_timestamp" 20 "errors" "1002"
# TIMESTAMP_TEST=$?

run_test_with_timeout "System Overheated" "python tests/mock_scd4x.py overheat" 20 "errors" "1006"
OVERHEAT_TEST=$?

# Check if all tests passed
if [ $TEMP_INVALID_TEST -eq 0 ] && [ $TEMP_FROZEN_TEST -eq 0 ] && [ $TEMP_HIGH_TEST -eq 0 ] && [ $CO2_HIGH_TEST -eq 0 ] && [ $OVERHEAT_TEST -eq 0 ]; then
    echo "All sensor error tests completed successfully"
    exit 0
else
    echo "Some tests failed"
    exit 1
fi 