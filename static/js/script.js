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

function updateTime() {
    document.getElementById('current-time').innerText = new Date().toLocaleTimeString();
    setTimeout(updateTime, 1000);
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

updateTime(); // Initialize the time update


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




var timespan = 120; // default timespan

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
var temperatureChart = new Chart(tempCtx, createChartConfig('Temperature (C)', 'rgb(255, 99, 132)'));
var humidCtx = document.getElementById('humidityChart').getContext('2d');
var humidityChart = new Chart(humidCtx, createChartConfig('Humidity (%)', 'rgb(54, 162, 235)'));
var eco2Ctx = document.getElementById('eco2Chart').getContext('2d');
var eco2Chart = new Chart(eco2Ctx, createChartConfig('eCO2 (ppm)', 'rgb(75, 192, 192)'));
var tvocCtx = document.getElementById('tvocChart').getContext('2d');
var tvocChart = new Chart(tvocCtx, createChartConfig('TVOC (ppb)', 'rgb(153, 102, 255)'));

function createChartConfig(label, borderColor) {
    return {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: label,
                borderColor: borderColor,
                data: []
            }]
        },
        options: {
            scales: {
                x: {  // Updated configuration for Chart.js v3
                    type: 'linear',
                    title: {
                        display: true,
                        text: 'last 24 hours'
                    },
                }
            }
        }
    };
}

function updateChart(chart, data) {
    // console.log("Updating chart with data:", data);

    if (data[0].length === 0) {
        console.log("Data array is empty, resetting chart data.");
        chart.data.labels = [];
        chart.data.datasets.forEach((dataset) => {
            dataset.data = [];
        });
    } else {
        // Assuming you have a way to generate labels or you use a simple index for labels
        chart.data.labels = data[0].map((_, index) => index); // Update labels if necessary
        chart.data.datasets.forEach((dataset, index) => {
            dataset.data = data[index]; // Update data within the dataset
        });
    }
    chart.update(); // Redraw the chart
}
// Function to create dynamic list items for state.json data
function createStateList(data) {
    const listContainer = document.getElementById('dynamic-list');
    listContainer.innerHTML = ''; // Clear any existing items
    const deviceMap = {
        light: 'Light',
        fridge: 'Fridge',
        co2: 'CO2 Valve'
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
        3: 'CO2 Valve'
    };

    deviceCounter = 1;

    for (const [deviceId, deviceData] of Object.entries(data)) {
        deviceCounter++;
        deviceMapID = deviceCounter - 1;

        if (deviceCounter > 4) {
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
            document.getElementById('actual-tvoc').innerText = data[0][3].toFixed(2);
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
            // console.log("Received data for charts:", data);  // Debug print
            if (data && data.length > 0) {
                var temps = data.map(d => d[0]);
                var humids = data.map(d => d[1]);
                var eco2s = data.map(d => d[2]);
                var tvocs = data.map(d => d[3]);
                
                updateChart(temperatureChart, [temps]);
                updateChart(humidityChart, [humids]);
                updateChart(eco2Chart, [eco2s]);
                updateChart(tvocChart, [tvocs]);
            } else {
                console.log("No data received, clearing charts");
                updateChart(temperatureChart, [[]]);
                updateChart(humidityChart, [[]]);
                updateChart(eco2Chart, [[]]);
                updateChart(tvocChart, [[]]);
            }
        },
        error: function(xhr, status, error) {
            console.error("Failed to fetch data:", error);
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

fetchData(); // Fetch data immediately
setInterval(fetchData, 3000);

fetchDataNow();
setInterval(fetchDataNow, 3000);

fetchFridgeState()
setInterval(fetchFridgeState, 3000);

fetchCPUTemperature();
setInterval(fetchCPUTemperature, 3000);

getZigbeeDevices();
setInterval(getZigbeeDevices, 3000);


setInterval(updateTemperatureDisplay, 3000);