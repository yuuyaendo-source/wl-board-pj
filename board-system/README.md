# Board System (Wonder Rinko)

付箋ボード（`wl-sticky-note`）と連携する統合ボードシステム。**Main / Task / Personal / Meeting** の 4 ボードを提供し、社内 LLM（Ollama）による自動仕分け・Google カレンダー連携・ニュース要約・デスクトップアプリ向け API を担う。

**本番は Docker（Blue/Green）+ PostgreSQL** が標準。付箋ボードと同一サーバ（`wl-board-pj` / `172.16.1.84`）で `https://wl-ai-board.internal.wonder-link.com/` に配信。

## 構成

```
board-system/
├── backend/     # FastAPI + SQLAlchemy（開発: SQLite / 本番: PostgreSQL）
├── frontend/    # Next.js App Router + Tailwind（本番 basePath: /boards）
├── deploy/      # deploy.sh / rollback.sh（Blue/Green）
├── nginx/       # 本番リバースプロキシ設定例
├── docker-compose.prod.yml
├── docker-compose.db.yml
└── README.md
```

## 開発状況（2026年6月時点）

| 項目 | 状態 | 備考 |
|------|------|------|
| 4 ボード UI | 完了 | `/main` `/taskboard` `/personal/:slug` `/meeting` |
| Task ボード | 完了 | 5 列（アイデア・短期・長期・重要・完了）。色・引き取り者表示 |
| Personal ボード | 完了 | Today / タスク / Done。Task 連動・Google カレンダー「今日の予定」 |
| Meeting ボード | 完了 | 毎朝 10:15 に Personal Today を MORNING へコピー。ニュース要約付箋も反映 |
| AI 自動仕分け | 完了 | Ollama（`OLLAMA_URL`）。Gemini は不使用 |
| Google カレンダー | 完了 | OAuth 連携・今日の予定・デスクトップ向けリマインド API |
| ブレスト API | 完了 | `POST /brainstorm`（SSE）。デスクトップアプリから利用 |
| タスク/カレンダーリマインド | 完了 | デスクトップアプリがポーリングする API |
| ニュース要約 | 完了 | スケジューラで取得・Meeting ボードへ配置 |
| LLM 管理 UI | 完了 | `/boards/admin/system`（`LLM_TARGET` 切替等） |
| デスクトップ MSI 配信 | 完了 | `/api/bs/desktop-app/*`（bind mount で即反映） |
| 本番デプロイ | 完了 | Blue/Green + PostgreSQL。詳細は下記ドキュメント |

## 本番 URL（Docker 構成）

| 用途 | パス（FQDN 配下） |
|------|-------------------|
| 付箋ボード | `/board/wl` 等 |
| Board System フロント | `/boards` |
| Board System API | `/api/bs` |
| Google OAuth コールバック | `/auth/google/callback` |
| デスクトップ更新 | `/api/bs/desktop-app/latest.json` |

同一 LAN 上の linko-system（`https://linko-board.internal.wonder-link.com/`）とユーザー DB・顔/音声登録 API を共有。

## 起動（開発時）

**バックエンドを先に起動すること。**

```bash
# ターミナル 1
cd board-system/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # OLLAMA_URL 等
uvicorn app.main:app --reload --port 8000

# ターミナル 2
cd board-system/frontend
npm install && npm run dev
```

- フロント: http://localhost:3000（単体）または :3001（付箋ボード併用）
- トップで「API 接続済み」と表示されれば OK

**付箋ボード併用**: `wl-sticky-note` を 3000、board-system フロントを 3001。  
`NEXT_PUBLIC_BOARD_SYSTEM_URL` / `NEXT_PUBLIC_LEGACY_BOARD_URL` で相互リンク。

## ローカル Docker（付箋＋Board まとめて）

```bash
cd board-system
cp .env.example .env
docker compose up -d --build
docker exec -it linko-backend alembic upgrade head   # 初回のみ
```

- Board System: http://localhost:3010
- 付箋ボード: http://localhost:3011

詳細: [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) のローカル確認セクション

## 日次スケジューラ（内蔵 APScheduler・JST）

`SCHEDULER_ENABLED=true`（既定）のとき、外部 cron 不要。

| 時刻 (JST) | 処理 |
|------------|------|
| 毎日 8:00 | `POST /daily_reset/run_8am` — Meeting リセット + 全ユーザーの今日の予定取得・Today 付箋 |
| 毎日 10:00 | `POST /news/clear` — ニュース付箋クリア |
| 毎日 10:15 | `POST /daily_reset/sync_to_morning` — Personal Today → Meeting ボード |
| 毎日 10:15 | `POST /news/fetch` — ニュース取得・要約を Meeting へ |

Docker 内では `SCHEDULER_BASE_URL` をコンテナから見える自サーバ URL に設定（例: `http://127.0.0.1:8000`）。

## 本番デプロイ・更新

| やりたいこと | 参照 |
|--------------|------|
| Docker 本番（推奨） | [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) |
| 要約・よく使うコマンド | [DEPLOY.md](DEPLOY.md) |
| 非 Docker（PM2） | [docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md) |
| ドキュメント索引 | [docs/デプロイ・運用.md](../docs/デプロイ・運用.md) |

コード更新時の典型フロー（Docker）:

```bash
cd board-system/deploy && ./deploy.sh
docker exec -it linko-backend-blue alembic upgrade head   # マイグレーションがある場合
```

デスクトップ MSI / `latest.json` の差し替えのみなら **deploy 不要**（`backend/desktop_app_releases/` の bind mount）。

## サブディレクトリ

| ディレクトリ | README | 内容 |
|--------------|--------|------|
| [backend/](backend/README.md) | あり | FastAPI、API 一覧、AI Worker、マイグレーション |
| [frontend/](frontend/README.md) | あり | Next.js、ボード別パス、環境変数 |
| [backend/desktop_app_releases/](backend/desktop_app_releases/README.md) | あり | デスクトップ MSI 自動更新配信 |

## 関連リポジトリ・サービス

| コンポーネント | 場所 |
|----------------|------|
| 付箋ボード | `wl-board-pj/wl-sticky-note` |
| デスクトップアプリ | `wl-board-pj/wl_desktop_app` |
| AI 受付（リン子） | `linko-system`（別リポジトリ） |

## 関連ドキュメント

- [docs/本番設定の目安.md](../docs/本番設定の目安.md) — 本番 .env・URL の目安
- [docs/Googleカレンダー連携の動作確認.md](../docs/Googleカレンダー連携の動作確認.md)
- [docs/ユーザーDB共用と登録方法.md](../docs/ユーザーDB共用と登録方法.md)
- [docs/開発・改善プラン/改善指示書11.md](../docs/開発・改善プラン/改善指示書11.md) — Task/Personal UI 仕様
