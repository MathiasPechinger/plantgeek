# ----------------- Install MySQL Server -----------------
# Update package list
sudo apt update

# Install MariaDB Server
sudo apt install -y mariadb-server

# Secure MariaDB Installation
sudo mysql_secure_installation <<EOF

Y
0
drowBox4ever
drowBox4ever
Y
Y
Y
Y
EOF

# Start and enable MariaDB service
sudo systemctl start mariadb
sudo systemctl enable mariadb

# Create a database and user
sudo mariadb -u root -ppassword <<EOF
CREATE DATABASE sensor_data;
CREATE USER 'drow'@'localhost' IDENTIFIED BY 'drowBox4ever';
GRANT ALL PRIVILEGES ON sensor_data.* TO 'drow'@'localhost';
FLUSH PRIVILEGES;
EOF

# Create a table
sudo mariadb -u root -ppassword <<EOF
USE sensor_data;
CREATE TABLE IF NOT EXISTS measurements (
    id INT AUTO_INCREMENT PRIMARY KEY,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    temperature_c FLOAT,
    humidity FLOAT,
    eco2 INT,
    tvoc INT,
    co2_state TINYINT,
    fridge_state TINYINT,
    light_state TINYINT
);
EOF

echo "Table created."


echo "MariaDB installation and setup complete."