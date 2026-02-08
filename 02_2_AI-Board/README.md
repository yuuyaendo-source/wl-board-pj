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

### 4. VRMアバター表示（画面右下）

| 項目 | 内容 |
|------|------|
| **表示** | `templates/index.html` で Three.js + @pixiv/three-vrm を CDN 読み込みし、画面右下に VRM アバター（バストアップ）を表示。 |
| **VRM ファイル** | `src/webapp/static/avatar.vrm` を配置すること。Webアプリ（02_1）の `public/avatar.vrm` をコピーして利用可能。 |

### 5. 設定ファイル

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
- 一括起動ではルートの `start_all_servers.ps1` がこの手順を実行。

### 遠隔アクセス（Receptionモード・受付オペレーター）

別のPCからこのサーバーへアクセスする場合:

1. **HTTPS を有効にする（推奨）**  
   カメラ・マイク利用のためブラウザは HTTPS を要求することがあります。  
   ```powershell
   cd 02_2_AI-Board\src\webapp
   python generate_cert.py
   ```
   その後 `app.py` を再起動すると `https://` で待ち受けます。

2. **Windows ファイアウォールでポート 5000 を許可**  
   遠隔から接続できない場合は、受信を許可してください。  
   ```powershell
   # プロジェクトルート (wlinko-pj) で、PowerShell を管理者として実行
   .\scripts\allow_firewall_port_5000.ps1
   ```

3. **接続URL**  
   起動時に表示される「Remote:」の URL を使います。  
   - ディスプレイ（エントランス）: `https://<このPCのIP>:5000`  
   - 受付オペレーター: `https://<このPCのIP>:5000/operator`  
   - **名前・顔の管理**（特定の人物が利用）: `https://<このPCのIP>:5000/manager`  
   証明書は自己署名のため、ブラウザで「詳細」→「安全でないサイトに進む」で進めてください。

4. **自動パーソナル切替のカメラソース（このPCのカメラ / ネットワークカメラ）**  
   - **このPCのカメラ**: そのブラウザが動いているPCのカメラ（getUserMedia）。SASE越しのPCで開いた場合はそのPCのカメラ。  
   - **ネットワークカメラ（エントランス用）**: サーバーが提供する `/camera_stream` の MJPEG ストリームを使用。サーバー側の `.env` で **`RTSP_URL`** が設定されていればそのネットワークカメラ（RTSP）、未設定ならサーバー機の Webカメラ (0)。エントランスにモニターを設置し、AI-Board で使っているネットワークカメラの映像で顔検知したい場合は、設定で「ネットワークカメラ（エントランス用）」を選び、サーバーで `RTSP_URL` を設定してください。

5. **自動パーソナル切替（人検知）を SASE／リモートで使う場合**  
   - **「このPCのカメラ」** を選んだとき: そのページを開いているブラウザが動いているPCのカメラを使います。SASE内の別PCから開いた場合はその別PCのカメラになります。  
   - **「ネットワークカメラ（エントランス用）」** を選んだとき: サーバーの `/camera_stream`（RTSP またはサーバー機の Webカメラ）を使うため、エントランスのモニターで開いていればネットワークカメラの映像で検知できます。  
   - **画面上の状態表示**：設定で「自動でパーソナルに切替（人を検知）」をONにすると、画面上部に「検知中」「カメラ取得失敗」「顔検知非対応」などのメッセージが出ます。SASE越しで動かない場合は、ここで原因を確認してください。  
   - **想定される原因**  
     - **顔検知非対応**：Chrome の Face Detector API が使えない環境（SASE/プロキシで制限、または Chrome 以外）では、自動的に **MediaPipe Face Detector**（CDN から読み込み）で検知を試行します。画面上に「MediaPipeで検知を準備中…」→「検知中」と出ればフォールバックが動作しています。SASE で CDN（jsdelivr.net / storage.googleapis.com）がブロックされている場合は「MediaPipe で検知できませんでした」と表示されます。  
     - **カメラ取得失敗**：そのPCでカメラ許可が出ていない、HTTPS で開いていない、SASE/ファイアウォールで `getUserMedia` やカメラがブロックされている。  
   - **エントランスの表示用PCで「このPCのカメラ」を使う場合**：表示用PCのブラウザで `https://<表示用PCのIP>:5000` を開き、そのPCのカメラで検知させてください。**「ネットワークカメラ」** を選べば、どこから開いてもサーバー側のカメラ（RTSP）で検知できます。

6. **名前・顔の管理（パーソナルモードの本人確認用）**  
   - **管理者**（特定の人物）が `https://<IP>:5000/manager` で名前の追加・削除と、各名前に対する「顔」の登録を行います。  
   - データは現状サーバー上の `src/webapp/data/face_registry.json` に保存されます。**将来的に S3 等のクラウドストレージへ移行可能**な設計（ストレージ抽象層）です。  
   - 詳細は `docs/パーソナル_名前顔管理_設計.md` を参照してください。

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
| 付箋検知の API 送信先 | 開発: http://localhost:3000/api/sticky_notes。本番: `POSTIT_BOARD_URL=http://wl-sticky-note.local` で http://wl-sticky-note.local/api/sticky_notes に送信。 |
| **Postit連携** | 本番連携先: **http://wl-sticky-note.local/board/wl**。`config.json` の `board_id` を `wl` にし、本番では環境変数 `POSTIT_BOARD_URL=http://wl-sticky-note.local` を設定する。 |
| デフォルト HSV | H 20–46, S 0–50, V 0–255 |
| 設定保存 | 付箋検知ウィンドウで `S` → `src/config.json` に保存 |

---

## 開発の進め方

- **本番の sticky-note**（http://wl-sticky-note.local/board/wl）**との連携を確認しながら**開発する。`board_id`: `wl`、`POSTIT_BOARD_URL=http://wl-sticky-note.local` で本番に送信し、付箋・AIコメント連携を検証する。
- 詳細は wl-sticky-note の **`docs/AI-Board・Desktopアプリの開発の進め方.md`** を参照。

---

## 既知の制限・注意

- **付箋・リン子が反応しない場合**: 付箋とAIコメントは **Socket.IO** でブラウザに届きます。AI-Board の画面（同じURLで開いたブラウザタブ）が **Socket接続済** である必要があります。画面下部の「Socket接続済」が緑で出ていれば受信できます。「Socket未接続」のときは、ブラウザのコンソール（F12）で `connect_error` が出ていないか確認し、AI-Board サーバの URL で開き直してください。付箋ボード側の `AI_BOARD_URL` は、その AI-Board サーバの URL（例: `http://172.16.1.251:5000`）にすること。
- **RTSP 401 Unauthorized**: URL にユーザー名・パスワードを含める（`rtsp://user:pass@host:port/path`）。
- **Stream timeout**: ネットワーク遅延やカメラ側の応答が遅いと 30 秒程度でタイムアウトすることがある。接続後は `CAP_PROP_OPEN_TIMEOUT_MSEC` を 60 秒に延長する処理を入れているが、読み取り側のタイムアウトは環境により変動する。
- **google-genai**: Python 3.14 や一部環境では未対応のため、その場合は `google-generativeai` にフォールバックし、FutureWarning が表示される。
