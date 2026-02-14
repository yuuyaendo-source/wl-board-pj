import os
import json
from dotenv import load_dotenv
from pythonosc import udp_client

# .env のパス（プロジェクトルート 02_2_AI-Board）
_env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))

# 新しい google-genai を優先、失敗時は古い google-generativeai にフォールバック
_use_new_sdk = False
_genai_module = None  # genai (new SDK)
_genai_legacy = None
_types = None

try:
    from google import genai as _genai_module
    from google.genai import types as _types_new
    _use_new_sdk = True
    _types = _types_new
except ImportError:
    try:
        import google.generativeai as _genai_legacy
        _types = None
    except ImportError:
        pass


def _ensure_env():
    """実行時に .env を読み込む（起動時の cwd に依存しない）"""
    load_dotenv(_env_path)


def _get_api_key():
    """実行時に API キーを取得する"""
    _ensure_env()
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


_client_lazy = None


def _get_client():
    """実行時にクライアントを取得する（必要なら作成）"""
    global _client_lazy
    key = _get_api_key()
    if not key or not _use_new_sdk or _genai_module is None:
        return None
    if _client_lazy is None:
        try:
            _client_lazy = _genai_module.Client(api_key=key)
        except Exception as e:
            print(f"Gemini Client init error: {e}", flush=True)
            return None
    return _client_lazy


def _ensure_legacy_configured():
    """Legacy SDK 利用時に API キーを設定する"""
    if _genai_legacy and _get_api_key():
        _genai_legacy.configure(api_key=_get_api_key())

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
- 東北弁が少し混じる。
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

GEMINI_MODEL_NEW = "gemini-2.5-flash"
GEMINI_MODEL_LEGACY = "gemini-2.5-flash-lite"


def send_osc_emotion(emotion):
    """感情に応じたOSCメッセージを送信する"""
    try:
        osc_client.send_message("/avatar/parameters/Joy", 0.0)
        osc_client.send_message("/avatar/parameters/Sorrow", 0.0)
        osc_client.send_message("/avatar/parameters/Anger", 0.0)
        osc_client.send_message("/avatar/parameters/Fun", 0.0)
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


def _has_genai():
    """利用可能な Gemini SDK と API キーがあるか"""
    key = _get_api_key()
    if not key:
        return False
    return (_use_new_sdk and _get_client()) or _genai_legacy


def extract_text_from_image(image_path):
    """付箋画像からテキストを抽出する"""
    if not _get_api_key() or not _has_genai():
        return ""

    try:
        print(f"Extracting text from: {image_path}", flush=True)
        client = _get_client()
        if _use_new_sdk and client:
            myfile = client.files.upload(file=image_path)
            response = client.models.generate_content(
                model=GEMINI_MODEL_NEW,
                contents=["この付箋画像に書かれているテキストを正確に抽出してください。テキストのみを返してください。", myfile],
            )
            text = response.text.strip()
        else:
            _ensure_legacy_configured()
            sample_file = _genai_legacy.upload_file(path=image_path, display_name="Sticky Note")
            model = _genai_legacy.GenerativeModel(model_name=GEMINI_MODEL_LEGACY)
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
    if not _get_api_key() or not _has_genai():
        return "エラー：Gemini APIキーが設定されてへんで。管理者呼んできてや。"

    try:
        client = _get_client()
        if _use_new_sdk and client:
            myfile = client.files.upload(file=image_path)
            response = client.models.generate_content(
                model=GEMINI_MODEL_NEW,
                contents=[SYSTEM_PROMPT, myfile, "この付箋になんて書いてある？これについて一言コメントして。"],
                config=_types.GenerateContentConfig(response_mime_type="application/json"),
            )
        else:
            _ensure_legacy_configured()
            sample_file = _genai_legacy.upload_file(path=image_path, display_name="Sticky Note")
            model = _genai_legacy.GenerativeModel(
                model_name=GEMINI_MODEL_LEGACY,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content([SYSTEM_PROMPT, sample_file, "この付箋になんて書いてある？これについて一言コメントして。"])
        result = json.loads(response.text)
        comment = result.get("comment", "")
        emotion = result.get("emotion", "Neutral")
        send_osc_emotion(emotion)
        return f"[{emotion}] {comment}"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "なんや調子悪いわ。もう一回頼むわ。"


def generate_comment_from_text(text):
    if not _get_api_key() or not _has_genai():
        return "エラー：Gemini APIキーが設定されてへんで。"

    try:
        prompt = f"{SYSTEM_PROMPT}\n\nユーザーがWebアプリから以下の付箋を貼りました：\n「{text}」\n\nこれについて一言コメントして。"
        client = _get_client()
        if _use_new_sdk and client:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NEW,
                contents=prompt,
                config=_types.GenerateContentConfig(response_mime_type="application/json"),
            )
        else:
            _ensure_legacy_configured()
            model = _genai_legacy.GenerativeModel(
                model_name=GEMINI_MODEL_LEGACY,
                generation_config={"response_mime_type": "application/json"}
            )
            response = model.generate_content(prompt)
        result = json.loads(response.text)
        comment = result.get("comment", "")
        emotion = result.get("emotion", "Neutral")
        send_osc_emotion(emotion)
        return f"[{emotion}] {comment}"
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "なんや調子悪いわ。"


def generate_idea_from_two_texts(text_a, text_b):
    """
    2つの付箋の内容から、端的なタイトルとその説明を生成する。
    返り値: {"title": "20字以内のタイトル", "description": "1〜2文の説明"} または None
    """
    if not _get_api_key() or not _has_genai():
        return None
    prompt = (
        "以下の2つの付箋の内容を組み合わせて、新しいアイデアを生成してください。\n"
        "必ず次のJSON形式のみで出力してください。他は不要です。\n"
        '{"title": "20字以内の端的なタイトル（フレーズ）", "description": "1〜2文の説明文"}\n'
        f"付箋A: {text_a}\n付箋B: {text_b}"
    )
    try:
        client = _get_client()
        if _use_new_sdk and client:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NEW,
                contents=prompt,
            )
            raw = (response.text or "").strip()
        else:
            _ensure_legacy_configured()
            model = _genai_legacy.GenerativeModel(model_name=GEMINI_MODEL_LEGACY)
            response = model.generate_content(prompt)
            raw = (response.text or "").strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        title = (data.get("title") or "").strip()[:80]
        description = (data.get("description") or "").strip()[:300]
        if not title:
            return None
        return {"title": title, "description": description}
    except Exception as e:
        print(f"generate_idea_from_two_texts error: {e}", flush=True)
        return None


def wall_talk(note_text, user_message):
    """
    付箋の内容について「壁打ち」する。ユーザーの質問や掘り下げに短く返答する。
    """
    if not _get_api_key() or not _has_genai():
        return ""
    prompt = (
        "あなたは「リン子」というAIアシスタントです。東北弁が少し混じり、短くテンポよく話します。"
        "以下の付箋のアイデアについて、ユーザーが壁打ち（質問・掘り下げ）をしています。"
        "2〜3文で、親身にアドバイスやツッコミを返してください。\n"
        f"付箋の内容: {note_text}\n"
        f"ユーザー: {user_message or 'このアイデアについて聞きたい'}\n"
        "返答（説明や前置きは不要、本文のみ）:"
    )
    try:
        client = _get_client()
        if _use_new_sdk and client:
            response = client.models.generate_content(
                model=GEMINI_MODEL_NEW,
                contents=prompt,
            )
            reply = (response.text or "").strip()
        else:
            _ensure_legacy_configured()
            model = _genai_legacy.GenerativeModel(model_name=GEMINI_MODEL_LEGACY)
            response = model.generate_content(prompt)
            reply = (response.text or "").strip()
        return reply[:500]
    except Exception as e:
        print(f"wall_talk error: {e}", flush=True)
        return ""


import requests
import uuid

voicevox_url = os.getenv("VOICEVOX_URL", "http://localhost:50021")
speaker_id = os.getenv("VOICEVOX_SPEAKER_ID", "21")


import re

def generate_voice(text, output_dir):
    # Strip emotion tag (e.g. [Anger] ...) for speech generation
    clean_text = re.sub(r'^\[.*?\]\s*', '', text)
    print(f"Generating voice for: {clean_text[:20]}...", flush=True)
    try:
        query_payload = {'text': clean_text, 'speaker': speaker_id}
        print(f"Sending query to {voicevox_url}/audio_query", flush=True)
        query_response = requests.post(f"{voicevox_url}/audio_query", params=query_payload)
        if query_response.status_code != 200:
            print(f"VOICEVOX Query Error: {query_response.status_code} - {query_response.text}", flush=True)
            return None
        print("Synthesis...", flush=True)
        synthesis_payload = query_response.json()
        synthesis_response = requests.post(f"{voicevox_url}/synthesis", params={'speaker': speaker_id}, json=synthesis_payload)
        if synthesis_response.status_code != 200:
            print(f"VOICEVOX Synthesis Error: {synthesis_response.status_code} - {synthesis_response.text}", flush=True)
            return None
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
    print("AI Avatar Module")
    print("Using new SDK (google-genai)" if _use_new_sdk else "Using legacy SDK (google-generativeai)")
