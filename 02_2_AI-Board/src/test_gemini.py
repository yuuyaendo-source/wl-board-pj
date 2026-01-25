import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
print(f"API Key loaded: {api_key is not None}")
# Print first few chars to verify it's not empty or weird (don't print whole key)
if api_key:
    print(f"Key start: {api_key[:5]}...")

try:
    genai.configure(api_key=api_key)
    print("--------------------------------------------------", flush=True)
    # response = model.generate_content("Hello, can you hear me?")
    model = genai.GenerativeModel('gemini-2.5-flash-lite')
    response = model.generate_content("Hello, are you Gemini 2.5?")
    print(f"Response: {response.text}", flush=True)
    print("--------------------------------------------------", flush=True)
except Exception as e:
    print(f"Gemini API Error: {e}", flush=True)
