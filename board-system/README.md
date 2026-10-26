# Board System (Wonder Linko)

付箋ボード（`wl-sticky-note`）と連携する統合ボードシステム。**Main / Task / Personal / Meeting** の 4 ボードを提供し、社内 LLM（Ollama）による自動仕分け・Google カレンダー連携・ニュース要約・デスクトップアプリ向け API を担う。

**本番は Docker（Blue/Green）+ PostgreSQL** が標準。付箋ボードと同一サーバ（`wlboardsys-app-01` / `172.16.1.203`）で `https://wlboardsys.internal.wonder-link.com/` に配信。

---

## 構成

```
board-system/
├── backend/                # FastAPI + SQLAlchemy（開発: SQLite / 本番: PostgreSQL）
│   ├── app/                # APIルーター、モデル、AI Worker、スケジューラ
│   ├── alembic/            # DBマイグレーションスクリプト
│   └── desktop_app_releases/ # デスクトップアプリ MSI/latest.json 配信用（bind mount）
├── frontend/               # Next.js 16 App Router + Tailwind CSS v4（本番 basePath: /boards）
├── deploy/                 # deploy.sh / rollback.sh（Blue/Green ゼロダウンタイム）
├── nginx/                  # 本番リバースプロキシ設定（静的アセット直接配信対応）
├── docker-compose.prod.yml # 本番アプリ用 Compose
├── docker-compose.db.yml   # PostgreSQL DB用 Compose
└── README.md
```

---

## 主な機能と開発状況（2026年9月現在）

| 項目 | 状態 | 詳細 |
| :--- | :--- | :--- |
| **4 ボード UI** | 完了 | `/main`（全体構想・✨AI自動仕分け付箋）、`/taskboard`（5列）、`/personal/:id`（個別作業）、`/meeting`（朝会スナップショット） |
| **Task ボード** | 完了 | 5列（アイデア・短期・長期・重要・完了）。色・引き取り者表示。👥 チーム所属メンバーへの付箋一括コピー。**期限バッジ（DueDateBadge）表示**。 |
| **Personal ボード** | 完了 | Today / タスク / Done。Task 連動・Google カレンダー「今日の予定」。**パーソナル専用投稿（`is_personal_only`、AI仕分けスキップ）**。ゴミ箱ドロップ時の安全なアーカイブ。 |
| **Meeting ボード** | 完了 | 毎朝 10:15 に Personal Today を MORNING へ自動コピー。期限バッジ・強調枠線表示。ニュース要約付箋の反映。 |
| **複数チーム管理 (N:M)** | 完了 | `user_teams` 中間テーブルによる多対多所属対応。ユーザー一覧での色分けバッジ表示。チーム一括コピーの複数所属対応。 |
| **管理者認証 (JWT)** | 完了 | `ADMIN_PASSWORD` に基づく JWT 認証（`POST /admin/login`）。ユーザー作成/削除、チーム作成/削除、LLM切替操作の保護。 |
| **期限連動ルール** | 完了 | 期限（`due_date`）が当日または特定日数前（1〜5, 10, 20日前、30の倍数日前）のタスクを自動で Today レーンへ移動。 |
| **タスクローテーション** | 完了 | 停滞タスクを自動で末尾に再配置（2日に1回、`run_8am` 実行時）。期限10日以内の優先タスクは先頭キープ。手動トリガー API（`/daily_reset/rotate_tasks`）完備。 |
| **OAuthトークン暗号化** | 完了 | Google カレンダーのアクセストークン／リフレッシュトークンを AES-256 で暗号化保存（`TOKEN_ENCRYPTION_KEY` 必須）。 |
| **AI 自動仕分け** | 完了 | 社内 Ollama（`OLLAMA_URL`）。Gemini は不使用。複数 LLM スロット切替（1〜3）対応。 |
| **Google カレンダー** | 完了 | OAuth 連携・今日の予定・デスクトップ向けリマインド API（期限付き）。 |
| **ブレスト API** | 完了 | `POST /brainstorm`（SSE ストリーミング）。デスクトップアプリから利用（カレンダー予定登録提案・音声読み上げ連携）。 |
| **デスクトップ MSI 配信** | 完了 | `/api/bs/desktop-app/*`（ホストディレクトリの bind mount によりコンテナ再起動不要で即時反映）。 |
| **本番ゼロダウンタイム** | 完了 | Blue/Green 切り替え + 静的アセット（`_next/static`）のホストOSディレクトリ永続化同期（改善計画21）。 |

---

## 本番 URL（Docker 構成）

| 用途 | パス（FQDN: `wlboardsys.internal.wonder-link.com`） |
| :--- | :--- |
| 付箋ボード | `/board/wl` 等 |
| Board System フロント | `/boards`（ルート `/` は `/boards/taskboard` に自動リダイレクト） |
| Board System API | `/api/bs/`（末尾スラッシュ必須） |
| Google OAuth コールバック | `/auth/google/callback` |
| デスクトップ更新 | `/api/bs/desktop-app/latest.json` |

同一 LAN 上の linko-system（`https://linkosys.internal.wonder-link.com/`）とユーザー DB・顔/音声登録 API を共有。

---

## 起動方法（ローカル開発時）

**バックエンドを先に起動してください。**

### ターミナル 1: バックエンド

```bash
cd board-system/backend
python -m venv .venv
# Windows: .venv\Scripts\activate / Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 重要: .env 内の TOKEN_ENCRYPTION_KEY に 32 バイト以上の安全な文字列を設定
uvicorn app.main:app --reload --port 8000
```

- API ルート: <http://localhost:8000>
- 死活確認: <http://localhost:8000/health>

### ターミナル 2: フロントエンド

```bash
cd board-system/frontend
npm install
cp .env.local.example .env.local   # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev -- -p 3001
```

- フロントエンド: <http://localhost:3001>（単体時は 3000、付箋ボード併用時は 3001）
- 開くと自動的に `/taskboard` へリダイレクトされます。

---

## ローカル Docker（付箋＋Board まとめて起動）

```bash
cd board-system
cp .env.example .env
docker compose up -d --build
docker exec -it linko-backend alembic upgrade head   # 初回のみマイグレーション
```

- **Board System フロント**: <http://localhost:3010>
- **付箋ボード**: <http://localhost:3011/board/wl>
- **Backend API**: <http://localhost:8010/health>

詳細: [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md)

---

## 日次スケジューラ（内蔵 APScheduler・JST）

`SCHEDULER_ENABLED=true`（既定）のとき、外部 cron なしで動作します。

| 時刻 (JST) | 処理 | エンドポイント |
| :--- | :--- | :--- |
| **毎日 8:00** | Meeting リセット + 全ユーザーの今日の予定取得 + 期限連動ルール適用 + **停滞タスクの自動ローテーション** | `POST /daily_reset/run_8am` |
| **毎日 10:00** | ニュース付箋クリア | `POST /news/clear` |
| **毎日 10:15** | Personal Today → Meeting ボード同期 | `POST /daily_reset/sync_to_morning` |
| **毎日 10:15** | ニュース取得・要約を Meeting へ配置 | `POST /news/fetch` |

Docker 内では `SCHEDULER_BASE_URL` をコンテナ自身から到達可能な自サーバ URL（例: `http://127.0.0.1:8000`）に設定します。

---

## 本番デプロイ・更新手順

コード更新時の標準フロー（Docker Blue/Green）:

```bash
cd /var/www/wlinko-pj/board-system/deploy
./deploy.sh
```

`deploy.sh` は以下を自動で実行します:

1. PostgreSQL の起動確認（`pg_isready` による待機ループ）
2. 付箋データ（`boards.json`）の自動バックアップ（30世代保持）と共有ボリューム同期
3. 新コンテナのビルド・起動・ヘルスチェック（`/health`）
4. DB マイグレーション（`alembic upgrade head`）およびチームシード（`seed_teams.py`）
5. **静的アセットのホスト同期**（`/var/www/wlinko-pj/shared_static/frontend`）および 14 日超の旧アセット自動削除（改善計画21）
6. Nginx upstream 切り替え（`active_env.conf`）と Nginx リロード
7. 旧コンテナの安全な停止

> [!TIP]
> デスクトップアプリの MSI / `latest.json` の更新のみであれば、**`deploy.sh` の実行は不要**です（`backend/desktop_app_releases/` の bind mount により、ファイルを配置するだけで即時反映されます）。

---

## Nginx の注意点：`rewrite` + URI 無し `proxy_pass` の禁止

`location /api/bs/` は **URI 付き `proxy_pass`（末尾スラッシュあり）** で記述してください。

```nginx
# ✅ 正しい設定: location /api/bs/ が自動除去されてバックエンドに渡る
location /api/bs/ {
    proxy_pass http://current_backend/;      # 末尾スラッシュ必須
}

# ❌ 禁止: Ubuntu の nginx 更新パッチで URI 転送が破損する障害原因
location /api/bs/ {
    rewrite ^/api/bs/(.*)$ /$1 break;
    proxy_pass http://current_backend;       # URI 無し
}
```

### 静的アセットの直接配信と 404 ハンドリング（改善計画21）

デプロイ直後に旧画面を開いていたユーザーが古い JS ファイルを要求した際、Next.js のフォールバック HTML が返却されて `SyntaxError`（`🔴 Offline`）になるのを防ぐため、Nginx が静的アセットを直接配信し、存在しない場合は純粋な 404 を返します。

```nginx
location /_next/static/ {
    alias /var/www/wlinko-pj/shared_static/frontend/;
    expires 365d;
    access_log off;
    try_files $uri =404;
}
```

---

## サブディレクトリ README

| ディレクトリ | README | 内容 |
| :--- | :--- | :--- |
| [backend/](backend/README.md) | あり | FastAPI、全 API 一覧、管理者認証、AI Worker、マイグレーション |
| [frontend/](frontend/README.md) | あり | Next.js 16、4ボード仕様、チーム管理UI、環境変数 |
| [backend/desktop_app_releases/](backend/desktop_app_releases/README.md) | あり | デスクトップ MSI 自動更新配信仕様（bind mount） |

---

## 関連ドキュメント

- [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) — 本番 Docker 詳細手順
- [docs/Googleカレンダー連携の動作確認.md](../docs/Googleカレンダー連携の動作確認.md)
- [docs/ユーザーDB共用と登録方法.md](../docs/ユーザーDB共用と登録方法.md)
- [docs/開発・改善プラン/遠藤改善内容/改善計画21_アセット欠落対策とゼロダウンタイム化_ホストOS対応版.md](../docs/開発・改善プラン/遠藤改善内容/改善計画21_アセット欠落対策とゼロダウンタイム化_ホストOS対応版.md)
