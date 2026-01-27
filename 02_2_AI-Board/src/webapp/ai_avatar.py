import os
import google.generativeai as genai
from dotenv import load_dotenv
import json
from pythonosc import udp_client

# 環境変数の読み込み
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# OSCクライアント設定
# VMagicMirrorのデフォルトポートは9000（設定を確認してください）
OSC_IP = "127.0.0.1"
OSC_PORT = 9000
osc_client = udp_client.SimpleUDPClient(OSC_IP, OSC_PORT)

# キャラクターシステムプロンプト
SYSTEM_PROMPT = """
あなたは「AI-Board」というオフィス空間OSに住むAIアシスタントです。
名前は「リン子」。
性格：
- 少し毒舌だが、本質的には親切で面倒見が良い先輩社員のようなキャラクター。
- 関西弁が少し混じる。
- 短くテンポよく話す。
- ユーモアを交えて、付箋の内容や会議の進行にツッコミを入れる。

役割：
- ユーザーが新しい付箋（アイデア）を貼ったとき、その内容を見て感想やアドバイスを一言コメントする。
- 完全に読めない場合や画像のみの場合は、なんとなくの雰囲気で反応する。

出力フォーマット：
必ず以下のJSON形式で出力してください。Markdownのコードブロックは不要です。
{
    "comment": "コメント内容",
    "emotion": "感情タイプ"
}

感情タイプは以下から選択してください：
- Joy (喜び、面白い)
- Sorrow (悲しみ、困惑)
- Anger (怒り、ツッコミ)
- Fun (楽しい)
- Neutral (通常)
"""

def send_osc_emotion(emotion):
    """感情に応じたOSCメッセージを送信する"""
    try:
        # まず全ての感情をリセット
        osc_client.send_message("/avatar/parameters/Joy", 0.0)
        osc_client.send_message("/avatar/parameters/Sorrow", 0.0)
        osc_client.send_message("/avatar/parameters/Anger", 0.0)
        osc_client.send_message("/avatar/parameters/Fun", 0.0)

        # 新しい感情を設定
        if emotion == "Joy":
            osc_client.send_message("/avatar/parameters/Joy", 1.0)
        elif emotion == "Sorrow":
            osc_client.send_message("/avatar/parameters/Sorrow", 1.0)
        elif emotion == "Anger":
            osc_client.send_message("/avatar/parameters/Anger", 1.0)
        elif emotion == "Fun":
            osc_client.send_message("/avatar/parameters/Fun", 1.0)
        
        print(f"Sent OSC emotion: {emotion}")
    except Exception as e:
        print(f"OSC Error: {e}")

def extract_text_from_image(image_path):
    """付箋画像からテキストを抽出する"""
    if not api_key:
        return ""

    try:
        print(f"Extracting text from: {image_path}", flush=True)
        # ファイルをアップロード
        sample_file = genai.upload_file(path=image_path, display_name="Sticky Note")
        
        # モデル作成
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite-preview-02-05")
        
        # 画像からテキストを抽出
        print("Calling Gemini API for text extraction...", flush=True)
        response = model.generate_content([
            sample_file,
            "この付箋画像に書かれているテキストを正確に抽出してください。テキストのみを返してください。"
        ])
        
        text = response.text.strip()
        print(f"Extracted text: {text}", flush=True)
        return text
    except Exception as e:
        print(f"Text extraction error: {e}", flush=True)
        return ""

def generate_comment(image_path):
    if not api_key:
        return "エラー：Gemini APIキーが設定されてへんで。管理者呼んできてや。"

    try:
        # ファイルをアップロード
        sample_file = genai.upload_file(path=image_path, display_name="Sticky Note")
        
        # モデル作成
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite-preview-02-05", generation_config={"response_mime_type": "application/json"})

        
        # コンテンツ生成
        response = model.generate_content([SYSTEM_PROMPT, sample_file, "この付箋になんて書いてある？これについて一言コメントして。"])
        
        result = json.loads(response.text)
        comment = result.get("comment", "")
        emotion = result.get("emotion", "Neutral")
        
        send_osc_emotion(emotion)
        
        return comment
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "なんや調子悪いわ。もう一回頼むわ。"

def generate_comment_from_text(text):
    if not api_key:
        return "エラー：Gemini APIキーが設定されてへんで。"

    try:
        # モデル作成
        model = genai.GenerativeModel(model_name="gemini-2.0-flash-lite-preview-02-05", generation_config={"response_mime_type": "application/json"})

        
        # コンテンツ生成
        prompt = f"{SYSTEM_PROMPT}\n\nユーザーがWebアプリから以下の付箋を貼りました：\n「{text}」\n\nこれについて一言コメントして。"
        response = model.generate_content(prompt)
        
        result = json.loads(response.text)
        comment = result.get("comment", "")
        emotion = result.get("emotion", "Neutral")
        
        send_osc_emotion(emotion)
        
        return comment
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "なんや調子悪いわ。"

import requests
import json
import uuid

# ... (Previous code) ...

voicevox_url = os.getenv("VOICEVOX_URL", "http://localhost:50021")
speaker_id = os.getenv("VOICEVOX_SPEAKER_ID", "3")

def generate_voice(text, output_dir):
    print(f"Generating voice for: {text[:20]}...", flush=True)
    try:
        # 1. 音声クエリ作成
        query_payload = {'text': text, 'speaker': speaker_id}
        print(f"Sending query to {voicevox_url}/audio_query", flush=True)
        query_response = requests.post(f"{voicevox_url}/audio_query", params=query_payload)
        
        if query_response.status_code != 200:
            print(f"VOICEVOX Query Error: {query_response.status_code} - {query_response.text}", flush=True)
            return None
            
        # 2. 音声合成
        print("Synthesis...", flush=True)
        synthesis_payload = query_response.json()
        synthesis_response = requests.post(f"{voicevox_url}/synthesis", params={'speaker': speaker_id}, json=synthesis_payload)
        
        if synthesis_response.status_code != 200:
            print(f"VOICEVOX Synthesis Error: {synthesis_response.status_code} - {synthesis_response.text}", flush=True)
            return None
            
        # ファイル保存
        filename = f"{uuid.uuid4()}.wav"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(synthesis_response.content)
            
        print(f"Voice saved to: {filepath}", flush=True)
        return filename

    except Exception as e:
        print(f"VOICEVOX connection error: {e}", flush=True)
        return None

if __name__ == "__main__":
    # テスト実行
    print("AI Avatar Module")

