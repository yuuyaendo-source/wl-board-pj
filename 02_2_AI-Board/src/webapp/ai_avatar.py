import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Character System Prompt
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
"""

def generate_comment(image_path):
    if not api_key:
        return "エラー：Gemini APIキーが設定されてへんで。管理者呼んできてや。"

    try:
        # Upload the file
        sample_file = genai.upload_file(path=image_path, display_name="Sticky Note")
        
        # Create the model
        model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        
        # Generate content
        response = model.generate_content([SYSTEM_PROMPT, sample_file, "この付箋になんて書いてある？これについて一言コメントして。"])
        
        return response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        return "なんや調子悪いわ。もう一回頼むわ。"

if __name__ == "__main__":
    # Test execution
    print("AI Avatar Module")
