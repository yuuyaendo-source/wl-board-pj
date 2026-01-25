# AI-Board Project

アナログとデジタルを融合させた次世代オフィス空間OS「AI-Board」のプロトタイプシステムです。
Webアプリ上のデジタル付箋と、カメラで検知したアナログ付箋をリアルタイムに同期し、AIアバターが会議をファシリテートします。

## システム構成

本プロジェクトは以下のコンポーネントで構成されています。

1.  **Webアプリ (Postit Board)**
    *   **パス**: `02_1_App_postit_board/src`
    *   **技術**: Next.js, Express, Socket.IO
    *   **ポート**: 3000
    *   **機能**: 付箋の作成・編集・移動、リアルタイム同期、AIサーバーへの通知。

2.  **AIサーバー (AI-Board Backend)**
    *   **パス**: `02_2_AI-Board`
    *   **技術**: Python (Flask), Gemini API, VOICEVOX, Python-OSC
    *   **ポート**: 5000
    *   **機能**:
        *   画像からのテキスト抽出 (Gemini 2.5 Flash Lite)。
        *   付箋内容に対するコメント生成と感情分析。
        *   音声合成 (VOICEVOX)。
        *   アバター制御信号 (OSC) の送信。

3.  **カメラ検知モジュール**
    *   **スクリプト**: `02_2_AI-Board/src/sticky_note_detector.py`
    *   **技術**: OpenCV
    *   **機能**: Webカメラ映像から黄色い付箋を検知し、画像を切り出してAIサーバーへ送信。

4.  **アバター表示 (外部連携)**
    *   **ソフトウェア**: VMagicMirror
    *   **連携**: VMC Protocol (OSC Port 9000)
    *   **機能**: AIの感情に合わせて表情やモーションを変化させる。

## 前提条件

*   **OS**: Windows 10/11 (推奨)
*   **Node.js**: v18以上
*   **Python**: v3.10以上
*   **VOICEVOX**: アプリ版またはDocker版が起動していること (デフォルト: `http://localhost:50021`)
*   **VMagicMirror**: インストール済みであること
*   **Webカメラ**: 接続済みであること

## セットアップ

### 1. 環境変数の設定

`02_2_AI-Board/.env` ファイルを作成し、以下の内容を設定してください。

```env
GEMINI_API_KEY=your_gemini_api_key_here
VOICEVOX_URL=http://localhost:50021
VOICEVOX_SPEAKER_ID=3
```

### 2. 依存関係のインストール

**Webアプリ:**
```powershell
cd 02_1_App_postit_board/src
npm install
```

**AIサーバー:**
```powershell
cd 02_2_AI-Board
# 仮想環境を作成・有効化することを推奨
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 起動方法

### 1. サーバーの一括起動 (推奨)

プロジェクトルート (`02_Projects`) にある起動スクリプトを使用します。

```powershell
.\start_all_servers.ps1
```

これにより、Webアプリ (ポート3000) と AIサーバー (ポート5000) が別ウィンドウで起動します。

### 2. カメラ検知の起動

アナログ付箋を認識させる場合は、別途以下のスクリプトを実行します。

```powershell
cd 02_2_AI-Board
# 仮想環境有効化後
python src/sticky_note_detector.py
```

### 3. VOICEVOXとVMagicMirrorの準備

*   **VOICEVOX**: 起動しておく。
*   **VMagicMirror**:
    *   設定画面を開く。
    *   「Ex. Tracker」タブ（または配信タブ）で **「OSC受信を有効にする」** をONにする。
    *   ポート番号が **9000** であることを確認する。
    *   リップシンク設定で、PCの音声を拾うようにマイク入力（ステレオミキサー等）を設定する。

## 使い方

1.  **Webアプリで付箋を追加**:
    *   ブラウザで `http://localhost:3000` にアクセス。
    *   「＋付箋」ボタンからテキストを入力して作成。
    *   AI（リン子）が内容に反応してコメントし、アバターが動きます。

2.  **アナログ付箋を追加**:
    *   Webカメラに向けて黄色い付箋を映す。
    *   検知されると自動的に撮影・テキスト化され、Webアプリ上のボードに反映されます。
    *   同様にAIが反応します。

## ディレクトリ構成

```
02_Projects/
├── 02_1_App_postit_board/   # Webアプリ (Frontend/Backend)
├── 02_2_AI-Board/           # AI処理・カメラ検知 (Python)
├── start_all_servers.ps1    # 一括起動スクリプト
├── check_ports.ps1          # ポート確認スクリプト
└── README.md                # 本ファイル
```
