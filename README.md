# 02_Projects

**このREADMEは `02_Projects` フォルダ内の内容のみを説明します。**  
別の人や別のAIエージェントが、このフォルダだけを見て内容を把握できるように記載しています。

---

## このフォルダの目的

**AI-Board** のプロトタイプです。  
Web上のデジタル付箋ボードと、カメラで検知したアナログ付箋を同期し、AIアバターがコメント・音声・表情で会議をファシリテートするシステムです。

---

## フォルダ構成（02_Projects 内のみ）

```
02_Projects/
├── 02_1_App_postit_board/   # 付箋ボード Webアプリ（フロント＋API）
├── 02_2_AI-Board/           # AIサーバー・付箋OCR・音声・アバター制御
├── docs/                    # 改善指示書など（02_Projects 共通のドキュメント）
├── start_all_servers.ps1    # WebアプリとAIサーバーを一括起動するスクリプト
├── check_ports.ps1          # ポート 3000 / 5000 の使用状況を確認するスクリプト
├── サーバー起動手順.md       # 起動方法・トラブルシュート（詳細はここを参照）
└── README.md                # 本ファイル
```

---

## 含まれるプロジェクトの説明

### 02_1_App_postit_board（Webアプリ）

| 項目 | 内容 |
|------|------|
| **役割** | 付箋ボードのUIとAPI。付箋の作成・編集・移動、リアルタイム同期、AIサーバーへの通知。 |
| **技術** | Next.js, Express, Socket.IO |
| **ポート** | 3000 |
| **実体** | アプリのソースは `02_1_App_postit_board/src` にあり、`package.json` で `npm run dev` により起動。 |
| **主な機能** | ボード画面、付箋操作、コメント一覧、スマホ用アップロードページ（`/mobile/upload`）。 |
| **詳細** | 各サブプロジェクトの詳細は `02_1_App_postit_board/` 内の README 等を参照。 |

### 02_2_AI-Board（AIサーバー）

| 項目 | 内容 |
|------|------|
| **役割** | 付箋画像のOCR、コメント生成・感情分析、音声合成（VOICEVOX）、アバター制御（OSC）。 |
| **技術** | Python (Flask), Gemini API, VOICEVOX, Python-OSC, OpenCV |
| **ポート** | 5000（Web API）。カメラ検知は別プロセスで実行。 |
| **実体** | `02_2_AI-Board/src/webapp/app.py` がメイン。一括起動時は `src/webapp` から `app.py` を実行。 |
| **主な機能** | 画像→テキスト抽出、付箋へのコメント生成、感情に応じた音声・OSC送信。Webカメラ用の付箋検知は `02_2_AI-Board/src/sticky_note_detector.py`。 |
| **外部依存** | VOICEVOX（音声）、VMagicMirror（アバター表示・OSC受信）。 |
| **詳細** | `02_2_AI-Board/` 内の README や `.env.example` を参照。 |

### docs/

02_Projects 全体に関わるドキュメント（改善指示書など）を格納するフォルダです。

### ルートのスクリプト・ドキュメント

| ファイル | 説明 |
|----------|------|
| **start_all_servers.ps1** | 02_1 の Webアプリ（ポート3000）と 02_2 の AIサーバー（ポート5000）を別ウィンドウで起動する。実行場所は `02_Projects` フォルダ。 |
| **check_ports.ps1** | ポート 3000 と 5000 が使用中かどうかを表示する。起動前に実行して競合を確認できる。 |
| **サーバー起動手順.md** | 起動方法（一括・個別）、アクセスURL、ポート確認・依存関係・環境変数などのトラブルシュートを記載。 |

---

## システムの動き（02_1 と 02_2 の関係）

1. **02_1（Webアプリ）** がブラウザで付箋ボードを表示し、ユーザー操作や付箋データを管理する。
2. 付箋の追加・更新時に **02_2（AIサーバー）** にリクエストが送られ、AIがコメントと感情を返す。
3. 02_2 は VOICEVOX で音声を合成し、VMagicMirror に OSC で表情・モーションを送る。
4. スマホからは `http://<PCのIP>:3000/mobile/upload` で付箋画像をアップロードでき、02_2 が画像を処理してボードに反映する。
5. Webカメラでアナログ付箋を認識する場合は、別途 `02_2_AI-Board/src/sticky_note_detector.py` を実行する。

---

## クイックリファレンス（このフォルダ内で完結）

- **一括起動（PowerShell、02_Projects がカレント）**: `.\start_all_servers.ps1`
- **ポート確認**: `.\check_ports.ps1`
- **WebアプリURL**: http://localhost:3000
- **AIサーバーURL**: http://localhost:5000
- **環境変数**: `02_2_AI-Board/.env` に `GEMINI_API_KEY`, `VOICEVOX_URL` 等を設定（`02_2_AI-Board/.env.example` を参照）
- **詳細な起動手順・トラブルシュート**: `サーバー起動手順.md` を参照

---

## 前提条件（AI-Board を動かす場合）

- OS: Windows 10/11 を想定
- Node.js: v18 以上（02_1 用）
- Python: v3.10 以上（02_2 用）
- VOICEVOX: 起動済み（デフォルト http://localhost:50021）
- VMagicMirror: インストール・起動済み（OSC ポート 9000）
- Webカメラ: 付箋検知を使う場合のみ必要

以上が、**02_Projects フォルダ内に含まれる内容の説明**です。
