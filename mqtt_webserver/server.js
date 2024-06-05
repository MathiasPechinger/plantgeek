const express = require('express');
const fs = require('fs');
const path = require('path');
const cors = require('cors');
const app = express();
const port = 5010;

// Enable CORS for all routes
app.use(cors());

// Middleware to serve static files (e.g., your HTML, CSS, JavaScript)
app.use(express.static('public'));

// Endpoint to get state.json data
app.get('/zigbee/state', (req, res) => {
    const stateFilePath = '/home/drow/zigbee2mqtt/data/state.json';

    fs.readFile(stateFilePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading state.json:', err);
            res.status(500).json({ error: 'Failed to read state.json' });
            return;
        }
        res.json(JSON.parse(data));
    });
});

// Endpoint to get data from JSON file (previously thought to be database.db)
app.get('/zigbee/devices', (req, res) => {
    const dbFilePath = '/home/drow/zigbee2mqtt/data/database.db';

    fs.readFile(dbFilePath, 'utf8', (err, data) => {
        if (err) {
            console.error('Error reading database.json:', err);
            res.status(500).json({ error: 'Failed to read database.json' });
            return;
        }

        try {
            const devices = data.trim().split('\n').map(JSON.parse);
            res.json(devices);
        } catch (parseError) {
            console.error('Error parsing database.json:', parseError);
            res.status(500).json({ error: 'Failed to parse database.json' });
        }
    });
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});
