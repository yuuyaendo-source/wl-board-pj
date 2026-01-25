import threading
import time
import asyncio
import logging
import sys
import speech_recognition as sr
from local_processor import poll_sqs_queue, introduce_self
from live_session import GeminiLiveSession

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("main_controller.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# グローバルフラグ
live_mode_trigger = threading.Event()

def run_reception_mode(stop_event):
    logging.info("Starting Reception Mode (SQS Polling)...")
    poll_sqs_queue(stop_event)
    logging.info("Reception Mode Stopped.")

def run_live_mode(video_mode="camera", voice_name="Zephyr", stop_event=None):
    logging.info(f"Starting Live Mode (Gemini Live) - {video_mode} mode, Voice: {voice_name}...")
    session = GeminiLiveSession(video_mode=video_mode, voice_name=voice_name, stop_event=stop_event)
    try:
        asyncio.run(session.run())
    except Exception as e:
        logging.error(f"Live session error: {e}")
    logging.info("Live Mode Stopped.")

def listen_for_trigger(stop_event):
    """音声で「リン子さん」を検出したらLiveモードに切り替え"""
    recognizer = sr.Recognizer()
    mic = sr.Microphone()
    
    logging.info("Voice trigger listener started...")
    
    with mic as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
    
    try:
        while not stop_event.is_set():
            try:
                with mic as source:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                
                try:
                    text = recognizer.recognize_google(audio, language="ja-JP")
                    logging.info(f"Recognized: {text}")
                    
                    if "リン子" in text or "りん子" in text:
                        logging.info("Trigger word detected! Switching to Live Mode...")
                        live_mode_trigger.set()
                        break
                        
                except sr.UnknownValueError:
                    pass  # 音声認識できなかった場合は無視
                except sr.RequestError as e:
                    logging.error(f"Speech recognition error: {e}")
                    
            except sr.WaitTimeoutError:
                pass  # タイムアウトは正常、継続
                
    except Exception as e:
        logging.error(f"Voice listener error: {e}")

def wait_for_input(stop_event):
    """キーボード入力を待つスレッド"""
    while not stop_event.is_set():
        try:
            user_input = input()
            if user_input.lower() == 'q':
                live_mode_trigger.clear()
                stop_event.set()
                break
            else:
                # Enterキーが押された
                live_mode_trigger.set()
                break
        except:
            break

def main():
    global live_mode_trigger
    
    # 初回起動時に自己紹介
    is_first_run = True
    
    while True:
        live_mode_trigger.clear()
        
        # 1. 受付モードを開始
        stop_event = threading.Event()
        
        reception_thread = threading.Thread(target=run_reception_mode, args=(stop_event,))
        reception_thread.start()
        
        # 音声トリガースレッドを開始
        voice_thread = threading.Thread(target=listen_for_trigger, args=(stop_event,), daemon=True)
        voice_thread.start()

        # 初回のみ自己紹介
        if is_first_run:
            time.sleep(1)  # スレッドが起動するまで少し待つ
            introduce_self()
            is_first_run = False

        print("\n" + "="*30)
        print(" Reception Mode is Running")
        print(" Press 'Enter' to switch to Live Mode")
        print(" Or say 'リン子さん' to activate")
        print(" Type 'q' and Enter to Quit")
        print("="*30 + "\n")

        # キーボード入力スレッド
        input_thread = threading.Thread(target=wait_for_input, args=(stop_event,), daemon=True)
        input_thread.start()

        # Enterキーまたは音声トリガーを待つ
        while not stop_event.is_set() and not live_mode_trigger.is_set():
            time.sleep(0.1)
        
        if stop_event.is_set() and not live_mode_trigger.is_set():
            # 'q'で終了
            print("Quitting...")
            reception_thread.join(timeout=2)
            return
        
        # 2. ライブモードへの切り替え
        print("Switching to Live Mode...")
        stop_event.set()
        reception_thread.join(timeout=2)

        # ビデオモードを選択
        print("\n" + "="*30)
        print(" Select Video Mode:")
        print(" 1. Camera (カメラ)")
        print(" 2. Screen (画面共有)")
        print("="*30)
        mode_input = input("Enter 1 or 2 (default: 1): ").strip()
        
        video_mode = "camera"
        if mode_input == "2":
            video_mode = "screen"
            print("Screen sharing mode selected.")
        else:
            print("Camera mode selected.")

        # 音声を選択
        print("\n" + "="*30)
        print(" Select Voice:")
        print(" 1. Zephyr (default)")
        print(" 2. Aoede")
        print(" 3. Charon")
        print(" 4. Fenrir")
        print(" 5. Kore")
        print(" 6. Puck")
        print("="*30)
        voice_input = input("Enter 1-6 (default: 1): ").strip()
        
        voice_map = {
            "1": "Zephyr",
            "2": "Aoede",
            "3": "Charon",
            "4": "Fenrir",
            "5": "Kore",
            "6": "Puck"
        }
        voice_name = voice_map.get(voice_input, "Zephyr")
        print(f"Voice selected: {voice_name}")

        run_live_mode(video_mode, voice_name)
        
        print("Returning to Reception Mode...")

if __name__ == "__main__":
    main()
