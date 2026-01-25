import boto3
import json
import os
import asyncio
import threading
import time
import certifi
import ssl
import logging
import datetime
import tempfile
from dotenv import load_dotenv
from pythonosc import udp_client
from google import genai
from google.genai import types
import edge_tts
import pygame

# .envファイルから環境変数を読み込む
load_dotenv()

# --- ロギングの設定 ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("aivtuber.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# --- Catoの証明書を信頼させるための設定 ---
cato_cert_path = r".\CatoNetworksTrustedRootCA.pem"
if os.path.exists(cato_cert_path):
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
    with open(cato_cert_path, 'rb') as cato_cert_file, open(certifi.where(), 'ab') as certifi_bundle:
        certifi_bundle.write(cato_cert_file.read())
    ssl._create_default_https_context = ssl.create_default_context(cafile=certifi.where())

# --- 各種APIキーとURLの設定 ---
SQS_QUEUE_URL = os.environ.get("SQS_QUEUE_URL")
if not SQS_QUEUE_URL:
    raise ValueError("SQS_QUEUE_URL environment variable is not set.")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable is not set.")

client = genai.Client(api_key=GEMINI_API_KEY)

AWS_REGION = "ap-northeast-1"
OSC_HOST = "127.0.0.1"
OSC_PORT = 39539

# Edge TTS設定
EDGE_TTS_VOICE = "ja-JP-NanamiNeural"  # 日本語女性ボイス

# --- boto3セッションの初期化 ---
if "AWS_PROFILE" not in os.environ:
    os.environ["AWS_PROFILE"] = "admin_sso"

session = boto3.Session()
sqs = session.client('sqs', region_name=AWS_REGION)

# --- OSCクライアントの初期化 ---
try:
    osc_client = udp_client.SimpleUDPClient(OSC_HOST, OSC_PORT)
    logging.info(f"OSC client connected to {OSC_HOST}:{OSC_PORT}")
except Exception as e:
    logging.error(f"Failed to connect to OSC server: {e}")
    osc_client = None

# --- Pygame初期化 ---
pygame.mixer.init()

# --- VMagicMirrorに表情を送信する関数 ---
def set_expression(expression_name, value=1.0):
    """VMagicMirrorに表情を送信 (/VMC/Ext/Blend 使用)"""
    if osc_client:
        try:
            osc_client.send_message("/VMC/Ext/Blend", [expression_name, float(value)])
            logging.info(f"Sent expression: {expression_name} = {value}")
        except Exception as e:
            logging.error(f"Error sending expression: {e}")
    else:
        logging.warning("OSC client is not connected. Skipping expression.")

def reset_expression():
    """表情をリセット"""
    if osc_client:
        for expr in ["Joy", "Fun", "Sorrow", "Anger"]:
            set_expression(expr, 0.0)

# --- Edge TTSで音声生成（非同期） ---
async def generate_audio_async(text, output_file):
    """Edge TTSで音声を生成してファイルに保存"""
    communicate = edge_tts.Communicate(text, EDGE_TTS_VOICE)
    await communicate.save(output_file)
    logging.info(f"Audio generated: {output_file}")

def generate_audio(text, output_file):
    """同期ラッパー"""
    asyncio.run(generate_audio_async(text, output_file))

# --- リップシンクを送信する関数（別スレッド用） ---
def lipsync_loop(stop_event):
    """音声再生中に口パクを送信する"""
    mouth_shapes = ["A", "I", "U", "E", "O"]
    idx = 0
    
    while not stop_event.is_set():
        if pygame.mixer.music.get_busy():
            # 音声再生中は口を動かす
            set_expression(mouth_shapes[idx % len(mouth_shapes)], 0.5)
            idx += 1
            time.sleep(0.1)
        else:
            # 再生が終わったら口を閉じる
            set_expression("A", 0.0)
            break
    
    # 終了時に口を閉じる
    set_expression("A", 0.0)
    logging.info("Lipsync stopped")

# --- 音声を再生し、VMagicMirrorと連携する関数 ---
def synthesize_and_play(text):
    """Edge TTSで音声を生成・再生し、リップシンクを行う"""
    try:
        # 一時ファイルに音声を保存
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
            tmp_filename = tmp_file.name
        
        # 音声生成
        generate_audio(text, tmp_filename)
        
        # 音声を再生
        pygame.mixer.music.load(tmp_filename)
        pygame.mixer.music.play()
        
        # リップシンクを別スレッドで開始
        stop_event = threading.Event()
        lipsync_thread = threading.Thread(target=lipsync_loop, args=(stop_event,))
        lipsync_thread.start()
        
        # 再生が終わるまで待機
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        
        # リップシンクスレッドを停止
        stop_event.set()
        lipsync_thread.join()
        
        # 一時ファイルを削除
        try:
            os.unlink(tmp_filename)
        except:
            pass
        
    except Exception as e:
        logging.error(f"Error in synthesize_and_play: {e}")

# --- 自己紹介関数 ---
def introduce_self():
    """ワンダーリン子の自己紹介"""
    introduction = ("はじめまして！WonderLink株式会社のAIvtuber、ワンダーリン子です。"
                   "受付を担当しています。何かお困りのことがあれば、私の名前を呼んでくださいね！")
    logging.info("Playing self-introduction")
    
    # Joy表情
    set_expression("Joy", 1.0)
    
    # 自己紹介を再生
    synthesize_and_play(introduction)
    
    # 表情をリセット
    reset_expression()

# --- AIに挨拶文を生成させる関数 ---
def get_ai_greeting(person_label=None):
    """Gemini APIを使って挨拶を生成"""
    current_hour = datetime.datetime.now().hour
    
    time_greeting = "こんにちは"
    if 5 <= current_hour < 11:
        time_greeting = "おはようございます"
    elif 11 <= current_hour < 18:
        time_greeting = "こんにちは"
    else:
        time_greeting = "こんばんは"

    if person_label:
        prompt = f"""あなたはオフィスの受付AIキャラクターです。
社員である「{person_label}」さんがオフィスのエントランスを通りました。
現在の時間は{current_hour}時です。「{time_greeting}」を含めた、自然で親しみやすい挨拶をしてください。
毎回同じセリフにならないように、労いの言葉や、天気、季節感、あるいはちょっとした冗談などをランダムに交えてください。
長さは20文字〜40文字程度で短くまとめてください。

重要: 挨拶のセリフのみを出力してください。「承知しました」「はい」などの余計な返事は不要です。"""
    else:
        prompt = f"""あなたはオフィスの受付AIキャラクターです。
お客様（名前不明）が来られました。
現在の時間は{current_hour}時です。「{time_greeting}」を含めた、丁寧かつ温かい挨拶をしてください。
「いらっしゃいませ」に加えて、居心地の良さを感じさせる一言を添えてください。
長さは20文字〜40文字程度で短くまとめてください。

重要: 挨拶のセリフのみを出力してください。「承知しました」「はい」などの余計な返事は不要です。"""
    
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=prompt,
            config=types.GenerateContentConfig(
                max_output_tokens=50,
                temperature=0.9
            )
        )
        greeting = response.text.strip()
        # 念のため、不要なフレーズを削除
        greeting = greeting.replace("承知いたしました。", "").replace("はい、", "").strip()
        greeting = greeting.strip('"「」')  # 引用符も削除
        logging.info(f"Generated greeting: {greeting}")
        return greeting
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        return f"{time_greeting}、いらっしゃいませ。"

# --- SQSメッセージを処理するメイン関数 ---
def poll_sqs_queue(stop_event=None):
    """SQSキューをポーリングしてメッセージを処理"""
    logging.info("Polling SQS queue for messages...")
    try:
        while True:
            if stop_event and stop_event.is_set():
                logging.info("Stopping SQS polling...")
                break

            response = sqs.receive_message(
                QueueUrl=SQS_QUEUE_URL,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=5
            )

            messages = response.get('Messages', [])
            if not messages:
                continue

            for message in messages:
                if stop_event and stop_event.is_set():
                    break
                    
                message_body_string = message['Body']
                
                try:
                    sqs_message_data = json.loads(message_body_string)
                    if 'body' in sqs_message_data:
                        webhook_data = json.loads(sqs_message_data['body'])
                    else:
                        webhook_data = sqs_message_data
                except json.JSONDecodeError:
                    logging.error("Received malformed JSON, skipping message.")
                    sqs.delete_message(QueueUrl=SQS_QUEUE_URL, ReceiptHandle=message['ReceiptHandle'])
                    continue

                person_label = webhook_data.get('data', {}).get('person_label')
                
                # AIに挨拶文を生成させる
                greeting_text = get_ai_greeting(person_label)
                
                # 挨拶に合わせて表情を変える
                set_expression("Joy", 1.0)

                # 音声を再生（リップシンクも自動実行）
                synthesize_and_play(greeting_text)
                
                # 表情を戻す
                reset_expression()

                # メッセージをキューから削除
                sqs.delete_message(
                    QueueUrl=SQS_QUEUE_URL,
                    ReceiptHandle=message['ReceiptHandle']
                )

    except Exception as e:
        logging.error(f"An error occurred: {e}")

if __name__ == '__main__':
    poll_sqs_queue()