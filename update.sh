#!/bin/bash

# MySQL credentials
DB_USER="drow"
DB_PASS="drowBox4ever"
DB_NAME="sensor_data"

# SQL command to add heater_state column
SQL_COMMAND="ALTER TABLE measurements ADD COLUMN heater_state BOOLEAN DEFAULT FALSE;"

# Check if column already exists
CHECK_COLUMN="SELECT COUNT(*) FROM information_schema.columns 
              WHERE table_schema = '$DB_NAME' 
              AND table_name = 'measurements' 
              AND column_name = 'heater_state';"

echo "Checking if heater_state column exists..."

# Execute the check
COLUMN_EXISTS=$(mysql -u "$DB_USER" -p"$DB_PASS" -N -B -e "$CHECK_COLUMN")

if [ "$COLUMN_EXISTS" -eq 0 ]; then
    echo "Adding heater_state column to measurements table..."
    mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" -e "$SQL_COMMAND"
    if [ $? -eq 0 ]; then
        echo "Successfully added heater_state column!"
    else
        echo "Error: Failed to add heater_state column"
        exit 1
    fi
else
    echo "heater_state column already exists. No action needed."
fi

# Update the data_writer_mysql.py query
echo "Updating data_writer_mysql.py with new query..."
sed -i 's/INSERT INTO measurements (temperature_c, humidity, eco2, light_state, fridge_state,co2_state) VALUES (%s, %s, %s, %s, %s, %s)/INSERT INTO measurements (temperature_c, humidity, eco2, light_state, fridge_state, co2_state, heater_state) VALUES (%s, %s, %s, %s, %s, %s, %s)/g' include/data_writer_mysql.py

if [ $? -eq 0 ]; then
    echo "Successfully updated data_writer_mysql.py!"
else
    echo "Error: Failed to update data_writer_mysql.py"
    exit 1
fi

echo "Update completed successfully!"
