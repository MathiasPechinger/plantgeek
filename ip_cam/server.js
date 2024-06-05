const express = require('express');
const WebSocket = require('ws');
const http = require('http');

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

const { spawn } = require('child_process');
const ffmpeg = spawn('ffmpeg', [
  '-f', 'v4l2',
  '-framerate', '1',
  '-input_format', 'mjpeg',
  '-i', '/dev/video0',
  '-f', 'mjpeg',
  '-q:v', '20',
  '-',
]);

ffmpeg.stdout.on('data', (data) => {
  broadcast(data);
});

ffmpeg.stderr.on('data', (data) => {
//   console.error(`stderr: ${data}`);
});

ffmpeg.on('close', (code) => {
  console.log(`child process exited with code ${code}`);
});
