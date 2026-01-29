# 02_2_AI-Board

AI-Board のバックエンド・付箋検知・AIアバター制御を担う Python プロジェクトです。

---

## 概要

| 項目 | 内容 |
|------|------|
| **役割** | 付箋画像の OCR、コメント・感情生成（Gemini）、音声合成（VOICEVOX）、アバター制御（OSC）。カメラ／RTSP による付箋検知。 |
| **技術** | Python 3.10+, Flask, Flask-SocketIO, OpenCV, Gemini API（google-genai / google-generativeai）, VOICEVOX, Python-OSC |
| **ポート** | 5000（Web API）。付箋検知は別プロセスで実行。 |

---

## フォルダ構成

```
02_2_AI-Board/
├── .env              # 環境変数（GEMINI_API_KEY, RTSP_URL 等）※ .gitignore 対象
├── .env.example      # 環境変数の例
├── requirements.txt  # Python 依存関係
├── README.md         # 本ファイル
├── start_server.ps1  # AIサーバー（Flask）起動用スクリプト
├── start_voicevox.ps1
└── src/
    ├── config.json       # ボードID・HSV・キャリブレーション等（実行時に更新）
    ├── sticky_note_detector.py  # 付箋検知（カメラ/RTSP → 検出・OCR・API送信）
    └── webapp/
        ├── app.py        # Flask メイン（REST API, Socket.IO）
        ├── ai_avatar.py  # Gemini / VOICEVOX / OSC 連携
        └── templates/
            └── index.html
```

---

## 実装状況・技術・機能

### 1. AIサーバー（Flask / `src/webapp/app.py`）

| 機能 | 説明 |
|------|------|
| **REST API** | 付箋画像のアップロード（`/api/upload`）、付箋データの受信（`/api/sticky_notes`）。Webアプリ（02_1）と連携。 |
| **Socket.IO** | コメント・音声ファイル情報をフロントへリアルタイム配信。 |
| **付箋の重複防止** | 既存IDの付箋は更新（`note-updated`）として扱い、新規のみ `note-added` で AI コメントをトリガー。 |

### 2. AIアバター（`src/webapp/ai_avatar.py`）

| 機能 | 説明 |
|------|------|
| **Gemini API** | 画像からのテキスト抽出（OCR）、付箋内容に基づくコメント・感情（Joy/Sorrow/Anger/Fun/Neutral）の生成。 |
| **SDK** | `google-genai` を優先。import に失敗した場合は `google-generativeai` にフォールバック（FutureWarning は出るが動作可能）。 |
| **VOICEVOX** | コメント文の音声合成（デフォルト http://localhost:50021）。話者 ID は `.env` の `VOICEVOX_SPEAKER_ID`。 |
| **OSC** | VMagicMirror へ感情パラメータを送信（127.0.0.1:9000）。Joy / Sorrow / Anger / Fun を 0/1 で制御。 |

### 3. 付箋検知（`src/sticky_note_detector.py`）

| 機能 | 説明 |
|------|------|
| **カメラソース** | `.env` の `RTSP_URL` が設定されていれば RTSP、未設定なら Webカメラ（ID 0）。RTSP は認証付き URL（`rtsp://user:pass@host:port/path`）を想定。 |
| **HSV 検出** | 黄色付箋を HSV でマスク。H 20–46, S 0–50, V 0–255 をデフォルトとし、`config.json` または画面上スライダーで変更可能。 |
| **キャリブレーション** | マウスで 4 点指定し射影変換（台形補正）。座標は `config.json` に保存。 |
| **2層フレーム** | データ用は元解像度、表示・スライダー用は幅 960px のプレビュー。軽量化のためプレビュー上で操作し、座標を元解像度にスケールバック。 |
| **min_area** | 付箋として認識する最小面積（ピクセル）。`.env` の `MIN_AREA` または `config.json` で指定。未設定時は解像度に応じて自動計算（基準 640×480 で 2000 など）。 |
| **非同期解析** | メインスレッドは描画・UI、ワーカーがキューで OCR → API 送信。解析中は「解析中...」表示と排他制御で同一付箋の連続送信を防止。 |
| **重複防止** | キュー投入直後に `last_upload` を更新し、同一付箋の連続キュー投入を抑制。 |

### 4. 設定ファイル

| ファイル | 内容 |
|----------|------|
| **.env** | `GEMINI_API_KEY`, `VOICEVOX_URL`, `VOICEVOX_SPEAKER_ID`, `RTSP_URL`, `MIN_AREA`。詳細は `.env.example` を参照。 |
| **src/config.json** | `board_id`, HSV（h_min/h_max, s_min/s_max, v_min/v_max）, キャリブレーション 4 点、`min_area` 等。付箋検知の起動・キャリブレーション・保存で更新。 |

---

## セットアップ

### 前提

- Python 3.10 以上（3.14 では `google-genai` が未対応の可能性あり。その場合は `google-generativeai` にフォールバック）
- VOICEVOX 利用時は起動済み（デフォルト http://localhost:50021）
- アバター利用時は VMagicMirror 起動済み（OSC ポート 9000）

### 手順

1. **仮想環境と依存関係**

   ```powershell
   cd 02_2_AI-Board
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **環境変数**

   `.env.example` をコピーして `.env` を作成し、少なくとも `GEMINI_API_KEY` を設定。

   - RTSP カメラ: `RTSP_URL=rtsp://ユーザー名:パスワード@ホスト:ポート/ストリームパス`
   - 付箋の最小面積: `MIN_AREA=2000`（任意）

---

## 起動方法

### AIサーバー（Flask）のみ

```powershell
cd 02_2_AI-Board
.\.venv\Scripts\Activate.ps1
cd src\webapp
python app.py
```

- ブラウザ: http://localhost:5000  
- 一括起動では `02_Projects\start_all_servers.ps1` がこの手順を実行。

### 付箋検知（カメラ／RTSP）を動かす場合

1. 02_1（Webアプリ）と 02_2（本サーバー）を起動しておく。
2. 別ターミナルで付箋検知を起動:

   ```powershell
   cd 02_2_AI-Board
   .\.venv\Scripts\Activate.ps1
   cd src
   python sticky_note_detector.py
   ```

- ウィンドウでプレビュー・HSVスライダー・キャリブレーション（`c`）・設定保存（`S`）が可能。
- キー: `q` 終了, `c` キャリブレーション, `S` 設定保存。u/j, i/k, o/l, p/;, [/'], ]/\ で HSV を微調整。

---

## クイックリファレンス

| 項目 | 値 |
|------|-----|
| AIサーバーURL | http://localhost:5000 |
| 付箋検知の API 送信先 | http://localhost:3000/api/sticky_notes（02_1 が起動していること） |
| デフォルト HSV | H 20–46, S 0–50, V 0–255 |
| 設定保存 | 付箋検知ウィンドウで `S` → `src/config.json` に保存 |

---

## 既知の制限・注意

- **RTSP 401 Unauthorized**: URL にユーザー名・パスワードを含める（`rtsp://user:pass@host:port/path`）。
- **Stream timeout**: ネットワーク遅延やカメラ側の応答が遅いと 30 秒程度でタイムアウトすることがある。接続後は `CAP_PROP_OPEN_TIMEOUT_MSEC` を 60 秒に延長する処理を入れているが、読み取り側のタイムアウトは環境により変動する。
- **google-genai**: Python 3.14 や一部環境では未対応のため、その場合は `google-generativeai` にフォールバックし、FutureWarning が表示される。
