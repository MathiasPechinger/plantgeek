#!/bin/bash

# Set error handling
set -e  # Exit on any error
set -u  # Error on undefined variables

echo "Starting Controller Tests..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run the Python tests
echo "Running fridge controller temperature tests..."
python3 -m pytest tests/test_fridge_controller_temp_day.py -v


echo "Running test_heater_controller tests..."
python3 -m pytest tests/test_heater_controller.py -v

echo "All controller tests completed."

# Deactivate virtual environment if it was activated
if [ -d "venv" ]; then
    deactivate
fi 