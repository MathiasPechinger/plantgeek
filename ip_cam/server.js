const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const { spawn } = require('child_process');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

app.use(express.static('public')); // Serve your HTML file from public directory

wss.on('connection', function connection(ws) {
  console.log('Client connected');
  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
  });
  ws.on('close', () => console.log('Client disconnected'));
});

const broadcast = (data) => {
  wss.clients.forEach((client) => {
    if (client.readyState === WebSocket.OPEN) {
      client.send(data);
    }
  });
};

server.listen(8080, () => {
  console.log('Server running on http://192.168.2.167:8080');
});

// Function to capture a single image and broadcast it
const captureImage = () => {
  const ffmpeg = spawn('ffmpeg', [
    '-f', 'v4l2',
    '-framerate', '5', // Adjusted frame rate to match driver's automatic adjustment
    '-input_format', 'mjpeg',
    '-i', '/dev/video0',
    '-frames:v', '1',
    '-q:v', '2',
    '-f', 'mjpeg',
    'pipe:1',
  ]);

  let imageData = Buffer.alloc(0);

  ffmpeg.stdout.on('data', (data) => {
    imageData = Buffer.concat([imageData, data]);
  });

  ffmpeg.stdout.on('end', () => {
    broadcast(imageData);
  });

  ffmpeg.stderr.on('data', (data) => {
    // console.error(`stderr: ${data}`);
  });

  ffmpeg.on('close', (code) => {
    if (code !== 0) {
      // console.error(`ffmpeg process exited with code ${code}`);
    }
  });
};

// Capture an image every 5 seconds
setInterval(captureImage, 5000);
