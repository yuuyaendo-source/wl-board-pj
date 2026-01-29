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

パフォーマンス（2層構造）:
- データ用(Original): 元解像度の画像。OCR用切り出し・座標計算のベース。
- 表示・調整用(Preview): 幅960pxにリサイズした軽量フレーム。HSVプレビュー・スライダー・四隅クリックはこちらで処理し、取得した座標は元解像度にスケールバックする。

非同期解析（改善指示書3）:
- メインスレッド: カメラ取得・HSV・描画・マウスに専念。付箋検知時は RequestQueue に投入するだけ（待機しない）。
- ワーカースレッド: キューを監視し、OCR -> API 送信を実行。解析中は is_processing で排他し、UI に「解析中...」を表示する。
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
import threading
import queue

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

# ai_avatarをインポートするために親ディレクトリをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from webapp.ai_avatar import extract_text_from_image

# 表示・調整用フレームの幅（軽量処理用）
PREVIEW_WIDTH = 960


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
        # .env の読み込み（02_2_AI-Board ルートを参照）
        self._root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        if load_dotenv:
            env_path = os.path.join(self._root_dir, '.env')
            load_dotenv(env_path)

        # 設定ファイルの読み込み
        self.CONFIG_FILE = os.path.join(os.path.dirname(__file__), 'config.json')
        self.load_config()

        # カメラソース: .env の RTSP_URL があれば使用、なければ 0 (Webカメラ)
        rtsp_url = os.environ.get('RTSP_URL', '').strip()
        self.camera_source = rtsp_url if rtsp_url else 0

        # 付箋検知の最小面積: .env の MIN_AREA で上書き、なければ config の detection.min_area、未設定なら解像度で自動調整
        env_min = os.environ.get('MIN_AREA', '').strip()
        if env_min and env_min.isdigit():
            self.min_area = int(env_min)

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
        # プレビュー⇔元解像度のスケール用（mouse_callbackで使用）
        self._last_original_width = None
        self._last_original_height = None
        self._last_preview_width = None
        self._last_preview_height = None

        # 解析処理の非同期化（改善指示書3）
        self._request_queue = queue.Queue()
        self._is_processing = False
        self._processing_lock = threading.Lock()
        self._worker_stop = threading.Event()

    def load_config(self):
        """config.jsonから設定を読み込む。失敗した場合はデフォルト値を使用。"""
        if os.path.exists(self.CONFIG_FILE):
            try:
                with open(self.CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    self.BOARD_ID = config.get('board_id', 'default_board')
                    hsv = config.get('hsv', {})
                    self.h_min = hsv.get('h_min', 20)
                    self.h_max = hsv.get('h_max', 46)
                    self.s_min = hsv.get('s_min', 0)
                    self.s_max = hsv.get('s_max', 50)
                    self.v_min = hsv.get('v_min', 0)
                    self.v_max = hsv.get('v_max', 255)
                    
                    tracking = config.get('tracking', {})
                    self.TRACKING_DISTANCE_THRESHOLD = tracking.get('distance_threshold', 50.0)
                    self.UPLOAD_INTERVAL = tracking.get('upload_interval', 2.0)
                    self.STABLE_THRESHOLD = tracking.get('stable_threshold', 5)
                    self.DELETE_TIMEOUT = tracking.get('delete_timeout', 2.0)
                    detection = config.get('detection', {})
                    _min = detection.get('min_area')
                    self.min_area = int(_min) if _min is not None else None
                    print("Config loaded.")
            except Exception as e:
                print(f"Error loading config: {e}")
                self.set_default_config()
        else:
            self.set_default_config()

    def set_default_config(self):
        """デフォルト設定を適用"""
        self.BOARD_ID = "default_board"
        self.h_min, self.h_max = 20, 46
        self.s_min, self.s_max = 0, 50
        self.v_min, self.v_max = 0, 255
        self.TRACKING_DISTANCE_THRESHOLD = 50.0
        self.UPLOAD_INTERVAL = 2.0
        self.STABLE_THRESHOLD = 5
        self.DELETE_TIMEOUT = 2.0
        self.min_area = None  # None = 解像度に応じて自動調整

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
            },
            "detection": {
                "min_area": self.min_area
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
        """マウスイベント処理：プレビュー上でクリックし、元解像度にスケールしてキャリブレーションポイントを指定"""
        if event == cv2.EVENT_LBUTTONDOWN and self.is_calibrating:
            if len(self.calibration_points) < 4:
                # 軽量フレーム上の座標を元解像度にスケールバック
                if (self._last_original_width and self._last_original_height and
                        self._last_preview_width and self._last_preview_height):
                    orig_x = x * (self._last_original_width / self._last_preview_width)
                    orig_y = y * (self._last_original_height / self._last_preview_height)
                    self.calibration_points.append([orig_x, orig_y])
                    print(f"Calibration Point {len(self.calibration_points)}: preview({x},{y}) -> original({orig_x:.0f},{orig_y:.0f})")
                else:
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

    def _get_min_area(self, frame):
        """
        付箋検知の最小面積を返す。
        self.min_area が設定されていればその値、なければ解像度に応じて自動調整（基準 640x480 で 2000）。
        """
        if self.min_area is not None:
            return self.min_area
        h, w = frame.shape[:2]
        ref_area = 640 * 480
        return max(500, int(2000 * (w * h) / ref_area))

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
        min_area = self._get_min_area(image)
        detected_notes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                roi = image[y:y+h, x:x+w]
                if roi.size > 0:
                    detected_notes.append({
                        'image': roi,
                        'x': x, 'y': y, 'w': w, 'h': h
                    })
        return detected_notes

    def _is_processing_analysis(self):
        """解析中かどうか（メインスレッドがUI表示に使用）。排他制御付き。"""
        with self._processing_lock:
            return self._is_processing

    def _worker_loop(self):
        """
        ワーカースレッド：RequestQueue を監視し、キューに画像が入ったら
        OCR -> API 送信などの重い処理を実行する。
        """
        while not self._worker_stop.is_set():
            try:
                item = self._request_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                break
            note_obj, roi_image, x, y, w, h, frame_shape = item
            with self._processing_lock:
                self._is_processing = True
            try:
                self.upload_note(note_obj, roi_image, x, y, w, h, frame_shape)
            finally:
                with self._processing_lock:
                    self._is_processing = False
            self._request_queue.task_done()

    def _build_preview_layers(self, original_frame):
        """
        2層構造を構築する。
        - データ用: 元解像度（または射影変換後）のフレーム。OCR用切り出し・座標計算のベース。
        - 表示・調整用: 幅 PREVIEW_WIDTH にリサイズした軽量フレーム。HSVプレビュー・描画用。
        Returns: (work_frame, full_res_frame, scale_x, scale_y)
        """
        h_orig, w_orig = original_frame.shape[:2]
        scale_resize = w_orig / PREVIEW_WIDTH
        preview_h = int(h_orig / scale_resize)
        preview_frame = cv2.resize(original_frame, (PREVIEW_WIDTH, preview_h))

        if self.homography_matrix is not None:
            warped_original = cv2.warpPerspective(
                original_frame, self.homography_matrix,
                (self.target_width, self.target_height)
            )
            warped_preview_h = int(self.target_height * PREVIEW_WIDTH / self.target_width)
            work_frame = cv2.resize(warped_original, (PREVIEW_WIDTH, warped_preview_h))
            full_res_frame = warped_original
            scale_x = full_res_frame.shape[1] / work_frame.shape[1]
            scale_y = full_res_frame.shape[0] / work_frame.shape[0]
        else:
            work_frame = preview_frame.copy()
            full_res_frame = original_frame
            scale_x = w_orig / work_frame.shape[1]
            scale_y = h_orig / work_frame.shape[0]

        return work_frame, full_res_frame, scale_x, scale_y

    def detect_and_track(self, original_frame):
        """
        フレームごとの検知とトラッキング処理。
        表示・調整は軽量フレーム（Preview）で行い、OCR用切り出しは元解像度（Full Res）から行う。
        """
        # 1. 2層構造を構築（軽量フレーム + 元解像度フレーム）
        work_frame, full_res_frame, scale_x, scale_y = self._build_preview_layers(original_frame)

        # 2. 軽量フレーム上でHSV・マスク・輪郭検出（パフォーマンス改善）
        hsv = cv2.cvtColor(work_frame, cv2.COLOR_BGR2HSV)
        lower_bound = np.array([self.h_min, self.s_min, self.v_min])
        upper_bound = np.array([self.h_max, self.s_max, self.v_max])
        mask = cv2.inRange(hsv, lower_bound, upper_bound)

        kernel = np.ones((5, 5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        min_area = self._get_min_area(work_frame)

        # 3. 現在のフレームでの検知リスト作成（座標は軽量フレーム上）
        current_detections = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_area:
                x, y, w, h = cv2.boundingRect(contour)
                center_x = x + w / 2
                center_y = y + h / 2
                current_detections.append({'x': x, 'y': y, 'w': w, 'h': h, 'cx': center_x, 'cy': center_y, 'contour': contour})

        # 4. トラッキング処理（既存の付箋と紐付け）。描画は軽量フレーム上。
        current_time = time.time()
        matched_indices = set()

        for note in self.tracked_notes:
            min_dist = float('inf')
            match_idx = -1

            for i, detection in enumerate(current_detections):
                if i in matched_indices:
                    continue
                dist = math.sqrt((note.center_x - detection['cx'])**2 + (note.center_y - detection['cy'])**2)
                if dist < min_dist:
                    min_dist = dist
                    match_idx = i

            if match_idx != -1 and min_dist < self.TRACKING_DISTANCE_THRESHOLD:
                det = current_detections[match_idx]
                note.center_x = det['cx']
                note.center_y = det['cy']
                note.w = det['w']
                note.h = det['h']
                note.last_seen = current_time
                note.stable_counter = min(note.stable_counter + 1, 100)
                matched_indices.add(match_idx)

                cv2.rectangle(work_frame, (det['x'], det['y']), (det['x'] + det['w'], det['y'] + det['h']), (0, 255, 0), 2)
                cv2.putText(work_frame, f"ID:{note.id}", (det['x'], det['y'] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                # アップロード時：解析中でなければキューに投入するだけ（非同期、待機しない）
                # 同一付箋の連続投入を防ぐため、投入直後に last_upload を更新する
                if note.stable_counter >= self.STABLE_THRESHOLD and (current_time - note.last_upload > self.UPLOAD_INTERVAL):
                    if not self._is_processing_analysis():
                        ox = int(det['x'] * scale_x)
                        oy = int(det['y'] * scale_y)
                        ow = int(det['w'] * scale_x)
                        oh = int(det['h'] * scale_y)
                        if ow > 0 and oh > 0:
                            roi = full_res_frame[oy:oy+oh, ox:ox+ow]
                            if roi.size > 0:
                                self._request_queue.put((
                                    note, roi.copy(), ox, oy, ow, oh, full_res_frame.shape
                                ))
                                note.last_upload = current_time  # クールダウン開始（同じ付箋の連続投入防止）

        for i, detection in enumerate(current_detections):
            if i not in matched_indices:
                new_id = f"cam-{int(time.time() * 1000)}-{i}"
                new_note = TrackedNote(new_id, detection['cx'], detection['cy'], detection['w'], detection['h'])
                self.tracked_notes.append(new_note)
                cv2.rectangle(work_frame, (detection['x'], detection['y']), (detection['x'] + detection['w'], detection['y'] + detection['h']), (0, 255, 255), 2)

        self.tracked_notes = [n for n in self.tracked_notes if current_time - n.last_seen < self.DELETE_TIMEOUT]

        info_text = [
            f"Board: {self.BOARD_ID}",
            f"H: {self.h_min}-{self.h_max}",
            f"S: {self.s_min}-{self.s_max}",
            f"V: {self.v_min}-{self.v_max}",
            "[S]ave Config"
        ]
        for i, text in enumerate(info_text):
            cv2.putText(work_frame, text, (10, 30 + i * 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        return work_frame, mask

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
        # RTSP URL の場合は文字列で開く、Webカメラの場合は 0 + CAP_DSHOW
        if isinstance(self.camera_source, str):
            cap = cv2.VideoCapture(self.camera_source)
            print(f"Camera: RTSP URL (RTSP_URL from .env)")
            # RTSP のストリームタイムアウトを延長（OpenCV が対応している場合）
            try:
                cap_open_timeout = getattr(cv2, "CAP_PROP_OPEN_TIMEOUT_MSEC", 37)
                cap.set(cap_open_timeout, 60000)  # 60秒
            except Exception:
                pass
        else:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            print("Camera: Web camera (ID 0)")
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

        # ワーカースレッド起動（解析処理を非同期で実行）
        worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        worker_thread.start()

        while True:
            ret, original_frame = cap.read()
            if not ret:
                break

            # 元解像度を保持（mouse_callbackでのスケールバック用）
            self._last_original_height, self._last_original_width = original_frame.shape[:2]

            self.h_min = cv2.getTrackbarPos('Hue Min', 'Sticky Note Detector')
            self.h_max = cv2.getTrackbarPos('Hue Max', 'Sticky Note Detector')
            self.s_min = cv2.getTrackbarPos('Sat Min', 'Sticky Note Detector')
            self.s_max = cv2.getTrackbarPos('Sat Max', 'Sticky Note Detector')
            self.v_min = cv2.getTrackbarPos('Val Min', 'Sticky Note Detector')
            self.v_max = cv2.getTrackbarPos('Val Max', 'Sticky Note Detector')

            # 表示用は軽量フレーム（Preview）で処理し、imshow も軽量フレームのみ
            processed_frame, mask = self.detect_and_track(original_frame)
            self._last_preview_height, self._last_preview_width = processed_frame.shape[:2]

            # 解析中ステータス表示（ワーカーが処理中は画面隅に表示）
            if self._is_processing_analysis():
                cv2.putText(
                    processed_frame, "解析中...",
                    (processed_frame.shape[1] - 150, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2
                )

            # キャリブレーション点描画（保存座標は元解像度のため、表示用にプレビュー座標へ変換）
            if self.is_calibrating and self._last_original_width and self._last_original_height:
                for pt in self.calibration_points:
                    px = int(pt[0] * self._last_preview_width / self._last_original_width)
                    py = int(pt[1] * self._last_preview_height / self._last_original_height)
                    cv2.circle(processed_frame, (px, py), 5, (0, 0, 255), -1)

            cv2.imshow('Sticky Note Detector', processed_frame)
            cv2.imshow('Mask Debug', mask)

            key = cv2.waitKey(1) & 0xFF

            # キー操作による微調整
            if key == ord('q'):
                self._worker_stop.set()
                self._request_queue.put(None)
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

        worker_thread.join(timeout=2.0)
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = StickyNoteDetector()
    detector.run()
