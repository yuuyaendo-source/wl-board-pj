import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

with open('models_list.txt', 'w', encoding='utf-8') as f:
    print("Listing supported models:", file=f)
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"- {m.name} (Version: {m.version})", file=f)
    except Exception as e:
        print(f"Error listing models: {e}", file=f)
