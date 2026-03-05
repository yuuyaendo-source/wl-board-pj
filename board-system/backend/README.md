# Board System Backend (Wonder Rinko)

4ボード（Main / Task / Personal / Morning）用の FastAPI バックエンド。  
SQLite（開発）を async SQLAlchemy + aiosqlite で利用。本番は PostgreSQL + asyncpg。`DATABASE_URL` の変更のみで移行可能。

## 技術スタック

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0（非同期）
- **DB ドライバ**: aiosqlite（SQLite）。本番は `postgresql+asyncpg`
- **設定**: pydantic-settings + .env
- **AI（フェーズ3）**: Ollama（ローカル LLM）による自動仕分け・マトリクススコア・日次リセット
- **Google カレンダー連携**: OAuth 2.0（google-auth-oauthlib + google-api-python-client）でパーソナルの「今日の予定」を取得

## セットアップ

```bash
cd board-system/backend
python -m venv .venv
.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
cp .env.example .env     # 必要に応じて編集
```

## 起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000
- ヘルス: http://localhost:8000/health

## ディレクトリ構成

```
backend/
├── alembic/
│   ├── versions/      # マイグレーションスクリプト
│   └── env.py         # 非同期対応
├── app/
│   ├── ai/            # Rinko Core（client, triage, matrix, daily_reset）
│   ├── config.py      # 設定（DATABASE_URL, OLLAMA_URL, Google OAuth 等）
│   ├── db.py          # 非同期エンジン・セッション・Base
│   ├── main.py        # FastAPI アプリ
│   ├── models/        # User, UserFace, StickyNote, BoardPlacement, PersonalSummaryCache, OAuthPkceState, UserGoogleToken
│   ├── routers/       # users, sticky_notes, boards, board_placements, daily_reset, personal, auth_google
│   ├── schemas/       # Pydantic スキーマ
│   └── services/      # orchestrator（AI 自動振り分けオーケストレーター）
├── desktop_app_releases/  # デスクトップアプリ自動更新用（latest.json + MSI）
├── scripts/       # migrate_sqlite_to_pg.py, seed_personal_members.py
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

## マイグレーション

```bash
alembic upgrade head   # 最新まで適用
alembic revision --autogenerate -m "説明"   # 変更から新規リビジョン生成
```

## API（実装済み）

### コア API

| 種別 | メソッド | パス | 説明 |
|------|----------|------|------|
| 死活 | GET | `/health` | ヘルスチェック |
| users | GET | `/users` | ユーザー一覧 |
| | POST | `/users` | ユーザー作成（email 一意） |
| | GET | `/users/by-email?email=` | メールでユーザー検索（デスクトップログイン・ Linko 解決用） |
| | GET | `/users/{id}` | ユーザー1件取得 |
| | PATCH | `/users/{id}` | ユーザー更新 |
| | DELETE | `/users/{id}` | ユーザー削除（パーソナル付箋をタスクへリリース後削除） |
| 顔画像 | GET | `/users/{id}/faces` | 顔画像一覧 |
| | POST | `/users/{id}/faces` | 顔画像追加（JSON base64 / multipart 両対応） |
| | GET | `/users/{id}/faces/{face_id}/image` | 顔画像取得 |
| | DELETE | `/users/{id}/faces/{face_id}` | 顔画像削除 |
| sticky_notes | GET | `/sticky_notes` | 付箋一覧 |
| | POST | `/sticky_notes` | 付箋作成（Main Board に配置、AI で Task/Personal にも自動配置） |
| | POST | `/sticky_notes/import_from_postit` | 付箋ボードから一括取り込み（重複スキップ、AI 自動振り分け） |
| | POST | `/sticky_notes/personal` | パーソナルボードに直接投稿（create + move_to_personal を1トランザクションで） |
| | POST | `/sticky_notes/sync_from_postit` | 付箋ボードで追記された内容を同期 |
| | GET | `/sticky_notes/{id}` | 付箋1件取得 |
| | PATCH | `/sticky_notes/{id}` | 付箋更新（付箋ボード連携時は双方に反映） |
| | DELETE | `/sticky_notes/{id}` | 付箋削除（付箋ボード連携時はグレー化） |
| | DELETE | `/sticky_notes/by_postit?board_id=&note_id=` | 付箋ボード削除連携 |
| | POST | `/sticky_notes/{id}/move_to_personal` | Personal に配置（body: `owner_id`, `lane`） |
| | POST | `/sticky_notes/{id}/release_to_task_board` | Task Board に配置 |
| board_placements | GET/POST | `/board_placements` | 一覧（`?board_type=&owner_id=`）・作成 |
| | GET/PATCH/DELETE | `/board_placements/{id}` | 1件取得・更新・削除 |

### ボード View API

| 種別 | メソッド | パス | 説明 |
|------|----------|------|------|
| boards | GET | `/boards/main` | Main ボード View |
| | GET | `/boards/task` | Task ボード View（5列。各配置に `taken_by`, `task_color` 付与） |
| | GET | `/boards/personal?owner_id=` | Personal ボード View（`is_from_task` 付与） |
| | GET | `/boards/morning` | Morning ボード View（MORNING 配置一覧） |
| daily_reset | GET | `/daily_reset/messages?owner_id=` | 朝会用「持ち越しますか？」メッセージ一覧（Logic 3） |
| | POST | `/daily_reset/sync_to_morning` | 全ユーザーの Personal Today を MORNING にコピー（cron 10:15 用） |

### パーソナルサマリ・カレンダー連携 API

| 種別 | メソッド | パス | 説明 |
|------|----------|------|------|
| personal | GET | `/api/personal/{person_id}/summary` | パーソナルサマリ取得（events + today）。linko-system 用 |
| | POST | `/api/personal/{person_id}/today` | Today 項目保存（カレンダーキーワード連携） |
| | POST | `/api/personal/{person_id}/events` | 今日の予定保存（Google カレンダー取得結果等） |
| auth | GET | `/auth/google?user_id=` | Google OAuth 開始（PKCE 対応、Google へリダイレクト） |
| | GET | `/auth/google/callback` | Google OAuth コールバック（トークン保存後 Personal へリダイレクト） |
| | POST | `/auth/google/refresh-calendar?user_id=` | Google カレンダーから今日の予定を再取得 |

- **Task ボード**: `matrix_quadrant` は 1=アイデア、2=短期タスク、3=長期タスク、4=重要、5=完了。レスポンスに `taken_by`（引き取り者 id/name/name_short）、`task_color`（yellow/green/grey/red）を付与。
- **Personal と Task の連動**: `PATCH /board_placements` で Personal の `lane` を DONE にすると、同一 note の TASK 配置の `matrix_quadrant` を 5（完了）に更新。DONE から INBOX/TODAY に戻すと TASK を 4（重要）に戻す。
- **Personal レーン**: INBOX、TODAY、DONE、HELP_REQUEST（応援要請）の 4 レーン。HELP_REQUEST にすると Task ボードでは付箋が赤色表示になる。
- **CORS**: 全オリジン許可（開発用）。本番では `allow_origins` を絞ること。

## AI Worker（Rinko Core）

`OLLAMA_URL` を .env に設定すると以下が有効になる。オーケストレーター（`services/orchestrator.py`）が Triage → Matrix Scoring → 配置を一貫で実行。

1. **Auto-Triage（Logic 1）**  
   `POST /sticky_notes` で Main に投稿すると、LLM が「タスクか情報か」「担当者明記か」を判定。  
   タスク → **Task Board** に配置し、緊急度・重要度をスコアリング（position_x/y, matrix_quadrant）。  
   担当者名あり → 該当ユーザー（`users.name` 部分一致）の **Personal Board Inbox** に配置。

2. **Matrix Scoring（Logic 2）**  
   Task Board に載せる際、LLM が緊急度・重要度を 0–100 で採点。  
   position_x = 緊急度、position_y = 重要度。matrix_quadrant は 1–4 で自動算出（5=完了は Personal DONE 連動で設定）。

3. **Daily Reset（Logic 3）**  
   `GET /daily_reset/messages?owner_id=` で、そのユーザーの Personal Today レーンの付箋について  
   「昨日の『〇〇』は持ち越しますか？」形式のメッセージを LLM で生成。

4. **Meeting スナップショット**  
   `POST /daily_reset/sync_to_morning` で全ユーザーの Personal Today を MORNING にコピー。既存 MORNING は削除してから作成。本番では cron で毎朝 10:15 に実行する想定。

- 環境変数: `OLLAMA_URL`（必須・例: http://172.16.1.251:11434/v1）、`OLLAMA_MODEL`（任意・既定: llama3.2）

## 本番（Ubuntu）: 起動とログ

- **ログはファイルに残さない**。確認時だけ別ターミナルで `tail -f` する想定。

### 起動（本番では --reload なし）

```bash
cd /path/to/board-system/backend
source .venv/bin/activate
# 別ターミナルで tail するため一時的に tee（ファイルは残さず /tmp でよい）
uvicorn app.main:app --host 0.0.0.0 --port 8000 2>&1 | tee /tmp/board-backend.log
```

- `/tmp` は再起動で消えるのでログを残さない運用に適している。必要なら `tail -f /tmp/board-backend.log` で追う。

### 別ターミナルでログを追う

```bash
tail -f /tmp/board-backend.log
```

- 直近から: `tail -n 100 -f /tmp/board-backend.log`
- `Ctrl+C` で終了（バックエンドは止まらない）

### systemd で運用する場合

- ログは **journald** に出るので、別ターミナルで `journalctl -u board-system-api -f` で追える（ユニット名は環境に合わせる）。
- 詳細は [docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md) を参照。

## 引き継ぎ・本番

- 本番デプロイ・運用: リポジトリルート [docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md) を参照。
- systemd で `board-system-api` として uvicorn を常時起動。SQLite の書き込み権限（backend ディレクトリの chown）と uvicorn パスの確認が必要な場合あり（同ドキュメントのトラブルシューティング参照）。
