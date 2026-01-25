from flask import Flask, render_template, jsonify
from flask_socketio import SocketIO, emit
import threading
import logging
import time
from datetime import datetime
from main_controller import run_reception_mode, run_live_mode

app = Flask(__name__)
app.config['SECRET_KEY'] = 'wonderlink-aivtuber-secret'
socketio = SocketIO(app, cors_allowed_origins="*")

# グローバル状態
app_state = {
    "mode": "stopped",  # stopped, reception, live
    "running": False,
    "start_time": None,
    "video_mode": "camera",
    "stop_event": None,
    "reception_thread": None
}

# ログハンドラーを追加してログをWebSocketで送信
class SocketIOLogHandler(logging.Handler):
    def emit(self, record):
        try:
            # FlaskとWerkzeugのHTTPリクエストログを除外
            if record.name in ('werkzeug', 'socketio.server', 'engineio.server'):
                return
            
            # HTTPリクエストログのメッセージパターンを除外
            message = record.getMessage()
            if ' - - [' in message and ('GET' in message or 'POST' in message):
                return
            
            log_entry = self.format(record)
            socketio.emit('log', {'message': log_entry, 'level': record.levelname})
        except:
            pass

# ログハンドラーを設定
socket_log_handler = SocketIOLogHandler()
socket_log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logging.getLogger().addHandler(socket_log_handler)

# FlaskとWerkzeugのログレベルをWARNINGに設定してアクセスログを抑制
logging.getLogger('werkzeug').setLevel(logging.WARNING)
logging.getLogger('socketio.server').setLevel(logging.WARNING)
logging.getLogger('engineio.server').setLevel(logging.WARNING)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/status')
def get_status():
    uptime = "00:00:00"
    if app_state["start_time"]:
        elapsed = int(time.time() - app_state["start_time"])
        hours = elapsed // 3600
        minutes = (elapsed % 3600) // 60
        seconds = elapsed % 60
        uptime = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return jsonify({
        "mode": app_state["mode"],
        "running": app_state["running"],
        "uptime": uptime,
        "video_mode": app_state["video_mode"]
    })

@socketio.on('connect')
def handle_connect():
    logging.info("Web UI client connected")
    emit('status', {
        'mode': app_state['mode'],
        'running': app_state['running']
    })

@socketio.on('start_reception')
def handle_start_reception():
    global app_state
    
    # Live Mode中の場合は、まずLive Modeを停止する
    if app_state["mode"] == "live":
        logging.info("Switching from Live Mode to Reception Mode...")
        if app_state["stop_event"]:
            app_state["stop_event"].set()
        time.sleep(1)  # Live Modeが停止するまで待つ
    
    if app_state["running"] and app_state["mode"] == "reception":
        emit('error', {'message': 'Reception Modeは既に実行中です'})
        return
    
    logging.info("Starting Reception Mode from Web UI...")
    app_state["running"] = True
    app_state["mode"] = "reception"
    app_state["start_time"] = time.time()
    app_state["stop_event"] = threading.Event()
    
    # Reception Modeを別スレッドで開始
    app_state["reception_thread"] = threading.Thread(
        target=run_reception_mode,
        args=(app_state["stop_event"],),
        daemon=True
    )
    app_state["reception_thread"].start()
    
    socketio.emit('status', {
        'mode': 'reception',
        'running': True
    })

@socketio.on('start_live')
def handle_start_live(data):
    global app_state
    
    if not app_state["running"]:
        emit('error', {'message': 'Reception Modeを先に開始してください'})
        return
    
    if app_state["mode"] == "live":
        emit('error', {'message': 'Live Modeは既に実行中です'})
        return
    
    video_mode = data.get('video_mode', 'camera')
    voice_name = data.get('voice_name', 'Zephyr')
    app_state["video_mode"] = video_mode
    
    logging.info(f"Switching to Live Mode ({video_mode}) from Web UI, Voice: {voice_name}...")
    
    # Reception Modeを停止
    if app_state["stop_event"]:
        app_state["stop_event"].set()
        time.sleep(1)  # スレッドが停止するまで待つ
    
    app_state["mode"] = "live"
    
    # Live Mode用の新しいstop_eventを作成
    app_state["stop_event"] = threading.Event()
    
    # Live Modeを別スレッドで開始
    live_thread = threading.Thread(
        target=run_live_mode,
        args=(video_mode, voice_name, app_state["stop_event"]),
        daemon=True
    )
    live_thread.start()
    
    socketio.emit('status', {
        'mode': 'live',
        'running': True
    })
    
    # Live Mode終了後、自動的にReception Modeに戻る
    def auto_return_to_reception():
        live_thread.join()
        if app_state["running"]:
            logging.info("Live Mode ended, returning to Reception Mode...")
            handle_start_reception()
    
    threading.Thread(target=auto_return_to_reception, daemon=True).start()

@socketio.on('stop')
def handle_stop():
    global app_state
    
    logging.info("Stopping application from Web UI...")
    
    if app_state["stop_event"]:
        app_state["stop_event"].set()
    
    app_state["running"] = False
    app_state["mode"] = "stopped"
    app_state["start_time"] = None
    
    socketio.emit('status', {
        'mode': 'stopped',
        'running': False
    })

if __name__ == '__main__':
    logging.info("Starting Web UI Server on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True)
