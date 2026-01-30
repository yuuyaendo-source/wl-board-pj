"""
Gemini API と .env の確認用スクリプト。
02_2_AI-Board フォルダで実行: python check_gemini_env.py
"""
import os
from pathlib import Path

# このスクリプトは 02_2_AI-Board 直下にある想定
_env_path = Path(__file__).resolve().parent / ".env"
from dotenv import load_dotenv
load_dotenv(_env_path)

api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
print(f".env path: {_env_path}")
print(f".env exists: {_env_path.exists()}")
print(f"GEMINI_API_KEY set: {bool(api_key)}")
if api_key:
    print(f"Key (masked): {api_key[:8]}...{api_key[-4:]}")
else:
    print("GEMINI_API_KEY is empty or not set.")
    exit(1)

# 新しい google-genai でテスト、失敗時は Legacy でテスト
try:
    from google import genai
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents="Hello, 短く「OK」とだけ返してください。",
    )
    print("Gemini response (new SDK):", response.text.strip())
    print("--- Gemini API OK ---")
except Exception as e1:
    print("New SDK failed:", e1)
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash-lite")
        response = model.generate_content("Hello, 短く「OK」とだけ返してください。")
        print("Gemini response (legacy SDK):", response.text.strip())
        print("--- Gemini API OK (legacy) ---")
    except Exception as e2:
        print("Legacy SDK Error:", e2)
        exit(1)
