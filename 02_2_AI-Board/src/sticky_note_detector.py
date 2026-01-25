import cv2
import numpy as np
import requests
import time
import os
import datetime
import base64
import sys

# ai_avatarをインポートするために親ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from webapp.ai_avatar import extract_text_from_image

# 設定
WEB_APP_API_URL = "http://localhost:3000/api/sticky_notes"
BOARD_ID = "odgeqgf"  # 既存のボードID（環境変数から取得可能にする）
DEBOUNCE_SECONDS = 3.0
TEMP_DIR = "temp_captures"

if not os.path.exists(TEMP_DIR):
    os.makedirs(TEMP_DIR)

def nothing(x):
    pass

def main():
    # Webカメラをオープン
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("カメラを開けませんでした。")
        return

    # 初期値設定（HSV色空間）
    h_min, h_max = 20, 40
    s_min, s_max = 100, 255
    v_min, v_max = 100, 255

    # 設定用ウィンドウとトラックバーの作成
    cv2.namedWindow('Settings')
    cv2.createTrackbar('Hue Min', 'Settings', h_min, 179, nothing)
    cv2.createTrackbar('Hue Max', 'Settings', h_max, 179, nothing)
    cv2.createTrackbar('Sat Min', 'Settings', s_min, 255, nothing)
    cv2.createTrackbar('Sat Max', 'Settings', s_max, 255, nothing)
    cv2.createTrackbar('Val Min', 'Settings', v_min, 255, nothing)
    cv2.createTrackbar('Val Max', 'Settings', v_max, 255, nothing)

    print("開始: 'q' キーで終了します。")
    print("調整: 'Settings' ウィンドウのスライダーで検出色を調整してください。")
    
    last_upload_time = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("フレームを取得できませんでした（終了）。")
            break

        # HSV変換
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

        if cv2.getWindowProperty('Settings', cv2.WND_PROP_VISIBLE) < 1:
            # ウィンドウが閉じられたら再作成するか、デフォルト値を使うなどの処理
            # ここでは単に再作成する
            cv2.namedWindow('Settings')
            cv2.createTrackbar('Hue Min', 'Settings', h_min, 179, nothing)
            cv2.createTrackbar('Hue Max', 'Settings', h_max, 179, nothing)
            cv2.createTrackbar('Sat Min', 'Settings', s_min, 255, nothing)
            cv2.createTrackbar('Sat Max', 'Settings', s_max, 255, nothing)
            cv2.createTrackbar('Val Min', 'Settings', v_min, 255, nothing)
            cv2.createTrackbar('Val Max', 'Settings', v_max, 255, nothing)

        # トラックバーから現在値を取得
        h_min = cv2.getTrackbarPos('Hue Min', 'Settings')
        h_max = cv2.getTrackbarPos('Hue Max', 'Settings')
        s_min = cv2.getTrackbarPos('Sat Min', 'Settings')
        s_max = cv2.getTrackbarPos('Sat Max', 'Settings')
        v_min = cv2.getTrackbarPos('Val Min', 'Settings')
        v_max = cv2.getTrackbarPos('Val Max', 'Settings')

        lower_bound = np.array([h_min, s_min, v_min])
        upper_bound = np.array([h_max, s_max, v_max])

        # マスク作成
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        # ノイズ除去
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # 輪郭検出
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000:
                x, y, w, h = cv2.boundingRect(contour)
                
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.putText(frame, "Sticky Note", (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 2)

                # アップロードロジック
                current_time = time.time()
                if current_time - last_upload_time > DEBOUNCE_SECONDS:
                    roi = frame[y:y+h, x:x+w]
                    if roi.size > 0:
                        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        filename = f"note_{timestamp}.jpg"
                        filepath = os.path.join(TEMP_DIR, filename)
                        
                        try:
                            cv2.imwrite(filepath, roi)
                            
                            # テキスト抽出（Gemini API使用）
                            text = extract_text_from_image(filepath)
                            if not text:
                                text = "(テキスト抽出できませんでした)"
                            
                            # 画像をBase64エンコード
                            with open(filepath, 'rb') as img_file:
                                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                                image_url = f"data:image/jpeg;base64,{img_base64}"
                            
                            # WebアプリのAPIに直接送信
                            note_id = f"cam-{int(time.time() * 1000)}"
                            note_data = {
                                "boardId": BOARD_ID,
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
                                    WEB_APP_API_URL,
                                    json=note_data,
                                    headers={'Content-Type': 'application/json'},
                                    timeout=5
                                )
                                if response.status_code == 200:
                                    print(f"Note sent to Web App: {note_id} - Text: {text[:50]}")
                                    last_upload_time = current_time
                                    cv2.putText(frame, "UPLOADED!", (x, y + h + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                                else:
                                    print(f"API Error: {response.status_code} - {response.text}")
                            except requests.exceptions.RequestException as e:
                                print(f"Request error: {e}")
                                # サーバーが起動していなくてもエラーで止めない
                        except Exception as e:
                            print(f"Error: {e}")

        # 結果表示
        cv2.imshow('Sticky Note Detector', frame)
        
        # マスク画面も表示（調整しやすくするため）
        # 元画像と結合して表示することも可能だが、今回は別ウィンドウで見せる
        cv2.imshow('Mask Debug', mask)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
