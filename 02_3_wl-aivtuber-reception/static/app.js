// Socket.IO接続
const socket = io();

// DOM要素
const currentModeEl = document.getElementById('current-mode');
const uptimeEl = document.getElementById('uptime');
const logContainerEl = document.getElementById('log-container');
const btnReception = document.getElementById('btn-reception');
const btnLive = document.getElementById('btn-live');
const btnStop = document.getElementById('btn-stop');
const btnClearLog = document.getElementById('btn-clear-log');
const autoScrollCheckbox = document.getElementById('auto-scroll');
const videoModeSelect = document.getElementById('video-mode');

// アプリケーション状態
let currentMode = 'stopped';
let isRunning = false;

// 接続イベント
socket.on('connect', () => {
    console.log('Connected to server');
    addLog('Web UIに接続しました', 'INFO');
});

// ステータス更新
socket.on('status', (data) => {
    currentMode = data.mode;
    isRunning = data.running;
    updateUI();
});

// ログ受信
socket.on('log', (data) => {
    addLog(data.message, data.level || 'INFO');
});

// エラー表示
socket.on('error', (data) => {
    addLog(`エラー: ${data.message}`, 'ERROR');
    alert(data.message);
});

// UI更新
function updateUI() {
    // モード表示を更新
    currentModeEl.className = 'status-value';

    const indicator = currentModeEl.querySelector('.status-indicator');

    if (currentMode === 'stopped') {
        currentModeEl.innerHTML = '<span class="status-indicator"></span>OFFLINE';
        currentModeEl.classList.add('status-stopped');
        btnReception.disabled = false;
        btnLive.disabled = true;
        btnStop.disabled = true;
    } else if (currentMode === 'reception') {
        currentModeEl.innerHTML = '<span class="status-indicator"></span>RECEPTION';
        currentModeEl.classList.add('status-reception');
        btnReception.disabled = true;
        btnLive.disabled = false;
        btnStop.disabled = false;
    } else if (currentMode === 'live') {
        currentModeEl.innerHTML = '<span class="status-indicator"></span>LIVE';
        currentModeEl.classList.add('status-live');
        btnReception.disabled = false; // Live Mode中でもReception Modeに戻れるようにする
        btnLive.disabled = true;
        btnStop.disabled = false;
    }
}

// ログ追加
function addLog(message, level = 'INFO') {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';

    if (level === 'WARNING') {
        logEntry.classList.add('log-warning');
    } else if (level === 'ERROR') {
        logEntry.classList.add('log-error');
    } else {
        logEntry.classList.add('log-info');
    }

    logEntry.textContent = message;
    logContainerEl.appendChild(logEntry);

    // 自動スクロール
    if (autoScrollCheckbox.checked) {
        logContainerEl.scrollTop = logContainerEl.scrollHeight;
    }

    // ログが多くなりすぎたら古いものを削除
    if (logContainerEl.children.length > 500) {
        logContainerEl.removeChild(logContainerEl.firstChild);
    }
}

// ボタンイベント
btnReception.addEventListener('click', () => {
    console.log('Starting Reception Mode');
    socket.emit('start_reception');
    addLog('Reception Mode 開始要求を送信しました', 'INFO');
});

btnLive.addEventListener('click', () => {
    const videoMode = videoModeSelect.value;
    const voiceName = document.getElementById('voice-select').value;
    console.log(`Starting Live Mode (${videoMode}, Voice: ${voiceName})`);
    socket.emit('start_live', { video_mode: videoMode, voice_name: voiceName });
    addLog(`Live Mode (${videoMode}, Voice: ${voiceName}) 開始要求を送信しました`, 'INFO');
});

btnStop.addEventListener('click', () => {
    if (confirm('アプリケーションを停止してもよろしいですか？')) {
        console.log('Stopping application');
        socket.emit('stop');
        addLog('停止要求を送信しました', 'INFO');
    }
});

btnClearLog.addEventListener('click', () => {
    logContainerEl.innerHTML = '';
    addLog('ログをクリアしました', 'INFO');
});

// 定期的にステータスを更新
setInterval(() => {
    fetch('/api/status')
        .then(response => response.json())
        .then(data => {
            currentMode = data.mode;
            isRunning = data.running;
            uptimeEl.textContent = data.uptime;
            updateUI();
        })
        .catch(error => {
            console.error('Error fetching status:', error);
        });
}, 1000);

// 初期UI更新
updateUI();
