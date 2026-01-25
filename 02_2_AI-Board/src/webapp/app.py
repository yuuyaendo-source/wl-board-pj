import os
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import eventlet
import ai_avatar
import requests
import time
import base64

# 設定
BOARD_APP_URL = "http://localhost:3000"
ACTIVE_BOARD_ID = "odgeqgf"  # 既存のボードIDを指定（または動的に変更可能に）

# Flaskアプリの初期化
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins="*")

# ディレクトリ設定
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'captures')
VOICE_FOLDER = os.path.join(os.path.dirname(__file__), 'static', 'voices')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VOICE_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/upload', methods=['POST'])
def upload_file():
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
            
            print(f"Emitting ai_comment with Audio URL: {audio_url}", flush=True)
            socketio.emit('ai_comment', {
                'comment': comment,
                'audio_url': audio_url
            })
            
        eventlet.spawn(generate_and_notify)
        
        return jsonify({'message': 'File uploaded successfully', 'filename': file.filename}), 200

# 付箋ごとの最終コメント時間を記録（レート制限用）
last_comment_time = {}

@app.route('/api/receive_note', methods=['POST'])
def receive_note():
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

        comment = ai_avatar.generate_comment_from_text(text)
        print(f"AI Comment (from text): {comment}")
        
        # 音声生成
        audio_filename = ai_avatar.generate_voice(comment, VOICE_FOLDER)
        audio_url = f"/static/voices/{audio_filename}" if audio_filename else None
        
        socketio.emit('ai_comment', {
            'comment': comment,
            'audio_url': audio_url
        })
        
    eventlet.spawn(generate_and_notify)
    
    # AI-Boardフロントエンドに付箋表示を通知
    socketio.emit('new_text_note', {
        'id': note_id,
        'text': text,
        'author': author
    })
    
    return jsonify({'message': 'Note received successfully'}), 200

if __name__ == '__main__':
    print("Starting Flask Server...")
    # 全インターフェースでリッスン
    socketio.run(app, host='0.0.0.0', port=5000)
