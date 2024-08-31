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

function updateDisplay(result) {
    console.log('Updating display with result:', result);
    if (result.detected) {
        objectName.textContent = `検出されたモデル: ${result.model_name}`;
        matchInfo.textContent = `マッチ品質: ${result.match_quality}`;
        confidenceInfo.textContent = `信頼度: ${result.confidence}`;
        matchRateInfo.textContent = `マッチ率: ${result.num_matches}/${result.DETECTION_THRESHOLD}`;

        if (result.metadata) {
            objectName.textContent = `名前: ${result.metadata.name}`;
            objectDescription.textContent = `説明: ${result.metadata.description}`;
            objectID.textContent = `ID: ${result.metadata.ID}`;
            
            // 親IDの処理
            const parentIDs = result.metadata.parentID ? result.metadata.parentID.split(',') : [];
            const parentLinks = parentIDs.map(id => 
                `<a href="#" onclick="getParentInfo('${id.trim()}'); return false;">${id.trim()}</a>`
            ).join(', ');
            objectParentID.innerHTML = `親ID: ${parentLinks}`;
            
            objectProductor.textContent = `製作者: ${result.metadata.productor}`;
            objectDate.textContent = `日付: ${result.metadata.date}`;
            objectSite.textContent = `サイト: ${result.metadata.site}`;
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
}

function getParentInfo(parentID) {
    console.log('Getting parent info for:', parentID);
    socket.emit('get_parent_info', parentID);
}

socket.on('detection_result', (result) => {
    console.log('Received detection result:', result);
    updateDisplay(result);
});

socket.on('parent_info', (result) => {
    console.log('Received parent info:', result);
    if (result.error) {
        console.error('Error getting parent info:', result.error);
    } else {
        updateDisplay(result);
    }
});

// グローバルスコープにgetParentInfo関数を追加
window.getParentInfo = getParentInfo;