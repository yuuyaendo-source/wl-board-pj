# Board System Backend (Wonder Linko)

4ボード（Main / Task / Personal / Meeting）用の FastAPI 非同期バックエンド。  
開発は SQLite（aiosqlite）、**本番 Docker は PostgreSQL**（`postgresql+asyncpg`、`docker-compose.prod.yml` + `docker-compose.db.yml`）。

---

## 技術スタック

- **Framework**: FastAPI (Python 3.10+)
- **ORM**: SQLAlchemy 2.0（完全非同期）
- **DB ドライバ**: aiosqlite（SQLite） / asyncpg（PostgreSQL）
- **マイグレーション**: Alembic
- **セキュリティ・認証**: 簡易 JWT（管理者用）、`cryptography` / `sqlalchemy-utils`（Google OAuth トークンの AES-256 暗号化保存）
- **設定管理**: pydantic-settings + .env
- **スケジューラ**: APScheduler（内蔵・Asia/Tokyo）
- **AI**: 社内 Ollama（`OLLAMA_URL`）。自動仕分け・マトリクススコア・日次リセット・ブレスト・ニュース要約

---

## セットアップ

```bash
cd board-system/backend
python -m venv .venv
# Windows: .venv\Scripts\activate / Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

> [!IMPORTANT]
> **`TOKEN_ENCRYPTION_KEY` の設定が必須です。**  
> Google カレンダーの OAuth トークンを暗号化するため、`.env` 内の `TOKEN_ENCRYPTION_KEY` に **32 バイト以上** の文字列を必ず設定してください。未設定の場合は起動時にエラーとなりアプリが停止します。

---

## 起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API ルート: <http://localhost:8000>
- 死活確認: <http://localhost:8000/health>
- Swagger UI (開発時): <http://localhost:8000/docs>

---

## ディレクトリ構成

```
backend/
├── alembic/
│   ├── versions/      # マイグレーション履歴（is_personal_only, user_teams, admin_auth 等）
│   └── env.py         # 非同期マイグレーション設定
├── app/
│   ├── ai/            # Linko Core（triage, matrix, daily_reset）
│   ├── config.py      # アプリ設定・環境変数バリデーション
│   ├── db.py          # 非同期エンジン・セッション管理・シード初期化
│   ├── main.py        # FastAPI エントリポイント・ルーター登録
│   ├── models/        # SQLAlchemy モデル（User, Team, UserTeam, StickyNote, BoardPlacement 等）
│   ├── routers/       # 各種 API ルーター（管理者認証, チーム, 付箋, ボード, スケジューラ等）
│   ├── schemas/       # Pydantic スキーマ
│   ├── services/      # LLM 連携・設定管理サービス
│   └── scheduler.py   # 内蔵 APScheduler
├── desktop_app_releases/ # デスクトップアプリ MSI・latest.json 配信用（bind mount）
├── scripts/           # seed_teams.py 等のユーティリティ
├── alembic.ini
├── .env.example
├── requirements.txt
└── README.md
```

---

## マイグレーション

```bash
alembic upgrade head                       # 最新リビジョンまで適用
alembic revision --autogenerate -m "説明"   # モデル変更から新規リビジョン生成
```

### 最新マイグレーション適用履歴

- `m3n4o5p6q7r8_add_is_personal_only_to_sticky_notes.py`: パーソナル直接投稿付箋の AI 仕分けスキップフラグ追加
- `l2m3n4o5p6q7_add_user_teams_and_admin_auth.py`: 複数チーム所属用 `user_teams` 中間テーブルおよび管理者認証基盤の追加
- `k1l2m3n4o5p6_add_due_date_and_manually_moved_flag.py`: 付箋の期限日および手動移動フラグ追加
- `e5f6a7b8c9d0_add_user_google_tokens.py`: Google OAuth トークン暗号化テーブル追加

---

## 主要 API 一覧

### 1. 管理者認証・システム管理

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| POST | `/admin/login` | 不要 | 管理者パスワード検証と JWT トークン発行（body: `{"password": "..."}`） |
| GET | `/admin/llm` | **要Admin** | 現在の LLM スロット・実効 URL・解決モデル情報の取得 |
| PUT | `/admin/llm` | **要Admin** | LLM スロットの動的切替（`{"llm_target": 1\|2\|3\|null}`） |

### 2. ユーザー & チーム管理 (N:M対応)

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| GET | `/users` | 不要 | ユーザー一覧取得（所属チームリスト `teams` を含む） |
| GET | `/users/by_email` | 不要 | メールアドレスによるユーザー検索（デスクトップログイン用） |
| GET | `/users/{id}` | 不要 | ユーザー個別取得 |
| POST | `/users` | **要Admin** | ユーザー新規作成（複数チーム `team_ids` リスト指定対応） |
| PATCH | `/users/{id}` | **要Admin** | ユーザー情報・所属チーム更新 |
| DELETE | `/users/{id}` | **要Admin** | ユーザー削除 |
| GET | `/teams` | 不要 | チーム一覧取得（所属メンバー数等を含む） |
| POST | `/teams` | **要Admin** | チーム新規作成 |
| PATCH | `/teams/{id}` | **要Admin** | チーム名更新 |
| DELETE | `/teams/{id}` | **要Admin** | チーム削除（所属メンバーの紐付け解除） |

### 3. 付箋 (Sticky Notes) & ボード配置

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| GET | `/sticky_notes` | 不要 | 付箋一覧取得 |
| POST | `/sticky_notes` | 不要 | 付箋作成（Main ボード配置 ＋ **AI 自動仕分けで Task/Personal にも配置**） |
| POST | `/sticky_notes/create_personal` | 不要 | **Personal ボード直接投稿**（`is_personal_only=True`、AI仕分けをスキップし、タスク化を防ぐ） |
| POST | `/sticky_notes/import_from_postit` | 不要 | 付箋ボードからの取り込み（`dueDate` / `due_date` エイリアス対応） |
| PATCH | `/sticky_notes/sync_from_postit` | 不要 | 付箋ボードからの双方向同期 |
| GET/PATCH | `/sticky_notes/{id}` | 不要 | 付箋の取得・本文や期限（`due_date`）の更新 |
| DELETE | `/sticky_notes/{id}` | 不要 | 付箋削除（付箋ボードへ PATCH でグレー化通知を送信） |
| POST | `/sticky_notes/{id}/move_to_personal` | 不要 | Personal ボードへの配置 |
| POST | `/sticky_notes/{id}/copy_to_team` | 不要 | 指定チームに所属する全メンバーの Personal ボードへ付箋を一括コピー |
| POST | `/sticky_notes/{id}/release_to_task_board` | 不要 | Personal 配置を解除し、Task ボードへ再配置 |
| POST | `/board_placements/reorder_personal_lane` | 不要 | Personal ボード内の付箋並び順（`sort_order`）の一括更新 |
| GET | `/boards/main` | 不要 | Main ボード表示用データ（フリーキャンバス座標） |
| GET | `/boards/task` | 不要 | Task ボード表示用データ（5列、引き取り者、タスク色、期限情報） |
| GET | `/boards/personal?owner_id=` | 不要 | Personal ボード表示用データ（Today / タスク / Done、期限情報） |
| GET | `/boards/morning` | 不要 | Meeting ボード表示用データ（朝会スナップショット） |

### 4. 日次リセット・タスクローテーション・スケジューラ

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| POST | `/daily_reset/run_8am` | 不要 | 毎朝 8:00 日次処理（Meeting リセット + 今日の予定取得 + 期限 Today 移動 + **タスクローテーション**） |
| POST | `/daily_reset/rotate_tasks` | 不要 | 停滞タスクローテーションの手動実行（クエリ `?force=true` 対応） |
| POST | `/daily_reset/sync_to_morning` | 不要 | 全ユーザーの Personal Today を MORNING にスナップショットコピー |
| POST | `/daily_reset/reset_meeting` | 不要 | Meeting ボードのクリア |
| GET | `/daily_reset/messages?owner_id=` | 不要 | 朝会用「持ち越しますか？」メッセージ取得 |

### 5. デスクトップアプリ連携・リマインド・ブレスト

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| GET | `/users/{id}/task_reminders/pending` | 不要 | Today タスクリマインド取得（期限警告情報 `due_date` 付与） |
| POST | `/users/{id}/task_reminders/shown_slot` | 不要 | リマインド表示済み記録 |
| POST | `/users/{id}/task_reminders/ack` | 不要 | リマインド応答（`continue` または `done`） |
| GET | `/users/{id}/calendar_reminders/pending` | 不要 | カレンダーリマインド取得（N分前通知） |
| POST | `/brainstorm` | 不要 | リン子とのブレストチャット（SSE ストリーミング） |
| POST | `/brainstorm/calendar/confirm` | 不要 | ブレスト内で提案された Google カレンダー予定の登録承認 |

---

## AI Worker & ビジネスロジック

### 1. Auto-Triage & Matrix Scoring

`POST /sticky_notes` で付箋が投稿されると、ローカル LLM が内容を解析:

- **タスクか情報か**: タスクの場合は Task Board に配置。
- **マトリクススコアリング**: 緊急度と重要度を 0〜100 で採点し、象限 1〜4（1: アイデア、2: 短期、3: 長期、4: 重要）を決定。
- **担当者判定**: `users.name` と一致する社員名が含まれている場合、その社員の Personal Board（INBOX）に自動配置。
- ※ `POST /sticky_notes/create_personal` から投稿されたパーソナル専用付箋は、この AI 仕分けがスキップされます。

### 2. 期限連動移動ルール (`apply_due_date_rules`)

期限日（`due_date`）が設定されている Personal 付箋について:

- **当日以前**（`days <= 0`）または **直前日数**（1, 2, 3, 4, 5, 10, 20日前、30の倍数日前）に該当する場合、自動的に `INBOX` から `TODAY` レーンへ移動。
- 手動で移動されたフラグ（`is_manually_moved_to_today`）が立っている付箋は、ユーザーの意図を尊重して維持。

### 3. 停滞タスクの自動ローテーション (`rotate_stale_tasks`)

タスクボードおよびパーソナルボードが停滞するのを防ぐため、2日に1回（`run_8am` 実行時）自動実行:

- **優先タスクの保護**: 期限が10日以内のタスクはローテーション対象外とし、先頭位置をキープ。
- **Task Board**: 象限内に 11 件以上ある場合、先頭 10 件を末尾に移動。
- **Personal Board**: INBOX 内に 4 件以上ある場合、先頭 3 件を末尾に移動。

### 4. Google カレンダー連携とトークン暗号化

- 取得範囲: Asia/Tokyo 基準の当日 0:00〜23:59。
- セキュリティ: トークンは AES-256（`TOKEN_ENCRYPTION_KEY`）で DB に暗号化保存。復号失敗時は安全にレコードを初期化し再認証を促す。

---

## 本番（Docker）デプロイ

ホスト側で Python 環境や pip をインストールする必要はありません。`backend/Dockerfile` ビルド時にコンテナ内部に環境が構築されます。

```bash
cd /var/www/wlinko-pj/board-system/deploy
./deploy.sh
```
