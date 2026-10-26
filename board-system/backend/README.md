# Board System Backend (Wonder Linko)

4ボード（Main / Task / Personal / Meeting）用の FastAPI 非同期バックエンド[cite: 1]。  
開発は SQLite（aiosqlite）、**本番 Docker は PostgreSQL**（`postgresql+asyncpg`、`docker-compose.prod.yml` + `docker-compose.db.yml`）[cite: 1]。

---

## 技術スタック

- **Framework**: FastAPI [Python 3.10+](cite: 1)
- **ORM**: SQLAlchemy 2.0（完全非同期）[cite: 1]
- **DB ドライバ**: aiosqlite（SQLite） / asyncpg（PostgreSQL）[cite: 1]
- **マイグレーション**: Alembic[cite: 1]
- **セキュリティ・認証**: 簡易 JWT（管理者用）、`cryptography` / `sqlalchemy-utils`（Google OAuth トークンの AES-256 暗号化保存）[cite: 1]
- **設定管理**: pydantic-settings + .env[cite: 1]
- **スケジューラ**: APScheduler（内蔵・Asia/Tokyo）[cite: 1]
- **AI**: 社内 Ollama（`OLLAMA_URL` / 3スロット切替機能）。自動仕分け・マトリクススコア・日次リセット・ブレスト・ニュース要約[cite: 1]

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
> **`TOKEN_ENCRYPTION_KEY` の設定が必須です。**[cite: 1]  
> Google カレンダーの OAuth トークンを暗号化するため、`.env` 内の `TOKEN_ENCRYPTION_KEY` に **32 バイト以上** の文字列を必ず設定してください[cite: 1]。未設定の場合は起動時にエラーとなりアプリが停止します[cite: 1]。

---

## 起動

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API ルート: <http://localhost:8000>[cite: 1]
- 死活確認: <http://localhost:8000/health>[cite: 1]
- Swagger UI (開発時): <http://localhost:8000/docs>[cite: 1]

---

## マイグレーション履歴

```bash
alembic upgrade head                       # 最新リビジョンまで適用
alembic revision --autogenerate -m "説明"   # モデル変更から新規リビジョン生成
```

### 主なマイグレーション適用履歴

- `n4o5p6q7r8s9_add_is_help_request_to_sticky_notes.py`: 応援要請フラグ (`is_help_request`) の追加[cite: 1]
- `m3n4o5p6q7r8_add_is_personal_only_to_sticky_notes.py`: パーソナル直接投稿付箋の AI 仕分けスキップフラグ追加[cite: 1]
- `l2m3n4o5p6q7_add_user_teams_and_admin_auth.py`: 複数チーム所属用 `user_teams` 中間テーブルおよび管理者認証基盤の追加[cite: 1]
- `k1l2m3n4o5p6_add_due_date_and_manually_moved_flag.py`: 付箋の期限日および手動移動フラグ追加[cite: 1]
- `e5f6a7b8c9d0_add_user_google_tokens.py`: Google OAuth トークン暗号化テーブル追加[cite: 1]

---

## 主要 API 一覧

### 1. 管理者認証・システム管理

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| POST | `/admin/login` | 不要 | 管理者パスワード検証と JWT トークン発行[cite: 1] |
| GET | `/admin/llm` | **要Admin** | 現在の LLM スロット・実効 URL・解決モデル情報の取得[cite: 1] |
| PUT | `/admin/llm` | **要Admin** | LLM スロットの動的切替（`{"llm_target": 1\|2\|3\|null}`）[cite: 1] |

### 2. ユーザー & チーム管理 (N:M対応)

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| GET | `/users` | 不要 | ユーザー一覧取得（所属チームリスト `teams` を含む）[cite: 1] |
| GET | `/users/by_email` | 不要 | メールアドレスによるユーザー検索[cite: 1] |
| POST | `/users` | **要Admin** | ユーザー新規作成（複数チーム `team_ids` 指定対応）[cite: 1] |
| PATCH | `/users/{id}` | **要Admin** | ユーザー情報・所属チーム更新[cite: 1] |
| DELETE | `/users/{id}` | **要Admin** | ユーザー削除（保有パーソナル付箋のタスクボードリリース）[cite: 1] |
| GET | `/teams` | 不要 | チーム一覧取得（所属メンバー数含む）[cite: 1] |
| POST | `/teams` | **要Admin** | チーム新規作成[cite: 1] |
| PATCH | `/teams/{id}` | **要Admin** | チーム名更新[cite: 1] |
| DELETE | `/teams/{id}` | **要Admin** | チーム削除[cite: 1] |

### 3. 付箋 (Sticky Notes) & ボード配置

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| GET | `/sticky_notes` | 不要 | 付箋一覧取得[cite: 1] |
| POST | `/sticky_notes` | 不要 | 付箋作成（Main配置 ＋ **AI 自動仕分けで Task/Personal にも配置**）[cite: 1] |
| POST | `/sticky_notes/create_personal` | 不要 | **Personal ボード直接投稿**（`is_personal_only=True`、AI仕分けをスキップ）[cite: 1] |
| PATCH | `/sticky_notes/{id}` | 不要 | 付箋の取得・本文や期限（`due_date`）の更新[cite: 1] |
| DELETE | `/sticky_notes/{id}` | 不要 | 付箋削除（付箋ボードへ PATCH でグレー化通知を送信）[cite: 1] |
| DELETE | `/board_placements/{id}` | 不要 | パーソナル配置削除（**複数人アサイン時は未完了メンバーがいる場合ブロック**）[cite: 1] |
| POST | `/sticky_notes/{id}/move_to_personal` | 不要 | Personal ボードへの配置（要請者 `HELP_REQUEST` ➔ `INBOX` 自動復帰）[cite: 1] |
| POST | `/sticky_notes/{id}/copy_to_team` | 不要 | チーム所属全メンバーの Personal ボードへ付箋を一括コピー[cite: 1] |
| GET | `/boards/personal?owner_id=` | 不要 | Personal ボード表示（Today/Inbox/Done、`taken_by` 他担当者進捗状態 `is_done` 含む）[cite: 1] |

### 4. 日次処理・自動移動・ローテーション・Self-Healing

| メソッド | パス | 認証 | 説明 |
| :--- | :--- | :---: | :--- |
| POST | `/daily_reset/run_8am` | 不要 | 毎朝 8:00 日次処理（Meeting リセット + カレンダー取得 + 期限 Today 移動 + **タスクローテーション** + **Self-Healing 差分照合**）[cite: 1] |
| POST | `/daily_reset/rotate_tasks` | 不要 | 停滞タスクローテーションの手動実行（`?force=true` 対応）[cite: 1] |
| POST | `/daily_reset/reconcile` | 不要 | 手動 Self-Healing 差分照合・自動修復（`?dry_run=true` 対応）[cite: 1] |

Self-Healing を本番で有効化する前に、`RECONCILIATION_DRY_RUN=true` のログを確認してください。特に `Missing in DB -> Create`（`created_in_db`）と `DB Completed/Archived -> Remote Gray`（`archived_in_remote`）の件数・対象が想定どおりで、定常運用で不要な差分がほぼ 0 件になっていることを確認します。問題がないと判断できた後、本番環境の `.env` で `RECONCILIATION_DRY_RUN=false` を明示してください。手動実行の結果には両件数を含む統計が返ります。

---

## 本番デプロイ

`backend/Dockerfile` ビルド時にコンテナ内部に環境が構築されます[cite: 1]。また、`desktop_app_releases/` はコンテナへ bind mount されているため、MSI や `latest.json` の更新はコンテナの再起動なしに即時配信されます[cite: 1]。

```bash
cd /var/www/wlinko-pj/board-system/deploy
./deploy.sh
```
