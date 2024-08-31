const express = require('express');
const { spawn } = require('child_process');
const https = require('https');
const fs = require('fs');
const ip = require('ip');
const path = require('path');
const app = express();
const server = https.createServer({
  key: fs.readFileSync('server.key'),
  cert: fs.readFileSync('server.crt')
}, app);
const io = require('socket.io')(server);

// 静的ファイルの提供
app.use(express.static('static'));
app.use('/nfts/images', express.static(path.join(__dirname, 'nfts', 'images')));
app.use('/nfts/nft_metadata', express.static(path.join(__dirname, 'nfts', 'nft_metadata')));

// CORS設定
app.use((req, res, next) => {
  res.header("Access-Control-Allow-Origin", "*");
  res.header("Access-Control-Allow-Headers", "Origin, X-Requested-With, Content-Type, Accept");
  next();
});

const pythonProcess = spawn('python3', ['app.py']);

pythonProcess.stdout.on('data', (data) => {
  console.log(`Python output: ${data}`);
});

pythonProcess.stderr.on('data', (data) => {
  console.error(`Python error: ${data}`);
});

pythonProcess.stdout.on('data', (data) => {
  try {
    const result = JSON.parse(data);
    console.log('Sending detection result to client:', result);
    io.emit('detection_result', result);
  } catch (error) {
    console.error('Error parsing Python output:', error);
    console.error('Raw Python output:', data.toString());
    io.emit('detection_result', { error: 'Server error processing detection result' });
  }
});

io.on('connection', (socket) => {
  console.log('A user connected');

  socket.on('detect_object', (imageData) => {
    pythonProcess.stdin.write(JSON.stringify({image: imageData}) + '\n');
  });

  socket.on('disconnect', () => {
    console.log('User disconnected');
  });
});

pythonProcess.stdout.on('data', (data) => {
  try {
    const result = JSON.parse(data);
    console.log('Sending detection result to client:', result);
    io.emit('detection_result', result);
  } catch (error) {
    console.error('Error parsing Python output:', error);
  }
});

const PORT = process.env.PORT || 3000;
const ipAddress = ip.address();
server.listen(PORT, () => {
  console.log(`Server running on https://${ipAddress}:${PORT}`);
  console.log(`Also accessible on https://localhost:${PORT}`);
});

