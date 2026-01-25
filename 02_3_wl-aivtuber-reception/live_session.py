import os
import asyncio
import base64
import io
import traceback
import cv2
import pyaudio
import PIL.Image
import mss
import logging
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

# --- 定数設定 ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024

MODEL = "models/gemini-2.5-flash-native-audio-preview-09-2025" # または最新のモデル

# 自動切断までの時間（秒）
AUTO_DISCONNECT_SECONDS = 180 # 3分

class GeminiLiveSession:
    def __init__(self, video_mode="camera", voice_name="Zephyr", stop_event=None):
        self.video_mode = video_mode
        self.voice_name = voice_name
        self.stop_event = stop_event
        self.audio_in_queue = None
        self.out_queue = None
        self.session = None
        self.client = genai.Client(
            http_options={"api_version": "v1beta"},
            api_key=os.environ.get("GEMINI_API_KEY"),
        )
        self.config = types.LiveConnectConfig(
            response_modalities=["AUDIO"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=self.voice_name)
                )
            ),
        )
        self.pya = pyaudio.PyAudio()
        self.audio_stream = None
        self.running = False
        self.last_activity_time = 0

    def _get_frame(self, cap):
        ret, frame = cap.read()
        if not ret:
            return None
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = PIL.Image.fromarray(frame_rgb)
        img.thumbnail([1024, 1024])

        image_io = io.BytesIO()
        img.save(image_io, format="jpeg")
        image_io.seek(0)

        mime_type = "image/jpeg"
        image_bytes = image_io.read()
        return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_frames(self):
        cap = await asyncio.to_thread(cv2.VideoCapture, 0)
        while self.running:
            frame = await asyncio.to_thread(self._get_frame, cap)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)
        cap.release()

    def _get_screen(self):
        with mss.mss() as sct:
            monitor = sct.monitors[1] # メインモニター
            i = sct.grab(monitor)
            mime_type = "image/jpeg"
            image_bytes = mss.tools.to_png(i.rgb, i.size)
            img = PIL.Image.open(io.BytesIO(image_bytes))
            
            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)
            image_bytes = image_io.read()
            return {"mime_type": mime_type, "data": base64.b64encode(image_bytes).decode()}

    async def get_screen(self):
        while self.running:
            frame = await asyncio.to_thread(self._get_screen)
            if frame is None:
                break
            await asyncio.sleep(1.0)
            await self.out_queue.put(frame)

    async def send_realtime(self):
        while self.running:
            msg = await self.out_queue.get()
            await self.session.send(input=msg)

    async def listen_audio(self):
        mic_info = self.pya.get_default_input_device_info()
        self.audio_stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=SEND_SAMPLE_RATE,
            input=True,
            input_device_index=mic_info["index"],
            frames_per_buffer=CHUNK_SIZE,
        )
        kwargs = {"exception_on_overflow": False}
        while self.running:
            data = await asyncio.to_thread(self.audio_stream.read, CHUNK_SIZE, **kwargs)
            await self.out_queue.put({"data": data, "mime_type": "audio/pcm"})
            # 音声入力があったらアクティビティ時間を更新（簡易的）
            # 本来はVAD(Voice Activity Detection)を入れるべきだが、ここではデータ送信をアクティビティとみなす
            # ただし、常時送信しているので、これは「セッションが生きている」ことの確認にしかならない。
            # 本当の無言検知は受信側で行うか、VADが必要。
            # ここでは「ユーザーが明示的に終了しない限り続く」が、
            # 別途タイマーで強制終了するロジックを run メソッドに入れる。

    async def receive_audio(self):
        while self.running:
            try:
                turn = self.session.receive()
                async for response in turn:
                    if data := response.data:
                        self.audio_in_queue.put_nowait(data)
                        continue
                    if text := response.text:
                        print(text, end="")
            except Exception as e:
                logging.error(f"Error receiving audio: {e}")
                break

    async def play_audio(self):
        stream = await asyncio.to_thread(
            self.pya.open,
            format=FORMAT,
            channels=CHANNELS,
            rate=RECEIVE_SAMPLE_RATE,
            output=True,
        )
        while self.running:
            bytestream = await self.audio_in_queue.get()
            await asyncio.to_thread(stream.write, bytestream)

    async def wait_for_quit_key(self):
        """キー入力を監視し、'Esc'または'q'が押されたら終了"""
        import sys
        
        def check_input():
            while self.running:
                try:
                    if sys.platform == 'win32':
                        import msvcrt
                        if msvcrt.kbhit():
                            key = msvcrt.getch()
                            # Escキー (0x1b) または q
                            if key in (b'\x1b', b'q', b'Q'):
                                logging.info("User requested to quit Live Mode")
                                self.running = False
                                return
                except Exception as e:
                    logging.error(f"Error in key check: {e}")
                    pass
        
        await asyncio.to_thread(check_input)

    async def run(self):
        self.running = True
        try:
            async with (
                self.client.aio.live.connect(model=MODEL, config=self.config) as session,
                asyncio.TaskGroup() as tg,
            ):
                self.session = session
                self.audio_in_queue = asyncio.Queue()
                self.out_queue = asyncio.Queue(maxsize=5)

                tg.create_task(self.send_realtime())
                tg.create_task(self.listen_audio())
                
                if self.video_mode == "camera":
                    tg.create_task(self.get_frames())
                elif self.video_mode == "screen":
                    tg.create_task(self.get_screen())

                tg.create_task(self.receive_audio())
                tg.create_task(self.play_audio())
                
                # キー入力監視タスクを追加
                tg.create_task(self.wait_for_quit_key())

                # 自動切断タイマー（または手動終了を待つ）
                print(f"\n{'='*50}")
                print(f" Live Mode Started")
                print(f" Press 'Esc' or 'q' to return to Reception Mode")
                print(f" Auto-disconnect in {AUTO_DISCONNECT_SECONDS} seconds")
                print(f"{'='*50}\n")
                
                # タイムアウトまたは手動終了を待つ
                for _ in range(AUTO_DISCONNECT_SECONDS * 10):
                    if not self.running:
                        print("\nManually disconnecting session...")
                        break
                    
                    if self.stop_event and self.stop_event.is_set():
                        print("\nStop event received. Disconnecting session...")
                        self.running = False
                        break

                    await asyncio.sleep(0.1)
                else:
                    print("\nAuto-disconnecting session...")
                
                self.running = False
                raise asyncio.CancelledError("Session ended")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            traceback.print_exc()
        finally:
            self.running = False
            if self.audio_stream:
                self.audio_stream.close()
            self.pya.terminate()

if __name__ == "__main__":
    # テスト実行用
    session = GeminiLiveSession(video_mode="camera")
    asyncio.run(session.run())
