# PlantGeek Build Checklist

Use this checklist to track your progress while building your PlantGeek system.

## Pre-Build Preparation

### Safety & Legal
- [ ] Read and understand the [safety disclaimer](manual.md#disclaimer)
- [ ] Verify compliance with local electrical regulations
- [ ] Prepare safe workspace for electrical work
- [ ] Have emergency contact information ready

### Component Procurement
- [ ] **Raspberry Pi 5 (4GB)** - Main control unit
- [ ] **Power Supply** - Official Raspberry Pi supply
- [ ] **Camera** - Compatible Pi camera with CSI cable
- [ ] **Zigbee Coordinator** - ZBDongle-P or Conbee 3
- [ ] **Zigbee Sockets** - Ledvance sockets (tested)
- [ ] **Environment Sensor** - SCD40 or SCD41
- [ ] **Fridge** - Recommended: OK. OFR 311 E
- [ ] **CO₂ System** - SodaStream bottle + regulator
- [ ] **Grow Light** - 100W (Spiderfarmer tested)
- [ ] **Heater** - LightHouse ECOHEAT or similar
- [ ] **Fans (2x)** - For airflow
- [ ] **Power Strip** - Internal power distribution
- [ ] **Temperature Relay** - Safety fallback
- [ ] **Mounting Grid** - For component mounting
- [ ] **Sheet Metal Panel** - For condensation collection
- [ ] **Cable Management** - Zip ties and mounts

## Hardware Assembly

### Fridge Preparation
- [ ] Remove internal components (keep bottom tray)
- [ ] Install sheet metal panel on rear wall
- [ ] Create power access opening at top
- [ ] Test fit all components before permanent installation

### Power System Setup
- [ ] ⚠️ **WARNING: Electrical work - ensure power is OFF**
- [ ] Modify power strip for cable pass-through
- [ ] Install external temperature relay
- [ ] Set temperature relay threshold (35°C recommended)
- [ ] Test relay operation with hot water
- [ ] Wire external power distribution

### Component Mounting
- [ ] Install metal tray at top of fridge
- [ ] Mount Zigbee sockets on rear of tray
- [ ] Secure fan(s) with zip ties
- [ ] Position heater (ensure no contact with other components)
- [ ] Install mounting grid for accessories
- [ ] Organize cables with cable mounts

### CO₂ System
- [ ] **WARNING: Keep CO₂ bottle upright at all times**
- [ ] Connect pressure regulator to CO₂ bottle
- [ ] Connect valve to Zigbee socket
- [ ] Test system for leaks
- [ ] Verify automatic shutoff capability

## Electronics Setup

### Raspberry Pi Configuration
- [ ] Download Raspberry Pi Imager
- [ ] Prepare SD card with OS
- [ ] Configure hostname: "plantgeek"
- [ ] Set username: "plantgeek" 
- [ ] Configure Wi-Fi (5GHz recommended)
- [ ] Enable SSH access
- [ ] Insert SD card and power on Pi

### Sensor Connections
- [ ] Connect SCD40/41 sensor to I2C pins
- [ ] Connect camera via CSI interface
- [ ] Plug in Zigbee coordinator USB stick
- [ ] Verify all connections are secure

### Software Installation
- [ ] SSH into Raspberry Pi: `ssh plantgeek@plantgeek`
- [ ] Clone repository: `git clone https://github.com/MathiasPechinger/plantgeek.git`
- [ ] Run setup script: `./setup.sh`
- [ ] Wait for installation completion (~7-8 minutes)
- [ ] Verify web interface at `http://plantgeek:5000`

### Zigbee Device Pairing
- [ ] Access Zigbee2MQTT at `http://plantgeek:8080`
- [ ] Enable "Permit join"
- [ ] Pair all Zigbee sockets one by one
- [ ] Verify devices appear in PlantGeek frontend
- [ ] Test manual control of each device

## System Testing

### Basic Functionality
- [ ] Verify sensor readings display correctly
- [ ] Test camera feed
- [ ] Manually control each Zigbee device
- [ ] Check temperature control
- [ ] Verify CO₂ system operation
- [ ] Test lighting controls

### Safety Systems Testing
- [ ] **Power Failure Test**: Disconnect Pi power, verify sockets shut down after 60s
- [ ] **Communication Loss Test**: Disconnect Zigbee coordinator, verify timeout behavior
- [ ] **Sensor Failure Test**: Disconnect sensor, verify error triggers and shutdown
- [ ] **Overheating Test**: Test both internal sensor and external relay responses
- [ ] **Manual Emergency Stop**: Verify ability to quickly shut down system

### Performance Verification
- [ ] Monitor system for 24 hours
- [ ] Check for error messages in logs
- [ ] Verify environmental controls maintain setpoints
- [ ] Test day/night lighting cycles
- [ ] Confirm CO₂ regulation works properly

## Final Setup

### Plant Installation
- [ ] Prepare growing medium
- [ ] Install plants in bottom tray
- [ ] Set initial environmental parameters
- [ ] Configure lighting schedule
- [ ] Set CO₂ target levels

### Documentation & Monitoring
- [ ] Create system operation log
- [ ] Document initial settings
- [ ] Schedule regular maintenance checks
- [ ] Set up monitoring/alert preferences
- [ ] Create backup of configuration

## Ongoing Maintenance Schedule

### Weekly Checks
- [ ] Visual inspection of all components
- [ ] Check for error messages
- [ ] Monitor plant health
- [ ] Verify environmental readings

### Monthly Checks
- [ ] Test power failure safety (Pi disconnect)
- [ ] Test Zigbee communication safety
- [ ] Clean camera lens
- [ ] Check CO₂ bottle level

### Quarterly Checks
- [ ] Test sensor failure response
- [ ] Test temperature safety systems
- [ ] Deep clean all components
- [ ] Update software if needed
- [ ] Review and update documentation

---

## Emergency Contacts & Resources

- **GitHub Issues**: [PlantGeek Issues](https://github.com/MathiasPechinger/plantgeek/issues)
- **Email Support**: beta@plantgeek.de
- **Video Guide**: [Quick Start Video](https://youtu.be/ruVc4RdbNsQ)
- **Complete Manual**: [Technical Documentation](manual.md)

---

**⚠️ SAFETY REMINDER**
This is a DIY project involving electrical components and pressurized gas. Always prioritize safety over convenience. When in doubt, consult with qualified professionals. 