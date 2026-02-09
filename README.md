# wlinko-pj (Wonder Link Project)

浅川研究室のプロジェクト群です。AI、Web技術、そしてアバターインタラクションを組み合わせた実験的なアプリケーションを含みます。

## 📁 プロジェクト構成

| ディレクトリ / ファイル | 説明 |
|------------------------|------|
| **02_1_App_postit_board** | 付箋掲示用Webアプリ（Next.js + Express + Socket.IO）。ポート3000で動作。AI-Board 連携用ボードへのリンクあり。 |
| **02_2_AI-Board** | **[メイン]** AI搭載デジタルボード（Flask + Socket.IO）。ポート5000。HTTPS・3モード（AI-Board / Reception / Personal）・受付画面 (`/operator`)・名前・顔管理 (`/manager`) 対応。 |
| **docs** | 共通ドキュメント。`改善議論.md`（音声・双方向設計）、`改善指示書6.md`（要件一覧）、`次の実装プラン.md`（優先順位）、`レセプション_トラッキング_切り分け.md`、`パーソナル_名前顔管理_設計.md` など。 |
| **scripts** | `allow_firewall_port_3000.ps1`（付箋ボード）、`allow_firewall_port_5000.ps1`（AI-Board）— CATO/遠隔アクセス用にファイアウォールでポート許可（管理者実行）。 |
| **start_all_servers.ps1** | 付箋ボード・AI-Board を一括起動。CATO 接続PCからは **http://172.16.1.251:3000** / **http://172.16.1.251:5000** でアクセス可能。 |
| **docs/開発ドキュメント/開発環境_CATO.md** | CATO ネットワークでの開発環境（localhost = 172.16.1.251）の説明。 |

---

# 🤖 02_2_AI-Board

物理的な付箋とデジタルアバターが融合した、インタラクティブな掲示板システムです。
カメラで検出した付箋に対して、AIキャラクター（Wonder Link-ko / リン子）がリアクションし、コメントを読み上げます。

## ✨ 主な機能

1.  **リアルタイム付箋同期**
    *   Webカメラで付箋を検出し、デジタルボード上にリアルタイム反映。
    *   `StickyNoteDetector` (OpenCV) による画像認識。
2.  **AIインタラクション**
    *   **画像認識 & テキスト生成**: Google Gemini API を使用して付箋の内容を理解し、コメントを生成。
    *   **音声合成**: VOICEVOX を使用してコメントを読み上げ。感情タグ（例: `[Anger]`）は自動除去され、自然な発話が可能。
    *   **感情表現**: AIが `[JOY]`, `[ANGRY]` などの感情タグを出力し、アバターの表情や声に反映。
3.  **3Dアバター (VRM)**
    *   Webブラウザ上で動作する3Dキャラクター (`@pixiv/three-vrm`, `Three.js`)。
    *   **リップシンク**: ブラウザの `AudioContext` を用いて、音声波形に合わせて口パクを自動生成。
    *   **自律動作 (Autonomous)**: 呼吸、ランダムな視線移動、発話時の手振りなどを自動で行い、生き生きとした存在感を表現。
    *   **フルコントロール**: 位置 (X/Y/Z)、回転 (Rot Y)、スケール、表示枠 (Window Scale/Pos) をGUIで自由に変更可能。
    *   **3モード切替**: **AI-Board**（自律）・**Reception**（オペレーターのトラッキング）・**Personal**（自動切替＝人検知、または任意切替＝名前・顔照合）。

## 🛠 技術スタック

### Backend (Python)
*   **Framework**: Flask, Flask-SocketIO
*   **AI/ML**: Google Generative AI (Gemini), OpenCV (CV2), NumPy
*   **Audio**: VOICEVOX (HTTP API経由)

### Frontend (Web)
*   **Core**: HTML5, CSS3, JavaScript (ES Modules)
*   **3D/Avatar**: Three.js (r170), @pixiv/three-vrm (v3)
*   **Real-time**: Socket.IO Client

## 🚀 セットアップ & 起動

### 必要要件
*   Python 3.10+
*   Node.js (for 02_1_App_postit_board)
*   VOICEVOX (別途起動が必要な場合あり、現状はHTTP API利用)
*   Google Gemini API Key (`.env` に記載)

### 起動方法
ルートディレクトリ (`wlinko-pj`) で以下のスクリプトを実行してください。

```powershell
.\start_all_servers.ps1
```

これにより、以下の2つのサーバーが起動します。
1.  **Web App (Postit)**: `http://localhost:3000` — トップから「付箋ボードを開く」で AI-Board 連携用ボード (`board_20260125`) を開く。
2.  **AI-Board**: `http://localhost:5000` または **HTTPS** (`https://localhost:5000`) — 証明書あり時は HTTPS。アバターはこちらで動作。

### 遠隔アクセス
*   AI-Board は `0.0.0.0` で待ち受け。別PCからは `https://<このPCのIP>:5000` でアクセス可能。
*   **主なURL**: ディスプレイ `https://<IP>:5000` / 受付オペレーター `https://<IP>:5000/operator` / **名前・顔の管理** `https://<IP>:5000/manager`（特定の管理者が利用）。
*   **HTTPS**: `02_2_AI-Board/src/webapp/generate_cert.py` で自己証明書を生成し、起動時に HTTPS で待ち受ける。
*   **ファイアウォール**: 遠隔から接続できない場合は、プロジェクトルートで `.\scripts\allow_firewall_port_5000.ps1` を**管理者PowerShell**で実行してポート5000を許可する。

## 🎮 アバター操作 (AI-Board)

`http://localhost:5000` にアクセス後、画面左下の **Avatar Settings** をクリックすると設定パネルが開きます。

*   **Visible**: 表示/非表示
*   **Scale / Pos X,Y,Z / Rot Y**: アバターの拡大縮小・位置・回転
*   **Win Scale / Win X,Y**: 表示ウィンドウのサイズ・位置
*   **自動切替のカメラ**: 「このPCのカメラ」または「ネットワークカメラ（エントランス用）」— 後者はサーバーの `/camera_stream`（RTSP または Webカメラ）を使用。
*   **自動でパーソナルに切替（人を検知）**: ON にすると、顔が約2秒映ったらパーソナルモードに自動切替。Chrome の Face Detector API が使えない環境では MediaPipe で検知を試行。

## 📝 現在の開発状況 (2026/02 時点)

*   ✅ **Phase 1: 基本機能** (完了)
    *   付箋検出～AI回答～音声再生～リップシンクの一連フロー
    *   アバター表示・操作UI (位置・回転・サイズ・枠)、自律動作（視線・呼吸・発話ジェスチャー）
*   ✅ **付箋ボード連携表示** (完了)
    *   表示数 10〜25 で変更可能。全件取得ボタンでボードから付箋を再取得。ローテーション表示・新しい付箋を大きく・フェードアウト。リン子のコメント・音声は付箋受信時に必ず通知（VOICEVOX 未起動時はテキストのみ）。
*   ✅ **Phase 2A: Receptionモード** (実装済み)
    *   **受付オペレーター** (`/operator`): MediaPipe Holistic + Kalidokit でトラッキング、Socket.IO で `tracking_data` 送信
    *   ディスプレイ側で VRM にポーズ・表情を適用。遠隔アクセス（HTTPS・ファイアウォール許可）。Postit 連携。`docs/レセプション_トラッキング_切り分け.md` で不調時の手順を記載。
*   ✅ **パーソナルモード** (実装済み)
    *   **自動切替**: 設定で「自動でパーソナルに切替」ON 時、カメラで人（顔）を検知すると約2秒でパーソナルモードに切替。Chrome Face Detector API 非対応環境では MediaPipe で検知。
    *   **カメラソース**: 「このPCのカメラ」または「ネットワークカメラ（エントランス用）」— 後者はサーバー `/camera_stream`（`.env` の `RTSP_URL` または Webカメラ）を使用。
    *   **任意切替＋名前・顔照合**: Personal ボタン押下時、登録がある場合は名前を選択しカメラで顔を照合。一致時のみパーソナルモードに切替。
    *   **名前・顔の管理** (`/manager`): 特定の管理者が名前の追加・削除と各名前に対する顔の登録を行う。データは `face_registry_storage` 経由で保存（現状はローカル JSON、将来 S3 等へ移行可能）。`docs/パーソナル_名前顔管理_設計.md` 参照。
*   🚧 **今後の予定** (`docs/次の実装プラン.md` 参照)
    *   **受付モードのトラッキング調整**: ポーズ・表情のずれ修正、検出安定化。
    *   **Phase 2B: 音声統合**: WebRTC 双方向音声、リップシンク。
    *   **Phase 2C: UI改善**: 接続状態インジケーター、音声レベル・ミュート/音量。

### 既知の制限・注意
*   **Reception**: オペレーター側で MediaPipe が体を検出しないと `pose` が送られない。VRM の表情名は読み込み時にコンソール「VRM expressions: [...]」で確認可能。
*   **自動パーソナル切替**: SASE 等で Face Detector API が使えない場合は MediaPipe で検知を試行。CDN がブロックされていると「MediaPipe で検知できませんでした」となる。
*   **名前・顔照合**: 簡易的な画像類似度（グレースケール MSE）で照合。閾値は要調整の可能性あり。
