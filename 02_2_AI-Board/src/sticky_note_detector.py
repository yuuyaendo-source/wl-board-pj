"""
Sticky Note Detector Module
---------------------------
Webカメラの映像から黄色い付箋を検出し、その位置と画像データをWebアプリへ送信するモジュールです。
また、キャリブレーション（台形補正）機能や、設定の保存・読み込み機能も提供します。

主な機能:
1. HSV色空間を用いた付箋の検出
2. 4点指定による射影変換（台形補正）
3. 付箋のトラッキング（ID管理、重複送信防止）
4. 検出した付箋画像の切り出しとWebアプリへのアップロード
5. 設定ファイル (config.json) の読み書き
"""

import cv2
import numpy as np
import requests
import time
import os
import datetime
import base64
import sys
import math
import json

# ai_avatarをインポートするために親ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from webapp.ai_avatar import extract_text_from_image

def nothing(x):
    """トラックバー用のダミー関数"""
    pass

class TrackedNote:
    """
    追跡中の付箋情報を保持するクラス
    """
    def __init__(self, id, center_x, center_y, w, h):
        self.id = id
        self.center_x = center_x
        self.center_y = center_y
        self.w = w
        self.h = h
        self.last_seen = time.time()  # 最後に検知された時刻
        self.last_upload = 0          # 最後にアップロードされた時刻
        self.stable_counter = 0       # 安定して検知された回数（ノイズ除去用）

class StickyNoteDetector:
    """
    付箋検出・トラッキング・アップロードを行うメインクラス
    """
    def __init__(self):
        # 設定ファイルの読み込み
        self.CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()

        self.WEB_APP_API_URL = "http://localhost:3000/api/sticky_notes"
        self.TEMP_DIR = "temp_captures"
        
        self.tracked_notes = [] # TrackedNoteのリスト

        if not os.path.exists(self.TEMP_DIR):
            os.makedirs(self.TEMP_DIR)
            
        # キャリブレーション（射影変換）関連
        self.calibration_points = []
        self.homography_matrix = None
        self.is_calibrating = False
        self.target_width = 1920
        self.target_height = 1080

    def load_config(self):
        """config.jsonから設定を読み込む。失敗した場合はデフォルト値を使用。"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.BOARD_ID = config.get('board_id', 'default_board')
                    hsv = config.get('hsv', {})
                    self.h_min = hsv.get('h_min', 20)
                    self.h_max = hsv.get('h_max', 40)
                    self.s_min = hsv.get('s_min', 100)
                    self.s_max = hsv.get('s_max', 255)
                    self.v_min = hsv.get('v_min', 100)
                    self.v_max = hsv.get('v_max', 255)
                    
                    tracking = config.get('tracking', {})
                    self.TRACKING_DISTANCE_THRESHOLD = tracking.get('distance_threshold', 50.0)
                    self.UPLOAD_INTERVAL = tracking.get('upload_interval', 2.0)
                    self.STABLE_THRESHOLD = tracking.get('stable_threshold', 5)
                    self.DELETE_TIMEOUT = tracking.get('delete_timeout', 2.0)
                    print("Config loaded.")
            except Exception as e:
                print(f"Error loading config: {e}")
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        """デフォルト設定を適用"""
        self.BOARD_ID = "default_board"
        self.h_min, self.h_max = 20, 40
        self.s_min, self.s_max = 100, 255
        self.v_min, self.v_max = 100, 255
        self.TRACKING_DISTANCE_THRESHOLD = 50.0
        self.UPLOAD_INTERVAL = 2.0
        self.STABLE_THRESHOLD = 5
        self.DELETE_TIMEOUT = 2.0

    def save_config(self):
        """現在の設定をconfig.jsonに保存"""
        config = {
            "board_id": self.BOARD_ID,
            "hsv": {
                "h_min": self.h_min, "h_max": self.h_max,
                "s_min": self.s_min, "s_max": self.s_max,
                "v_min": self.v_min, "v_max": self.v_max
            },
            "tracking": {
                "distance_threshold": self.TRACKING_DISTANCE_THRESHOLD,
                "upload_interval": self.UPLOAD_INTERVAL,
                "stable_threshold": self.STABLE_THRESHOLD,
                "delete_timeout": self.DELETE_TIMEOUT
            }
        }
        try:
            with open(self.CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
            print("Config saved.")
        except Exception as e:
            print(f"Error saving config: {e}")

    def input_hsv_values(self):
        """コンソールからHSVの閾値を直接入力する"""
        print("\n--- 数値入力モード ---")
        try:
            h_min = input(f"Hue Min ({self.h_min}): ")
            if h_min: self.h_min = int(h_min)
            h_max = input(f"Hue Max ({self.h_max}): ")
            if h_max: self.h_max = int(h_max)
            s_min = input(f"Sat Min ({self.s_min}): ")
            if s_min: self.s_min = int(s_min)
            s_max = input(f"Sat Max ({self.s_max}): ")
            if s_max: self.s_max = int(s_max)
            v_min = input(f"Val Min ({self.v_min}): ")
            if v_min: self.v_min = int(v_min)
            v_max = input(f"Val Max ({self.v_max}): ")
            if v_max: self.v_max = int(v_max)
            
            # トラックバーに反映
            cv2.setTrackbarPos('Hue Min', 'Sticky Note Detector', self.h_min)
            cv2.setTrackbarPos('Hue Max', 'Sticky Note Detector', self.h_max)
            cv2.setTrackbarPos('Sat Min', 'Sticky Note Detector', self.s_min)
            cv2.setTrackbarPos('Sat Max', 'Sticky Note Detector', self.s_max)
            cv2.setTrackbarPos('Val Min', 'Sticky Note Detector', self.v_min)
            cv2.setTrackbarPos('Val Max', 'Sticky Note Detector', self.v_max)
            print("設定を更新しました。")
        except ValueError:
            print("無効な入力です。")

    def mouse_callback(self, event, x, y, flags, param):
        """マウスイベント処理：キャリブレーションポイントの指定"""
        if event == cv2.EVENT_LBUTTONDOWN and self.is_calibrating:
            if len(self.calibration_points) < 4:
                self.calibration_points.append([x, y])
                print(f"Calibration Point {len(self.calibration_points)}: ({x}, {y})")
                
                if len(self.calibration_points) == 4:
                    self.calculate_homography()
                    self.is_calibrating = False
                    print("Calibration complete.")

    def calculate_homography(self):
        """4点の座標から射影変換行列を計算"""
        pts_src = np.float32(self.calibration_points)
        # 変換後の座標（長方形）
        pts_dst = np.float32([
            [0, 0],
            [self.target_width, 0],
            [self.target_width, self.target_height],
            [0, self.target_height]
        ])
        self.homography_matrix = cv2.getPerspectiveTransform(pts_src, pts_dst)

    def detect_from_image(self, image):
        """
        静止画から付箋を検知して切り出す（スマホアップロード用）
        Returns: 検知された付箋情報のリスト [{'image': roi, 'x': x, ...}, ...]
        """
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([self.h_min, self.s_min, self.v_min])
        upper_bound = np.array([self.h_max, self.s_max, self.v_max])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        # ノイズ除去
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        detected_notes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000: # 面積閾値（小さすぎるノイズを除外）
                x, y, w, h = cv2.boundingRect(contour)
                roi = image[y:y+h, x:x+w]
                if roi.size > 0:
                    detected_notes.append({
                        'image': roi,
                        'x': x, 'y': y, 'w': w, 'h': h
                    })
        return detected_notes

    def detect_and_track(self, frame):
        """
        フレームごとの検知とトラッキング処理
        """
        # 1. 画像処理（射影変換 -> HSV変換 -> マスク作成）
        if self.homography_matrix is not None:
            processed_frame = cv2.warpPerspective(frame, self.homography_matrix, (self.target_width, self.target_height))
        else:
            processed_frame = frame.copy()

        hsv = cv2.cvtColor(processed_frame, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([self.h_min, self.s_min, self.v_min])
        upper_bound = np.array([self.h_max, self.s_max, self.v_max])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)
        
        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # 2. 現在のフレームでの検知リスト作成
        current_detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 2000:
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w / 2
                center_y = y + h / 2
                current_detections.append({'x': x, 'y': y, 'w': w, 'h': h, 'cx': center_x, 'cy': center_y, 'contour': contour})

        # 3. トラッキング処理（既存の付箋と紐付け）
        current_time = time.time()
        matched_indices = set()
        
        # 既存の追跡対象とのマッチング
        for note in self.tracked_notes:
            min_dist = float('inf')
            match_idx = -1

            for i, detection in enumerate(current_detections):
                if i in matched_indices:
                    continue
                
                # 距離計算
                dist = math.sqrt((note.center_x - detection['cx'])**2 + (note.center_y - detection['cy'])**2)
                if dist < min_dist:
                    min_dist = dist
                    match_idx = i

            if match_idx != -1 and min_dist < self.TRACKING_DISTANCE_THRESHOLD:
                # マッチした場合：位置更新
                det = current_detections[match_idx]
                note.center_x = det['cx']
                note.center_y = det['cy']
                note.w = det['w']
                note.h = det['h']
                note.last_seen = current_time
                note.stable_counter = min(note.stable_counter + 1, 100)
                matched_indices.add(match_idx)
                
                # 描画
                cv2.rectangle(processed_frame, (det['x'], det['y']), (det['x'] + det['w'], det['y'] + det['h']), (0, 255, 0), 2)
                cv2.putText(processed_frame, f"ID:{note.id}", (det['x'], det['y'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # アップロード判定（安定して検知されており、かつ前回のアップロードから時間が経過している場合）
                if note.stable_counter >= self.STABLE_THRESHOLD and (current_time - note.last_upload > self.UPLOAD_INTERVAL):
                    roi = processed_frame[det['y']:det['y']+det['h'], det['x']:det['x']+det['w']]
                    if roi.size > 0:
                        self.upload_note(note, roi, det['x'], det['y'], det['w'], det['h'], processed_frame.shape)

        # マッチしなかった検知：新規登録候補
        for i, detection in enumerate(current_detections):
            if i not in matched_indices:
                # 新規ID発行
                new_id = f"cam-{int(time.time() * 1000)}-{i}"
                new_note = TrackedNote(new_id, detection['cx'], detection['cy'], detection['w'], detection['h'])
                self.tracked_notes.append(new_note)
                
                # 新規検知の描画（黄色）
                cv2.rectangle(processed_frame, (detection['x'], detection['y']), (detection['x'] + detection['w'], detection['y'] + detection['h']), (0, 255, 255), 2)

        # 4. ロストした付箋の削除
        self.tracked_notes = [n for n in self.tracked_notes if current_time - n.last_seen < self.DELETE_TIMEOUT]

        # 画面にHSV情報を表示
        info_text = [
            f"Board: {self.BOARD_ID}",
            f"H: {self.h_min}-{self.h_max}",
            f"S: {self.s_min}-{self.s_max}",
            f"V: {self.v_min}-{self.v_max}",
            "[S]ave Config"
        ]
        for i, text in enumerate(info_text):
            cv2.putText(processed_frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return processed_frame, mask

    def upload_note(self, note_obj, roi_image, x, y, w, h, frame_shape):
        """
        検知した付箋画像を保存し、Webアプリへ送信する
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{note_obj.id}_{timestamp}.jpg"
        filepath = os.path.join(self.TEMP_DIR, filename)
        
        print(f"Uploading note: {note_obj.id}")
        
        try:
            cv2.imwrite(filepath, roi_image)
            
            # テキスト抽出（AI）
            text = extract_text_from_image(filepath)
            if not text:
                text = "(テキスト抽出できませんでした)"
            
            # 画像をBase64エンコード
            with open(filepath, 'rb') as img_file:
                img_base64 = base64.b64encode(img_file.read()).decode('utf-8')
                image_url = f"data:image/jpeg;base64,{img_base64}"
            
            # 座標の正規化 (0.0 - 1.0)
            frame_h, frame_w = frame_shape[:2]
            normalized_x = x / frame_w
            normalized_y = y / frame_h
            ratio_w = w / frame_w

            note_data = {
                "boardId": self.BOARD_ID,
                "note": {
                    "id": note_obj.id, # トラッキングしたIDを使用（これが重要）
                    "text": text,
                    # Webアプリの座標系に合わせて変換（4000x4000の仮想キャンバス）
                    "x": normalized_x * 4000, 
                    "y": normalized_y * 4000,
                    "normalizedX": normalized_x,
                    "normalizedY": normalized_y,
                    "ratioW": ratio_w,
                    "color": "#ffeb3b",
                    "pinned": False,
                    "author": "Real Cam",
                    "createdAt": int(time.time() * 1000),
                    "imageUrl": image_url
                }
            }
            
            # WebアプリへPOSTリクエスト
            response = requests.post(
                self.WEB_APP_API_URL,
                json=note_data,
                headers={'Content-Type': 'application/json'},
                timeout=5
            )
            if response.status_code == 200:
                print(f"Note sent success: {note_obj.id}")
                note_obj.last_upload = time.time()
            else:
                print(f"API Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error uploading note: {e}")

    def run(self):
        """メインループ"""
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("Camera open failed.")
            return

        cv2.namedWindow('Sticky Note Detector')
        cv2.setMouseCallback('Sticky Note Detector', self.mouse_callback)
        
        # トラックバー (コールバックで値を更新するが、setTrackbarPosで同期もする)
        def on_trackbar(val): pass
        
        cv2.createTrackbar('Hue Min', 'Sticky Note Detector', self.h_min, 179, on_trackbar)
        cv2.createTrackbar('Hue Max', 'Sticky Note Detector', self.h_max, 179, on_trackbar)
        cv2.createTrackbar('Sat Min', 'Sticky Note Detector', self.s_min, 255, on_trackbar)
        cv2.createTrackbar('Sat Max', 'Sticky Note Detector', self.s_max, 255, on_trackbar)
        cv2.createTrackbar('Val Min', 'Sticky Note Detector', self.v_min, 255, on_trackbar)
        cv2.createTrackbar('Val Max', 'Sticky Note Detector', self.v_max, 255, on_trackbar)

        print("開始: 'q'で終了, 'c'でキャリブレーション, 'S'で設定保存")
        print("キー操作: u/j(Hmin), i/k(Hmax), o/l(Smin), p/;(Smax), [/'](Vmin), ]/\\(Vmax)")

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # トラックバーの値を取得（ユーザーがスライダーを動かしたかもしれないので）
            self.h_min = cv2.getTrackbarPos('Hue Min', 'Sticky Note Detector')
            self.h_max = cv2.getTrackbarPos('Hue Max', 'Sticky Note Detector')
            self.s_min = cv2.getTrackbarPos('Sat Min', 'Sticky Note Detector')
            self.s_max = cv2.getTrackbarPos('Sat Max', 'Sticky Note Detector')
            self.v_min = cv2.getTrackbarPos('Val Min', 'Sticky Note Detector')
            self.v_max = cv2.getTrackbarPos('Val Max', 'Sticky Note Detector')

            processed_frame, mask = self.detect_and_track(frame)

            # キャリブレーション点描画
            if self.is_calibrating:
                for pt in self.calibration_points:
                    cv2.circle(processed_frame, tuple(pt), 5, (0, 0, 255), -1)

            cv2.imshow('Sticky Note Detector', processed_frame)
            cv2.imshow('Mask Debug', mask)

            key = cv2.waitKey(1) & 0xFF
            
            # キー操作による微調整
            if key == ord('q'):
                break
            elif key == ord('c'):
                self.is_calibrating = True
                self.calibration_points = []
                self.homography_matrix = None
                print("Calibration started.")
            elif key == ord('r'):
                self.homography_matrix = None
                self.tracked_notes = []
                print("Reset.")
            elif key == ord('S'): # Shift+s
                self.save_config()
            elif key == ord('n'):
                self.input_hsv_values()
            
            # 微調整ロジック
            updates = []
            if key == ord('u'): self.h_min = min(self.h_min + 1, 179); updates.append(('Hue Min', self.h_min))
            elif key == ord('j'): self.h_min = max(self.h_min - 1, 0); updates.append(('Hue Min', self.h_min))
            elif key == ord('i'): self.h_max = min(self.h_max + 1, 179); updates.append(('Hue Max', self.h_max))
            elif key == ord('k'): self.h_max = max(self.h_max - 1, 0); updates.append(('Hue Max', self.h_max))
            elif key == ord('o'): self.s_min = min(self.s_min + 1, 255); updates.append(('Sat Min', self.s_min))
            elif key == ord('l'): self.s_min = max(self.s_min - 1, 0); updates.append(('Sat Min', self.s_min))
            elif key == ord('p'): self.s_max = min(self.s_max + 1, 255); updates.append(('Sat Max', self.s_max))
            elif key == ord(';'): self.s_max = max(self.s_max - 1, 0); updates.append(('Sat Max', self.s_max))
            elif key == ord('['): self.v_min = min(self.v_min + 1, 255); updates.append(('Val Min', self.v_min))
            elif key == ord('\''): self.v_min = max(self.v_min - 1, 0); updates.append(('Val Min', self.v_min))
            elif key == ord(']'): self.v_max = min(self.v_max + 1, 255); updates.append(('Val Max', self.v_max))
            elif key == ord('\\'): self.v_max = max(self.v_max - 1, 0); updates.append(('Val Max', self.v_max))

            # トラックバーに反映
            for name, val in updates:
                cv2.setTrackbarPos(name, 'Sticky Note Detector', val)

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = StickyNoteDetector()
    detector.run()
