# Board System Backend (Wonder Rinko)

4ボード（Main / Task / Personal / Morning）用の FastAPI バックエンド。  
SQLite（開発）を async SQLAlchemy + aiosqlite で利用。将来は PostgreSQL へ `DATABASE_URL` の変更のみで移行可能。

## 技術スタック

- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.0（非同期）
- **DB ドライバ**: aiosqlite（SQLite）。本番は `postgresql+asyncpg` を想定
- **設定**: pydantic-settings + .env
- **AI（フェーズ3）**: Google Gemini（自動仕分け・マトリクススコア・日次リセット）

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
│   ├── ai/            # Rinko Core（triage, matrix, daily_reset）
│   ├── config.py      # 設定（DATABASE_URL, GEMINI_API_KEY 等）
│   ├── db.py          # 非同期エンジン・セッション・Base
│   ├── main.py        # FastAPI アプリ
│   ├── models/        # User, StickyNote, BoardPlacement
│   ├── routers/       # users, sticky_notes, boards, daily_reset
│   └── schemas/       # Pydantic スキーマ
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

## API（フェーズ2・3 実装済み）

| 種別 | メソッド | パス | 説明 |
|------|----------|------|------|
| 死活 | GET | `/health` | ヘルスチェック |
| users | GET/POST | `/users` | 一覧・作成 |
| sticky_notes | GET/POST | `/sticky_notes` | 一覧・作成（作成時 MAIN＋**AI で Task/Personal にも自動配置**） |
| | GET/PATCH/DELETE | `/sticky_notes/{id}` | 1件取得・更新・削除 |
| | POST | `/sticky_notes/{id}/move_to_personal` | Personal に配置（body: `owner_id`, `lane`） |
| | POST | `/sticky_notes/{id}/release_to_task_board` | Task Board に配置 |
| board_placements | GET/POST | `/board_placements` | 一覧（`?board_type=&owner_id=`）・作成 |
| | GET/PATCH/DELETE | `/board_placements/{id}` | 1件取得・更新・削除 |
| boards | GET | `/boards/main` | Main ボード View |
| | GET | `/boards/task` | Task ボード View |
| | GET | `/boards/personal?owner_id=` | Personal ボード View |
| | GET | `/boards/morning` | Morning ボード View |
| daily_reset | GET | `/daily_reset/messages?owner_id=` | 朝会用「持ち越しますか？」メッセージ一覧（Logic 3） |

- **CORS**: 全オリジン許可（開発用）。本番では `allow_origins` を絞ること。

## フェーズ3: AI Worker（Rinko Core）

`GEMINI_API_KEY` を .env に設定すると以下が有効になる。

1. **Auto-Triage（Logic 1）**  
   `POST /sticky_notes` で Main に投稿すると、LLM が「タスクか情報か」「担当者明記か」を判定。  
   タスク → **Task Board** に配置し、緊急度・重要度をスコアリング（position_x/y, matrix_quadrant）。  
   担当者名あり → 該当ユーザー（`users.name` 部分一致）の **Personal Board Inbox** に配置。

2. **Matrix Scoring（Logic 2）**  
   Task Board に載せる際、LLM が緊急度・重要度を 0–100 で採点。  
   position_x = 緊急度、position_y = 重要度。matrix_quadrant は 1–4 で自動算出。

3. **Daily Reset（Logic 3）**  
   `GET /daily_reset/messages?owner_id=` で、そのユーザーの Personal Today レーンの付箋について  
   「昨日の『〇〇』は持ち越しますか？」形式のメッセージを LLM で生成。

- 環境変数: `GEMINI_API_KEY`（必須）、`GEMINI_MODEL`（任意・既定: gemini-2.5-flash-lite）

## 次のステップ（開発プラン）

1. **フェーズ4**: Frontend（Next.js 4ボード View）
