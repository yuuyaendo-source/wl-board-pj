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
    *   **スマホ連携**: `/mobile/upload` ページからスマホで撮影した付箋画像をアップロード可能。

2.  **AIサーバー (AI-Board Backend)**
    *   **パス**: `02_2_AI-Board`
    *   **技術**: Python (Flask), Gemini API, VOICEVOX, Python-OSC
    *   **ポート**: 5000
    *   **機能**:
        *   画像からのテキスト抽出 (Gemini 2.0 Flash Lite Preview)。
        *   付箋内容に対するコメント生成と感情分析。
        *   音声合成 (VOICEVOX)。
        *   アバター制御信号 (OSC) の送信。

3.  **カメラ検知モジュール**
    *   **スクリプト**: `02_2_AI-Board/src/sticky_note_detector.py`
    *   **技術**: OpenCV
    *   **機能**: Webカメラ映像から黄色い付箋を検知し、画像を切り出してAIサーバーへ送信。
    *   **補正**: 4点クリックによる射影変換（台形補正）機能付き。

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
*   **Webカメラ**: 接続済みであること (PCで実行する場合)

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

### 1. 事前準備 (必須)

以下の外部アプリケーションを先に起動しておいてください。

*   **VOICEVOX**: 音声合成に必要です。起動していないとAIの発話が行われません。
*   **VMagicMirror**: アバター表示に必要です。
    *   設定画面 > 「Ex. Tracker」タブ（または配信タブ）で **「OSC受信を有効にする」** をON。
    *   ポート番号が **9000** であることを確認。
    *   リップシンク設定で、PCの音声を拾うようにマイク入力（ステレオミキサー等）を設定。

### 2. サーバーの一括起動 (推奨)

プロジェクトルート (`02_Projects`) にある起動スクリプトを使用します。

```powershell
.\start_all_servers.ps1
```

これにより、Webアプリ (ポート3000) と AIサーバー (ポート5000) が別ウィンドウで起動します。

### 3. Webカメラ検知の起動 (オプション)

PCに接続したWebカメラでアナログ付箋を認識させる場合は、別途以下のスクリプトを実行します。

```powershell
cd 02_2_AI-Board
# 仮想環境有効化後
python src/sticky_note_detector.py
```

**操作方法:**
*   **キャリブレーション**: `c` キーを押した後、画面上の4点（左上、右上、右下、左下）をクリックして検知範囲を指定します。
*   **設定保存**: `S` (Shift+s) キーで現在のHSV設定等を保存します。
*   **終了**: `q` キー。

## 使い方

1.  **Webアプリで付箋を追加**:
    *   ブラウザで `http://localhost:3000` にアクセス。
    *   「＋付箋」ボタンからテキストを入力して作成。
    *   AI（リン子）が内容に反応してコメントし、アバターが動きます。

2.  **スマホから付箋を追加**:
    *   スマホで `http://<PCのIPアドレス>:3000/mobile/upload` にアクセス。
    *   「カメラを起動」ボタンで付箋を撮影してアップロード。
    *   自動的に付箋が切り出され、テキスト化されてボードに追加されます。

3.  **アナログ付箋を追加 (Webカメラ)**:
    *   `sticky_note_detector.py` を起動した状態で、Webカメラに向けて黄色い付箋を映す。
    *   安定して検知されると自動的に撮影・テキスト化され、Webアプリ上のボードに反映されます。

## ディレクトリ構成

```
02_Projects/
├── 02_1_App_postit_board/   # Webアプリ (Frontend/Backend)
├── 02_2_AI-Board/           # AI処理・カメラ検知 (Python)
├── start_all_servers.ps1    # 一括起動スクリプト
├── check_ports.ps1          # ポート確認スクリプト
└── README.md                # 本ファイル
```
