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
from flask import Flask, render_template, request, jsonify
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

# 設定
# BOARD_APP_URL = "http://localhost:3000"
BOARD_APP_URL = "http://127.0.0.1:3000" # Pythonからのリクエスト用にIP指定に変更

# config.jsonから設定を読み込む
# ボードIDを共有することで、Webアプリ上の正しいボードに付箋を送信できるようにする
CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'config.json')
try:
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = json.load(f)
        ACTIVE_BOARD_ID = config.get('board_id', 'odgeqgf')
        print(f"Loaded board ID from config: {ACTIVE_BOARD_ID}")
except Exception as e:
    print(f"Failed to load config.json: {e}")
    ACTIVE_BOARD_ID = "odgeqgf"  # デフォルト値


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

@app.route('/')
def index():
    """AI-Boardのステータス表示用ページ"""
    return render_template('index.html')

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
        
        # フロントエンドに通知（音声再生用）
        socketio.emit('ai_comment', {
            'comment': comment,
            'audio_url': audio_url
        })
        
    socketio.start_background_task(generate_and_notify)
    
    # AI-Boardフロントエンドに付箋表示を通知
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

if __name__ == '__main__':
    print("Starting Flask Server...")
    # 全インターフェースでリッスン
    socketio.run(app, host='0.0.0.0', port=5000)
