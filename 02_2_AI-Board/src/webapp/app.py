"""
AI-Board Backend Server
-----------------------
Flaskベースのバックエンドサーバーです。
主な役割:
1. Webカメラやスマホから送信された付箋画像を受け取る (REST API)
2. 画像からテキストを抽出する (Gemini API via ai_avatar.py)
3. 付箋の内容に応じたコメントと音声を生成する (Gemini API, VOICEVOX)
4. 生成された音声とコメントをSocket.IOでフロントエンドに通知する
5. VMagicMirrorへのOSC制御を行う (ai_avatar.py経由)
"""

# import eventlet
# eventlet.monkey_patch()

import os
import json

# .env をプロジェクトルート (02_2_AI-Board) から読み込む（ai_avatar より前に実行）
from dotenv import load_dotenv
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(_env_path)

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO
import ai_avatar
import requests
import time
import base64
import sys
import threading
import cv2
import numpy as np

# 再帰的なインポートエラーを防ぐためのパス設定
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
# 親ディレクトリをパスに追加して sticky_note_detector をインポート可能にする
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from sticky_note_detector import StickyNoteDetector
import face_registry_storage as face_registry

# 設定: 付箋ボード連携先。本番: POSTIT_BOARD_URL=http://wl-sticky-note.local
BOARD_APP_URL = os.environ.get("POSTIT_BOARD_URL", "http://127.0.0.1:3000").strip().rstrip("/")

# config.jsonから設定を読み込む（board_id: 本番は wl → http://wl-sticky-note.local/board/wl）
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
        ACTIVE_BOARD_ID = config.get('board_id', 'wl')
        print(f"Loaded board ID from config: {ACTIVE_BOARD_ID}")
except Exception as e:
    print(f"Failed to load config.json: {e}")
    ACTIVE_BOARD_ID = "wl"  # デフォルト（本番連携先）

print(f"Postit board: {BOARD_APP_URL} (board_id={ACTIVE_BOARD_ID})", flush=True)

# Flaskアプリの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
# async_mode='threading' を指定して Eventlet を回避 (Windows環境での互換性のため)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# ディレクトリ設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'captures')
VOICE_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'voices')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VOICE_FOLDER, exist_ok=True)

# 自動パーソナル切替用: /camera_stream の映像ソース（.env の RTSP_URL、未設定なら Webカメラ 0）
CAMERA_SOURCE_FOR_DETECTION = os.environ.get('RTSP_URL', '').strip() or 0


def _generate_mjpeg():
    """ネットワークカメラ（RTSP）または Webカメラの MJPEG ストリームを生成"""
    cap = None
    try:
        cap = cv2.VideoCapture(CAMERA_SOURCE_FOR_DETECTION)
        if not cap.isOpened():
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + b'' + b'\r\n')
            return
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            _, jpeg = cv2.imencode('.jpg', frame)
            yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
    finally:
        if cap is not None:
            cap.release()


@app.route('/camera_stream')
def camera_stream():
    """
    自動パーソナル切替（エントランス用）: ネットワークカメラの MJPEG ストリーム。
    .env の RTSP_URL が設定されていれば RTSP、未設定なら Webカメラ (0)。
    ブラウザの img で表示し、顔検知の入力に利用する。
    """
    return Response(
        _generate_mjpeg(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={'Cache-Control': 'no-store'},
    )


@app.route('/')
def index():
    """AI-Boardのステータス表示用ページ"""
    return render_template('index.html')


@app.route('/personal')
def personal():
    """個人用パーソナルモード（デスクトップアプリから user 指定でアクセス）。モード切替UIは非表示でパーソナルのみ表示。"""
    user_id = request.args.get('user', '').strip()
    return render_template('index.html', personal_only=True, user_id=user_id)


@app.route('/asakawa')
def asakawa():
    """デモ用: 浅川さんのパーソナルモード（顔検出・任意切替・デスクトップアプリで同じページに統一）。"""
    return render_template('index.html', personal_only=True, user_id='asakawa')


@app.route('/manager')
def manager():
    """名前・顔の管理画面（特定の人物が利用）"""
    return render_template('manager.html')


# --- アバター・視点のモード別設定（サーバーに保存して再起動後も維持） ---
AVATAR_MODE_SETTINGS_FILE = os.path.join(os.path.dirname(__file__), 'data', 'avatar_mode_settings.json')
_avatar_settings_lock = threading.Lock()


def _ensure_avatar_data_dir():
    d = os.path.dirname(AVATAR_MODE_SETTINGS_FILE)
    os.makedirs(d, exist_ok=True)


@app.route('/api/avatar_mode_settings', methods=['GET'])
def api_avatar_mode_settings_get():
    """アバター・視点のモード別設定を取得（サーバーに保存されたファイルから）"""
    try:
        with _avatar_settings_lock:
            if not os.path.exists(AVATAR_MODE_SETTINGS_FILE):
                return jsonify({'error': 'Not found'}), 404
            with open(AVATAR_MODE_SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/avatar_mode_settings', methods=['PUT'])
def api_avatar_mode_settings_put():
    """アバター・視点のモード別設定を保存（サーバーにファイルで保存）"""
    try:
        data = request.get_json()
        if data is None:
            return jsonify({'error': 'JSON body required'}), 400
        _ensure_avatar_data_dir()
        with _avatar_settings_lock:
            with open(AVATAR_MODE_SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 顔・名前登録 API（将来 S3 等に差し替え可能なストレージ抽象の上で動作） ---

@app.route('/api/face_registry', methods=['GET'])
def api_face_registry_list():
    """登録者一覧（id, name のみ）"""
    try:
        persons = face_registry.list_persons()
        return jsonify({'persons': persons})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/face_registry/<person_id>', methods=['GET'])
def api_face_registry_get(person_id):
    """1件取得（照合用に faceData を含む）"""
    try:
        person = face_registry.get_person(person_id, include_face=True)
        if person is None:
            return jsonify({'error': 'Not found'}), 404
        return jsonify(person)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/face_registry', methods=['POST'])
def api_face_registry_create():
    """名前のみで新規登録（管理者用）"""
    try:
        body = request.get_json() or {}
        name = (body.get('name') or '').strip()
        if not name:
            return jsonify({'error': 'name is required'}), 400
        person = face_registry.create_person(name)
        return jsonify(person), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/face_registry/<person_id>', methods=['PUT'])
def api_face_registry_update_face(person_id):
    """指定 id の顔データを登録・更新（管理者用）"""
    try:
        body = request.get_json() or {}
        face_data = body.get('faceData')
        if face_data is None:
            return jsonify({'error': 'faceData is required'}), 400
        ok = face_registry.update_face(person_id, face_data)
        if not ok:
            return jsonify({'error': 'Not found'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/face_registry/<person_id>', methods=['DELETE'])
def api_face_registry_delete(person_id):
    """指定 id を削除（管理者用）"""
    try:
        ok = face_registry.delete_person(person_id)
        if not ok:
            return jsonify({'error': 'Not found'}), 404
        return jsonify({'ok': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    [レガシー] カメラからの画像アップロード用エンドポイント
    現在は sticky_note_detector.py が直接Webアプリへ送信するため、主にデバッグ用
    """
    # ファイルアップロード処理
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    x = request.form.get('x', 0)
    y = request.form.get('y', 0)
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(filepath)
        
        # AI-Boardクライアントに通知（画像表示用）
        print(f"Emitting new_note to clients: filename={file.filename}", flush=True)
        socketio.emit('new_note', {
            'filename': file.filename,
            'x': x,
            'y': y
        })
        
        # テキスト抽出
        text = ai_avatar.extract_text_from_image(filepath)
        if not text:
            text = "(テキスト抽出できませんでした)"
        
        # 画像をBase64エンコード
        with open(filepath, 'rb') as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{img_base64}"
        
        # WebアプリのREST APIに送信
        note_id = f"phy-{int(time.time() * 1000)}"
        note_data = {
            "boardId": ACTIVE_BOARD_ID,
            "note": {
                "id": note_id,
                "text": text,
                "x": float(x),
                "y": float(y),
                "color": "#ffeb3b",  # 黄色固定
                "pinned": False,
                "author": "Real Cam",
                "createdAt": int(time.time() * 1000),
                "imageUrl": image_url
            }
        }
        
        try:
            response = requests.post(
                f"{BOARD_APP_URL}/api/sticky_notes",
                json=note_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if response.status_code == 200:
                print(f"Note sent to Web App via API: {note_id}")
            else:
                print(f"API Error: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"Error sending to Web App: {e}")
        
        # 非同期でAIコメント生成
        def generate_and_notify():
            comment = ai_avatar.generate_comment(filepath)
            print(f"AI Comment: {comment}")
            
            # 音声生成
            print("Calling generate_voice...", flush=True)
            audio_filename = ai_avatar.generate_voice(comment, VOICE_FOLDER)
            print(f"Audio Filename: {audio_filename}", flush=True)
            audio_url = f"/static/voices/{audio_filename}" if audio_filename else None
            
            print(f"Emitting ai_comment to clients (upload flow), audio_url={audio_url}", flush=True)
            socketio.emit('ai_comment', {
                'comment': comment,
                'audio_url': audio_url
            })
            
        socketio.start_background_task(generate_and_notify)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200

# 付箋ごとの最終コメント時間を記録（レート制限用）
last_comment_time = {}

# AI-Board 内部で保持しているモバイル付箋などの状態（必要に応じて拡張）
mobile_notes_data = {}

@app.route('/api/receive_note', methods=['POST'])
def receive_note():
    """
    Webアプリで付箋が追加/更新されたときに呼び出されるWebhook
    テキスト内容に基づいてAIがコメントと音声を生成する
    """
    # Webアプリからの付箋データ受信処理
    data = request.json
    note_id = data.get('id', '')
    text = data.get('text', '')
    author = data.get('author', 'Unknown')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
        
    print(f"Received note from Web App: {text} (by {author})")
    
    # 非同期でAIコメント生成
    def generate_and_notify():
        # レート制限: 同じ付箋に対して短時間（例：10秒）に連続してコメントしない
        current_time = time.time()
        if note_id in last_comment_time and current_time - last_comment_time[note_id] < 10:
            print(f"Skipping comment for note {note_id} (rate limited)")
            return

        last_comment_time[note_id] = current_time

        # Gemini APIでテキストに対するコメント生成
        comment = ai_avatar.generate_comment_from_text(text)
        print(f"AI Comment (from text): {comment}")
        
        # 音声生成 (VOICEVOX)
        audio_filename = ai_avatar.generate_voice(comment, VOICE_FOLDER)
        audio_url = f"/static/voices/{audio_filename}" if audio_filename else None
        
        # フロントエンドに通知（音声再生用・リン子の反応）
        print(f"Emitting ai_comment to clients (comment len={len(comment)})", flush=True)
        socketio.emit('ai_comment', {
            'comment': comment,
            'audio_url': audio_url
        })
        
    socketio.start_background_task(generate_and_notify)
    
    # AI-Boardフロントエンドに付箋表示を通知（付箋ボード連携・カメラ経由の付箋）
    print(f"Emitting new_text_note to clients: id={note_id}, text={(text or '')[:50]}...", flush=True)
    socketio.emit('new_text_note', {
        'id': note_id,
        'text': text,
        'author': author
    })
    
    return jsonify({'message': 'Note received successfully'}), 200

@app.route('/api/upload_image', methods=['POST'])
def upload_image_mobile():
    """
    スマホからの画像アップロードを受け付け、付箋を切り出して処理するエンドポイント
    1. 画像を受け取る
    2. StickyNoteDetectorで付箋領域を検出・切り出し
    3. 画像全体または切り出した付箋を保存
    4. テキスト抽出
    5. Webアプリへ送信
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filepath = os.path.join(UPLOAD_FOLDER, f"mobile_{file.filename}")
        file.save(filepath)
        print(f"Mobile upload received: {filepath}")

        # 画像読み込み
        img = cv2.imread(filepath)
        if img is None:
            return jsonify({'error': 'Failed to load image'}), 400

        # 付箋検知ロジックの呼び出し
        detector = StickyNoteDetector()
        detected_notes = detector.detect_from_image(img)
        
        print(f"Detected {len(detected_notes)} notes from mobile upload.")
        
        if len(detected_notes) == 0:
            # 付箋が見つからなかった場合、画像全体を1つの付箋として扱う
            print("No sticky notes detected. Treating the whole image as a note.")
            detected_notes.append({
                'image': img,
                'x': 0, 'y': 0, 'w': img.shape[1], 'h': img.shape[0]
            })

        processed_count = 0
        
        for i, note in enumerate(detected_notes):
            # 切り出し画像を保存
            crop_img = note['image']
            timestamp = int(time.time() * 1000)
            note_id = f"mobile-{timestamp}-{i}"
            crop_filename = f"{note_id}.jpg"
            crop_filepath = os.path.join(UPLOAD_FOLDER, crop_filename)
            cv2.imwrite(crop_filepath, crop_img)
            
            # テキスト抽出
            text = ai_avatar.extract_text_from_image(crop_filepath)
            if not text:
                text = "(テキスト抽出できませんでした)"
            
            # 画像Base64
            with open(crop_filepath, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{img_base64}"
            
            # Webアプリへ送信データ作成
            note_data = {
                "boardId": ACTIVE_BOARD_ID,
                "note": {
                    "id": note_id,
                    "text": text,
                    "x": (note['x'] / img.shape[1]) * 4000, # 画像内の相対位置をキャンバス座標に変換
                    "y": (note['y'] / img.shape[0]) * 4000,
                    "color": "#ffeb3b",
                    "pinned": False,
                    "author": "Mobile User",
                    "createdAt": timestamp,
                    "imageUrl": image_url,
                    # タスクB: 付箋サイズの自動最適化用のパラメータ
                    "ratioW": note['w'] / img.shape[1] if 'w' in note else 0.25 
                }
            }
            
            try:
                # Flaskからのリクエスト送信時のエラー詳細を出力するように強化
                print(f"Sending note to Web App: {BOARD_APP_URL}/api/sticky_notes")
                print(f"Payload (BOARD_ID={ACTIVE_BOARD_ID}): {json.dumps(note_data, ensure_ascii=False)}")
                response = requests.post(
                    f"{BOARD_APP_URL}/api/sticky_notes",
                    json=note_data,
                    headers={'Content-Type': 'application/json'},
                    timeout=5
                )
                
                if response.status_code == 200:
                    print(f"Successfully sent note {note_id} to Web App.")
                    processed_count += 1
                else:
                    print(f"Failed to send note {note_id}. Status: {response.status_code}, Response: {response.text}")
                    
            except Exception as e:
                print(f"Error sending note {note_id}: {e}")


            # AI-Board (自分自身) にも画像を表示するためにSocket.IOイベントを発火
            # crop_filename は切り出された画像なので、それを表示させる
            socketio.emit('new_mobile_note', {
                'filename': crop_filename,
                'x': note['x'],
                'y': note['y']
            })

            # 最初の1枚だけAIコメント生成（全部やるとうるさいので）
            if i == 0:
                def generate_and_notify_mobile():
                    comment = ai_avatar.generate_comment(crop_filepath)
                    audio_filename = ai_avatar.generate_voice(comment, VOICE_FOLDER)
                    audio_url = f"/static/voices/{audio_filename}" if audio_filename else None
                    socketio.emit('ai_comment', {'comment': comment, 'audio_url': audio_url})
                socketio.start_background_task(generate_and_notify_mobile)

        return jsonify({'message': f'Processed {processed_count} notes', 'count': processed_count}), 200


@app.route('/api/clear_board', methods=['POST'])
def clear_board():
    """
    Webアプリ(Postit_board)からのリクエストで、
    AI-Board 側の表示中付箋やコメント履歴をクリアするエンドポイント。
    - 内部状態（mobile_notes_data, last_comment_time）をリセット
    - フロントエンドに clear_all_notes イベントを送出して画面を初期化
    """
    global mobile_notes_data, last_comment_time

    try:
        board_id = request.json.get('boardId') if request.is_json else None
    except Exception:
        board_id = None

    print(f"Received clear request from Web App. boardId={board_id}", flush=True)

    mobile_notes_data = {}
    last_comment_time = {}

    # フロントエンドに全削除を通知
    socketio.emit('clear_all_notes')

    return jsonify({'message': 'AI-Board cleared successfully', 'boardId': board_id}), 200


# ============================================================
# Remote Reception Mode (WebRTC & Tracking)
# ============================================================

@app.route('/operator')
def operator():
    """受付オペレーター用ページ"""
    return render_template('operator.html')


@socketio.on('webrtc-signal')
def handle_webrtc_signal(data):
    """
    WebRTCシグナリング中継
    オペレーターとディスプレイ間のWebRTC接続を仲介
    """
    print(f"WebRTC signal from {data.get('from')}", flush=True)
    # 送信元以外の全クライアントにブロードキャスト（skip_sid は python-socketio の API）
    socketio.emit('webrtc-signal', data, skip_sid=request.sid)


# トラッキング受信ログ用（10秒に1回＋初回のみ face のキーを出力）
_tracking_log_last = 0
_tracking_face_logged = False

@socketio.on('tracking_data')
def handle_tracking_data(data):
    """
    トラッキングデータ配信
    オペレーターからのトラッキングデータをディスプレイにブロードキャスト
    """
    global _tracking_log_last, _tracking_face_logged
    import time
    now = time.time()
    if now - _tracking_log_last > 10.0:
        _tracking_log_last = now
        has_pose = bool(data and data.get('pose'))
        has_face = bool(data and data.get('face'))
        print(f"[tracking_data] received from operator, relaying (pose={has_pose}, face={has_face})", flush=True)
    # 初回のみ: face のキーを出力（ディスプレイで表情が動かないときの切り分け用）
    if data and data.get('face') and not _tracking_face_logged:
        _tracking_face_logged = True
        face = data.get('face')
        keys = list(face.keys()) if isinstance(face, dict) else []
        eye_keys = list(face.get('eye', {}).keys()) if isinstance(face.get('eye'), dict) else []
        mouth_keys = list(face.get('mouth', {}).keys()) if isinstance(face.get('mouth'), dict) else []
        print(f"[tracking_data] face keys: {keys}, eye: {eye_keys}, mouth: {mouth_keys}", flush=True)
    # 送信元を除く全クライアントに配信（skip_sid は python-socketio の API）
    socketio.emit('tracking_data', data, skip_sid=request.sid)






def _get_local_ips():
    """このPCのローカルIPアドレス一覧を取得（遠隔アクセス用URL表示用）"""
    import socket
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addr = info[4][0]
            if addr != "127.0.0.1" and addr not in ips:
                ips.append(addr)
    except Exception:
        pass
    return ips if ips else ["(取得できません)"]


if __name__ == '__main__':
    print("Starting Flask Server...")
    local_ips = _get_local_ips()
    
    # Check for SSL certificate files
    cert_file = os.path.join(os.path.dirname(__file__), 'cert.pem')
    key_file = os.path.join(os.path.dirname(__file__), 'key.pem')
    
    if os.path.exists(cert_file) and os.path.exists(key_file):
        print("✅ SSL certificates found. Starting HTTPS server...")
        print(f"   Local:  https://localhost:5000  or  https://127.0.0.1:5000")
        for ip in local_ips:
            if ip != "(取得できません)":
                print(f"   Remote: https://{ip}:5000  (受付オペレーター: https://{ip}:5000/operator)")
        print("   ⚠️  Self-signed cert: Browser → 'Advanced' → 'Proceed to ... (unsafe)'")
        print("")
        print("   📌 遠隔PCから接続できない場合: Windowsファイアウォールでポート5000を許可してください。")
        print("      例: プロジェクトルートで .\\scripts\\allow_firewall_port_5000.ps1 を管理者PowerShellで実行")
        
        socketio.run(app, 
                    host='0.0.0.0', 
                    port=5000,
                    ssl_context=(cert_file, key_file))
    else:
        print("⚠️  SSL certificates not found. Starting HTTP server...")
        print(f"   Local:  http://localhost:5000  or  http://127.0.0.1:5000")
        for ip in local_ips:
            if ip != "(取得できません)":
                print(f"   Remote: http://{ip}:5000  (受付オペレーター: http://{ip}:5000/operator)")
        print("   遠隔アクセス用HTTPS: python src/webapp/generate_cert.py を実行後、再起動")
        print("")
        print("   📌 遠隔PCから接続できない場合: Windowsファイアウォールでポート5000を許可してください。")
        print("      例: プロジェクトルートで .\\scripts\\allow_firewall_port_5000.ps1 を管理者PowerShellで実行")
        socketio.run(app, host='0.0.0.0', port=5000)



