# AIvtuber受付システム

WonderLink株式会社のAIvtuber「ワンダーリン子」による受付システムです。

## 機能

### Reception Mode (受付モード)
- カメラ検知による自動挨拶
- Gemini APIによる動的な挨拶文生成
- Edge TTSによる音声合成
- VMagicMirrorとのOSC連携（表情・リップシンク）
- 初回起動時の自己紹介

### Live Mode (リアルタイム対話モード)
- Gemini Liveによる音声・映像でのリアルタイム対話
- カメラモードと画面共有モードの選択可能
- 音声トリガー「リン子さん」でReception ModeからLive Modeへ自動切り替え

## セットアップ

### 1. 環境要件
- Python 3.13+
- Windows OS (winsound, mss対応)
- マイク・スピーカー
- Webカメラ (オプション)

### 2. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定
`.env`ファイルを作成し、以下を設定:
```
SQS_QUEUE_URL=your_sqs_queue_url
GEMINI_API_KEY=your_gemini_api_key
AWS_PROFILE=your_aws_profile_name
```

### 4. VMagicMirrorの設定
1. VMagicMirrorを起動
2. VMC Protocolタブを開く
3. 「VMCPによる受信を有効化」にチェック
4. ポート: `39539`
5. 「上半身」「手」「足・腰」「表情」すべてにチェック
6. 「変更を適用」をクリック

## 使い方

### 起動
```bash
python main_controller.py
```

### モード切り替え
- **Reception → Live**: Enterキーを押す、または「リン子さん」と呼びかける
- **Live → Reception**: 自動的に戻る (180秒後、またはセッション終了時)
- **終了**: `q`を入力してEnter

### ビデオモード選択 (Live Mode時)
- `1`: カメラモード (Webカメラ映像を送信)
- `2`: 画面共有モード (デスクトップ画面を送信)

## ファイル構成

### メインファイル
- `main_controller.py`: アプリケーションのメインコントローラー
- `local_processor.py`: Reception Mode処理 (SQS, 音声合成, OSC)
- `live_session.py`: Live Mode処理 (Gemini Live API)

### 設定ファイル
- `.env`: 環境変数 (Git管理外)
- `requirements.txt`: 依存パッケージ

### その他
- `archived/`: 過去のテストファイル・スクリプト

## 技術スタック
- **音声合成**: Edge TTS (Microsoft)
- **AI**: Gemini API (Google)
- **AWS**: SQS (メッセージキュー)
- **3Dモデル連携**: VMagicMirror (VMC Protocol / OSC)
- **音声認識**: Google Speech Recognition

## ライセンス
WonderLink株式会社

## 作者
WonderLink株式会社
