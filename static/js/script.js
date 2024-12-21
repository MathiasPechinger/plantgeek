let activeIntervals = {};

function initializeTab(tabId) {
    stopAllIntervals();
    
    switch(tabId) {
        case 'stream':
            startStreamInterval();
            break;
        case 'zigbee':
            startZigbeeInterval();
            break;
        case 'environment':
            startEnvironmentInterval();
            break;
    }
}

function stopAllIntervals() {
    Object.values(activeIntervals).forEach(intervals => {
        intervals.forEach(interval => clearInterval(interval));
    });
    activeIntervals = {};
}

function startStreamInterval() {
    activeIntervals.stream = [];
    refreshImage();
    activeIntervals.stream.push(setInterval(refreshImage, 1000));
}

function startZigbeeInterval() {
    activeIntervals.zigbee = [];
    getZigbeeDevices();
    activeIntervals.zigbee.push(setInterval(getZigbeeDevices, 3000));
}

function startEnvironmentInterval() {
    activeIntervals.environment = [];
    const functions = [fetchData, fetchDataNow, fetchCPUTemperature, updateTemperatureDisplay];
    
    functions.forEach(func => {
        func();
        activeIntervals.environment.push(setInterval(func, 3000));
    });
}

// Initialize tab handling
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabs.forEach(tab => {
        tab.addEventListener('shown.bs.tab', function(event) {
            const targetId = event.target.href.split('#')[1];
            initializeTab(targetId);
            
            // Special handling for config tab
            if (targetId === 'config') {
                fetchConfig();
            }
        });
    });

    // Initialize the first active tab
    initializeTab('stream');
    setTimeSpanDataBaseRetrieval(1); // Set initial timespan and update charts
});

function fetchConfig() {
    fetch('/config')
        .then(response => response.json())
        .then(data => {
            populateConfigForm(data);
        })
        .catch(error => console.error('Error fetching config:', error));
}

function populateConfigForm(config) {
    // API Configuration
    document.getElementById('api_key').value = config.APIConfig.apiKey || '';
    document.getElementById('username').value = config.APIConfig.username || '';
    document.getElementById('device_name').value = config.PlanGeekBackend.deviceName || '';

    // Light Control
    document.getElementById('light_switch_on_time').value = config.LightControl.switchOnTime || '';
    document.getElementById('light_switch_off_time').value = config.LightControl.switchOffTime || '';

    // CO2 Control
    document.getElementById('co2_target_value').value = config.CO2Control.targetValue || '';
    document.getElementById('co2_hysteresis').value = config.CO2Control.hysteresis || '';

    // Temperature Control
    document.getElementById('target_temperature_day').value = config.TemperatureControl.targetDayTemperature || '';
    document.getElementById('target_temperature_night').value = config.TemperatureControl.targetNightTemperature || '';
    document.getElementById('temperature_hysteresis').value = config.TemperatureControl.hysteresis || '';

    // Humidity Control
    document.getElementById('target_humidity').value = config.HumidityControl.targetHumidity || '';
    document.getElementById('humidity_hysteresis').value = config.HumidityControl.hysteresis || '';

    // Fridge Control Mode
    if (config.FridgeControl && config.FridgeControl.controlMode) {
        document.getElementById('fridge_control_mode').value = config.FridgeControl.controlMode;
    }
}

function updateTemperatureDisplay() {
    const cpuTemperature = document.getElementById('cpu_temperature');
    const rp1AdcTemperature = document.getElementById('rp1_adc_temperature');
    const cpuTemperatureValue = parseFloat(cpuTemperature.innerText);
    const rp1AdcTemperatureValue = parseFloat(rp1AdcTemperature.innerText);

    if (cpuTemperatureValue > 80) {
        cpuTemperature.style.color = 'red';
        cpuTemperature.style.fontWeight = 'bold';
    } else {
        cpuTemperature.style.color = 'inherit';
        cpuTemperature.style.fontWeight = 'normal';
    }

    if (rp1AdcTemperatureValue > 80) {
        rp1AdcTemperature.style.color = 'red';
        rp1AdcTemperature.style.fontWeight = 'bold';
    } else {
        rp1AdcTemperature.style.color = 'inherit';
        rp1AdcTemperature.style.fontWeight = 'normal';
    }
}


function setLightTimes() {
    const onTime = document.getElementById('light-on-time').value;
    const offTime = document.getElementById('light-off-time').value;
    fetch('/set-light-times', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ onTime, offTime })
    }).then(response => response.json())
    .then(data => console.log(data));
}

// function setFanSpeed(speed) {
//     fetch('/set-fan-speed', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json',
//         },
//         body: JSON.stringify({ speed })
//     })
//     .then(response => response.json())
//     .then(data => console.log(data))
//     .catch(error => console.error('Error:', error));
// }

function sendToggleStatus(toggleId, toggleValue) {
    // Update the visibility of the associated div
    const divId = 'content_div' + toggleId.replace('toggle', '');
    const associatedDiv = document.getElementById(divId);
    
    if (associatedDiv) {
        if (toggleValue === 1) {
            associatedDiv.style.display = 'block';
        } else {
            associatedDiv.style.display = 'none';
        }
    }

    // Manage intervals
    if (toggleValue === 1) {
        startIntervals(toggleId);
    } else {
        stopIntervals(toggleId);
    }

    // Send the toggle status to the server
    fetch('/update_toggle', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
            'toggle_id': toggleId,
            'toggle_value': toggleValue
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log(`Toggle ${data.toggle_id} updated to ${data.toggle_value}`);
        } else {
            console.error(`Failed to update toggle: ${data.message}`);
        }
    });
}

// legacy function
function saveApiKey() {
    const api_key = document.getElementById('api-key-input').value;
    $.ajax({
        url: '/save_api_key',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({api_key: api_key}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function setPumpPower(power) {
    $.ajax({
        url: '/setPumpPower',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({power: power}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function activatePumpOnce() {
    $.ajax({
        url: '/activatePumpOnce',
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function setPumpTime(time) {
    $.ajax({
        url: '/setPumpTime',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({time: time}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}



function setFanSpeed(speed) {
    $.ajax({
        url: '/setFanSpeed',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({speed: speed}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}



function requestCO2(state) {
    $.ajax({
        url: '/co2/control',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({state: state}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function zigbeePairing(state) {
    
    const pairingText = document.getElementById('pairing-text');
    const pairingCircle = document.getElementById('pairing-circle');

    if (state) {
        pairingText.textContent = 'Pairing...';
        pairingCircle.style.display = 'inline-block';
    } else {
        pairingText.textContent = 'Pairing Disabled';
        pairingCircle.style.display = 'none';
    }

    $.ajax({
        url: '/zigbee/control',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({state: state}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}




var timespan = 1; // default timespan to 1 hour

function movingAverage(data, period) {
    let result = [];
    for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
            // Not enough data to calculate the moving average, use the actual data instead
            result.push(data[i]);
        } else {
            // Calculate the sum of the 'period' number of entries, including the current one
            let sum = 0;
            for (let j = 0; j < period; j++) {
                sum += data[i - j];
            }
            // Calculate the average and add it to the result array
            result.push(sum / period);
        }
    }
    return result;
}


function sampleData(data, sampleRate) {
    return data.filter((_, index) => index % sampleRate === 0);
}


function averageData(data, interval) {
    let result = [];
    for (let i = 0; i < data.length; i += interval) {
        let sum = 0;
        let count = 0;
        for (let j = i; j < i + interval && j < data.length; j++) {
            sum += data[j];
            count++;
        }
        result.push(sum / count);
    }
    return result;
}


function updateTimespan() {
    var newTimespan = document.getElementById('timespan').value;
    timespan = parseInt(newTimespan, 10);
    fetchData(); // Immediately fetch new data with the updated timespan
}

// Define the chart configurations
var tempCtx = document.getElementById('temperatureChart').getContext('2d');
var temperatureChart = new Chart(tempCtx, createChartConfig(
    'Temperature (°C)', 'rgb(255, 99, 132)', 
    'Light State', 'rgb(255, 205, 86)', 
    'Fridge State', 'rgb(54, 162, 235)',
    'Heater State', 'rgb(255, 99, 71)'
));
var humidCtx = document.getElementById('humidityChart').getContext('2d');
var humidityChart = new Chart(humidCtx, createChartConfig('Humidity (%)', 'rgb(54, 162, 235)'));
var eco2Ctx = document.getElementById('eco2Chart').getContext('2d');
var eco2Chart = new Chart(eco2Ctx, createChartConfig(
    'CO2 (ppm)', 'rgb(75, 192, 192)', 
    null, null, 
    'Valve State', 'rgb(255, 159, 64)',
    null, null
));

function createChartConfig(label, borderColor, lightStateLabel, lightStateColor, fridgeStateLabel, fridgeStateColor, heaterStateLabel, heaterStateColor) {
    const datasets = [
        {
            label: label,
            borderColor: borderColor,
            data: [],
            yAxisID: 'y',
            pointRadius: 0,
            borderWidth: 2,
            tension: 0.4
        }
    ];

    if (lightStateLabel) {
        datasets.push({
            label: lightStateLabel,
            borderColor: lightStateColor,
            backgroundColor: lightStateColor,
            data: [],
            yAxisID: 'y1',
            fill: false,
            stepped: true
        });
    }

    if (fridgeStateLabel) {
        datasets.push({
            label: fridgeStateLabel,
            borderColor: fridgeStateColor,
            backgroundColor: fridgeStateColor,
            data: [],
            yAxisID: 'y1',
            fill: false,
            stepped: true
        });
    }

    if (heaterStateLabel) {
        datasets.push({
            label: heaterStateLabel,
            borderColor: heaterStateColor,
            backgroundColor: heaterStateColor,
            data: [],
            yAxisID: 'y1',
            fill: false,
            stepped: true
        });
    }

    return {
        type: 'line',
        data: {
            labels: [],
            datasets: datasets
        },
        options: {
            scales: {
                x: {
                    type: 'linear',
                    title: {
                        display: true,
                        text: getTimespanLabel()
                    },
                    ticks: {
                        callback: function(value) {
                            const absValue = Math.abs(value);
                            if (timespan <= 1) {
                                return absValue + 'm';
                            } else {
                                return (absValue/60).toFixed(1) + 'h';
                            }
                        }
                    }
                },
                y: {
                    type: 'linear',
                    position: 'left',
                    title: {
                        display: true,
                        text: label
                    }
                },
                y1: datasets.length > 1 ? {
                    type: 'linear',
                    position: 'right',
                    title: {
                        display: true,
                        text: 'State'
                    },
                    grid: {
                        drawOnChartArea: false
                    },
                    min: 0,
                    max: 1
                } : undefined
            }
        }
    };
}

function getTimespanLabel() {
    switch(timespan) {
        case 1:
            return 'last hour';
        case 4:
            return 'last 4 hours';
        case 12:
            return 'last 12 hours';
        case 24:
        default:
            return 'last 24 hours';
    }
}

function updateChart(chart, data) {
    if (data[0].length === 0) {
        console.log("Data array is empty, resetting chart data.");
        chart.data.labels = [];
        chart.data.datasets.forEach((dataset) => {
            dataset.data = [];
        });
    } else {
        // Create time labels based on timespan
        const totalPoints = data[0].length;
        chart.options.scales.x.min = -timespan * 60;  // Set min based on timespan in minutes
        chart.options.scales.x.max = 0;               // Current time is always 0

        // Update datasets with their respective data
        chart.data.datasets.forEach((dataset, index) => {
            dataset.data = data[index].map((value, i) => ({
                x: -(timespan * 60 * (1 - i/totalPoints)),  // Calculate x value in minutes
                y: value
            }));
        });
    }
    chart.update('none'); // Update without animation for better performance
}



// Function to create dynamic list items for state.json data
function createStateList(data) {
    const listContainer = document.getElementById('dynamic-list');
    listContainer.innerHTML = ''; // Clear any existing items
    // todo: this just be dynamic or not?
    const deviceMap = {
        light: 'Light',
        fridge: 'Fridge',
        co2: 'CO2 Valve',
        heater: 'Heater'
    };
    const usedDevices = Object.keys(deviceMap);
    for (const [deviceId, deviceData] of Object.entries(data)) {
        if (usedDevices.includes(deviceId)) {
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            const deviceName = deviceMap[deviceId];
            listItem.textContent = `ID: ${deviceId}, Device: ${deviceName}, State: ${deviceData.state}, Voltage: ${deviceData.voltage}, Power: ${deviceData.power}`;
            listContainer.appendChild(listItem);
            usedDevices.splice(usedDevices.indexOf(deviceId), 1);
        }
    }
    usedDevices.forEach(deviceId => {
        const listItem = document.createElement('li');
        listItem.className = 'list-group-item';
        const deviceName = deviceMap[deviceId];
        listItem.textContent = `ID: ${deviceId}, Device: ${deviceName}, State: Unused`;
        listContainer.appendChild(listItem);
    });
}


function getZigbeeDevices() {
    $.ajax({
        url: '/getZigbeeDevices',
        type: 'POST',
        contentType: 'application/json',
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
            createDatabaseList(response);
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

// Function to create dynamic list items for JSON data
function createDatabaseList(data) {
    const listContainer = document.getElementById('dynamic-list');
    listContainer.innerHTML = ''; // Clear any existing items


    const deviceMap = {
        0: 'unused',
        1: 'Light',
        2: 'Fridge',
        3: 'CO2 Valve',
        4: 'Heater'
    };

    deviceCounter = 1;

    for (const [deviceId, deviceData] of Object.entries(data)) {
        deviceCounter++;
        deviceMapID = deviceCounter - 1;

        if (deviceCounter > 5) {
            deviceMapID = 0; // unused extra devices
        }

        const deviceInfo = deviceData.split(', ');
        const deviceId = deviceInfo[0].split(': ')[1];
        const availability = deviceInfo[1].split(': ')[1];

        if (availability === 'True') {
            const deviceType = deviceMap[deviceMapID];
            const listItem = document.createElement('li');
            listItem.className = 'list-group-item';
            listItem.textContent = `${deviceType} socket `;
            
            const buttonOn = document.createElement('button');
            buttonOn.className = 'btn btn-success';
            buttonOn.textContent = 'on';
            buttonOn.addEventListener('click', () => {
                switchPowerSocket(true, deviceId);
            });
            listItem.appendChild(buttonOn);

            const buttonOff = document.createElement('button');
            buttonOff.className = 'btn btn-danger';
            buttonOff.textContent = 'off';
            buttonOff.addEventListener('click', () => {
                switchPowerSocket(false, deviceId);
            });
            listItem.appendChild(buttonOff);

            const buttonRemove = document.createElement('button');
            buttonRemove.className = 'btn btn-warning';
            buttonRemove.textContent = 'remove';
            buttonRemove.addEventListener('click', () => {
                const confirmRemove = confirm('Are you sure you want to remove this device?');
                if (confirmRemove) {
                    removeZigbeeDevice(deviceId);
                }
            });
            listItem.appendChild(buttonRemove);
            
            listContainer.appendChild(listItem);
    
        }
    }
}

function setPowerSocketOverrideToggle(rate, ieeeAddr) {
    $.ajax({
        url: '/togglePowerSocketOverride',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({rate: rate, ieeeAddr: ieeeAddr}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function removeZigbeeDevice(ieeeAddr) {
    $.ajax({
        url: '/removeZigbeeDevice',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ieeeAddr: ieeeAddr}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function switchPowerSocket(state, ieeeAddr) {
    $.ajax({
        url: '/switchPowerSocket',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({state: state, ieeeAddr: ieeeAddr}),
        success: function(response) {
            // console.log("Response: " + JSON.stringify(response));
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function calculateLastSeen(lastSeen) {
    const currentTime = new Date();
    const lastSeenTime = new Date(lastSeen);
    const timeDifference = currentTime - lastSeenTime;
    // const hoursDifference = Math.floor(timeDifference / (1000 * 60 * 60));
    const secondsDifference = Math.floor(timeDifference / 1000);
    return secondsDifference;
}

function fetchCPUTemperature() {
    $.ajax({
        url: '/data/rpi-temperature',
        success: function(data) {
            if (data.cpu_thermal && data.cpu_thermal.length > 0) {
                // console.log("CPU Temperature:", data.cpu_thermal[0][1]);
                // console.log("ADC Temperature:", data.rp1_adc[0][1]);
                document.getElementById('cpu_temperature').innerText = data.cpu_thermal[0][1].toFixed(2);  // Format to 2 decimal places
                document.getElementById('rp1_adc_temperature').innerText = data.rp1_adc[0][1].toFixed(2);  // Format to 2 decimal places
            } else {
                console.log("CPU temperature data is not available.");
            }
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch CPU temperature:", error);
        }
    });
}

function fetchDataNow() {
    $.ajax({
        url: '/data/now',
        success: function(data) {
            // console.log("Received latest data:", data);
            document.getElementById('actual-temperature').innerText = data[0][0].toFixed(2);
            document.getElementById('actual-humidity').innerText = data[0][1].toFixed(2);
            document.getElementById('actual-eco2').innerText = data[0][2].toFixed(2);
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch latest data:", error);
        }
    });
}

function fetchFridgeState() {
    $.ajax({
        url: '/fridge_state',
        success: function(data) {
            // console.log("Received latest data:", data);
            if (data == true)
            {
                // document.getElementById('fridge-progress').setAttribute('aria-valuenow', '100');
                document.getElementById('fridge-progress').style.width = '100%';
                document.getElementById('fridge-state').innerText = "cooling";
            }
            else
            {
                // document.getElementById('fridge-progress').setAttribute('aria-valuenow', '0');
                document.getElementById('fridge-progress').style.width = '0%';
                document.getElementById('fridge-state').innerText = "standby";
            }
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch latest data:", error);
        }
    });
}

function fetchData() {
    $.ajax({
        url: '/data?timespan=' + timespan,
        success: function(data) {
            if (data && data.length > 0) {
                var temps = data.map(d => d[0]);
                var humids = data.map(d => d[1]);
                var eco2s = data.map(d => d[2]);
                var light_state = data.map(d => d[3]);
                var fridge_state = data.map(d => d[4]);
                var co2_state = data.map(d => d[5]);
                var heater_state = data.map(d => d[6]);

                updateChart(temperatureChart, [temps, light_state, fridge_state, heater_state]);
                updateChart(humidityChart, [humids]);
                updateChart(eco2Chart, [eco2s, co2_state]);
            } else {
                console.log("No data received, clearing charts");
                updateChart(temperatureChart, [[], [], [], []]);
                updateChart(humidityChart, [[]]);
                updateChart(eco2Chart, [[], []]);
            }
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch data:", error);
        }
    });
}

function setTimeSpanDataBaseRetrieval(timeSpan) {
    timespan = timeSpan; // Update the global timespan variable
    
    // Update x-axis labels for all charts
    [temperatureChart, humidityChart, eco2Chart].forEach(chart => {
        chart.options.scales.x.title.text = getTimespanLabel();
        chart.update();
    });

    $.ajax({
        url: '/dataFetchTimeSpan',
        type: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({timeSpan: timeSpan}),
        success: function(response) {
            fetchData(); // Fetch new data with updated timespan
        },
        error: function(xhr, status, error) {
            console.log("Error: " + error);
            console.log("Status: " + status);
            console.dir(xhr);
        }
    });
}

function rebootSystem() {
    if (confirm('Are you sure you want to reboot the system?')) {
        fetch('/reboot', {
            method: 'POST',
            headers: {
                'Authorization': 'Basic ' + btoa('admin:admin_password'),  // Update with your actual authentication mechanism
                'Content-Type': 'application/json'
            },
        })
        .then(response => response.json())
        .then(data => alert('Reboot initiated.'))
        .catch(error => console.error('Error:', error));
    }
}

function refreshImage() {
    const img = document.getElementById('webcamImage');
    img.src = '/static/cameraImages/latest/lastFrame.jpg?timestamp=' + new Date().getTime();
}

function startIntervals(toggleId) {
    if (!intervals[toggleId]) {
        intervals[toggleId] = [];
    }

    // Define the functions and time steps for each toggle
    let intervalConfigs = [];

    switch(toggleId) {
        case 'toggle_image_stream':
            intervalConfigs = [
                {func: refreshImage, timeStep: 1000},
            ];
            break;
        case 'toggle_fridge_state':
            intervalConfigs = [
                {func: fetchFridgeState, timeStep: 3000}
            ];
            break;
        case 'toggle_environment_graph':
            intervalConfigs = [
                {func: fetchData, timeStep: 3000},
                {func: fetchDataNow, timeStep: 3000},
                {func: fetchCPUTemperature, timeStep: 3000},
                {func: updateTemperatureDisplay, timeStep: 3000}
            ];
            break;
        case 'toggle_zigbee_dashboard':
            intervalConfigs = [
                {func: getZigbeeDevices, timeStep: 3000}
            ];
            break;
        // Add more cases as needed for additional toggles
        default:
            console.error('Unknown toggle ID');
            return;
    }

    intervalConfigs.forEach(config => {
        config.func();  // Execute the function immediately
        const intervalId = setInterval(config.func, config.timeStep);
        intervals[toggleId].push(intervalId);
    });
}

function stopIntervals(toggleId) {
    if (intervals[toggleId]) {
        intervals[toggleId].forEach(intervalId => clearInterval(intervalId));
        intervals[toggleId] = null;
    }
}

function saveDeviceName() {
    const deviceName = document.getElementById('device-name').value;
    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ device_name: deviceName })
    })
    .then(response => response.json())
    .then(data => {
        console.log('Device name saved:', data);
        alert('Device name saved successfully!');
    })
    .catch(error => {
        console.error('Error saving device name:', error);
        alert('Error saving device name');
    });
}

// Add this function to show notifications
function showNotification(message, isSuccess) {
    const notificationDiv = document.createElement('div');
    notificationDiv.className = `alert ${isSuccess ? 'alert-success' : 'alert-danger'} alert-dismissible fade show position-fixed top-0 end-0 m-3`;
    notificationDiv.role = 'alert';
    notificationDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    document.body.appendChild(notificationDiv);

    // Remove the notification after 5 seconds
    setTimeout(() => {
        notificationDiv.remove();
    }, 5000);
}

// Update the form submission handler
document.getElementById('configForm').addEventListener('submit', function(event) {
    event.preventDefault();
    
    const submitButton = this.querySelector('button[type="submit"]');
    const originalButtonText = submitButton.innerHTML;
    submitButton.disabled = true;
    submitButton.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Saving...';

    const formData = new FormData(event.target);
    const jsonData = {};

    formData.forEach((value, key) => {
        jsonData[key] = value;
    });

    fetch('/save_config', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(jsonData)
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        showNotification('Configuration saved successfully!', true);
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification(`Failed to save configuration: ${error.message}`, false);
    })
    .finally(() => {
        // Reset button state
        submitButton.disabled = false;
        submitButton.innerHTML = originalButtonText;
    });
});
