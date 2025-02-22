#!/bin/bash

# Create log directory if it doesn't exist
mkdir -p logs

# Function to start the application
start_app() {
    echo "Starting main application..."
    # Start main app
    source venv/bin/activate
    TESTING=1 python app.py > logs/app.log 2>&1 &
    APP_PID=$!
    sleep 1  # Wait for app to initialize
    echo "App started with PID $APP_PID"
}

# Function to stop the application
stop_app() {
    echo "Stopping application..."
    kill $APP_PID 2>/dev/null
    sleep 5  # Wait for app to fully stop
}

# Function to check if the application is still running
check_app_status() {
    sleep 5
    if ps -p $APP_PID > /dev/null; then
        echo "✓ Application is running without errors"
        return 0
    else
        echo "✗ Application exited with an error"
        return 1
    fi
}

# Start the application
start_app

# Check the application status after 5 seconds
check_app_status
APP_STATUS=$?

# Stop the application
stop_app

# Exit with the application status
exit $APP_STATUS