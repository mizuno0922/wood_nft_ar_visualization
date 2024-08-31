const socket = io();
const video = document.getElementById('camera-feed');
const arOverlay = document.getElementById('ar-overlay');
const infoDisplay = document.getElementById('info-display');
const objectName = document.getElementById('object-name');
const objectDescription = document.getElementById('object-description');
const objectID = document.getElementById('object-id');
const objectParentID = document.getElementById('object-parent-id');
const objectProductor = document.getElementById('object-productor');
const objectDate = document.getElementById('object-date');
const objectSite = document.getElementById('object-site');
const matchInfo = document.getElementById('match-info');
const confidenceInfo = document.getElementById('confidence-info');
const matchRateInfo = document.getElementById('match-rate-info');

navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } })
    .then(stream => {
        video.srcObject = stream;
        video.play();
    })
    .catch(err => console.error('Error accessing camera:', err));

function captureFrame() {
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    return canvas.toDataURL('image/jpeg');
}

setInterval(() => {
    const frame = captureFrame();
    socket.emit('detect_object', frame);
}, 1000);

socket.on('detection_result', (result) => {
    console.log('Received detection result:', result); // デバッグ用ログ
    if (result.detected) {
        objectName.textContent = `検出されたモデル: ${result.model_name}`;
        matchInfo.textContent = `マッチ品質: ${result.match_quality}`;
        confidenceInfo.textContent = `信頼度: ${result.confidence}`;
        matchRateInfo.textContent = `マッチ率: ${result.num_matches}/${result.DETECTION_THRESHOLD}`;

        if (result.metadata) {
            objectName.textContent = `名前: ${result.metadata.name}`;
            objectDescription.textContent = `説明: ${result.metadata.description}`;
            objectID.textContent = `ID: ${result.metadata.ID}`;
            objectParentID.textContent = `parentID: ${result.metadata.parentID}`;
            objectProductor.textContent = `productor: ${result.metadata.productor}`;
            objectDate.textContent = `date: ${result.metadata.date}`;
            objectSite.textContent = `site: ${result.metadata.site}`;
        } else {
            objectDescription.textContent = '';
            objectID.textContent = '';
            objectParentID.textContent = '';
            objectProductor.textContent = '';
            objectDate.textContent = '';
            objectSite.textContent = '';
        }

        infoDisplay.style.display = 'block';
    } else {
        infoDisplay.style.display = 'none';
    }
});