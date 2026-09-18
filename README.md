# Wonder Linko (wl-board-pj)

付箋ボード（`wl-sticky-note`）、統合4ボードシステム（`board-system`）、社内常駐デスクトップアプリ（`wl_desktop_app`）が連携する、ワンダーリンクの業務協調・タスク管理プラットフォームです。

---

## 1. プロジェクト構成

```
wl-board-pj/
├── board-system/               # 統合4ボードシステム（Main / Task / Personal / Meeting）
│   ├── backend/                # FastAPI + SQLAlchemy（非同期、SQLite / PostgreSQL）
│   ├── frontend/               # Next.js (App Router) + Tailwind CSS v4（basePath: /boards）
│   ├── deploy/                 # Blue/Green デプロイスクリプト（deploy.sh / rollback.sh）
│   ├── nginx/                  # 本番用 Nginx 設定（リバースプロキシ・静的アセット直接配信）
│   ├── docker-compose.prod.yml # 本番用 Docker Compose 設定
│   └── docker-compose.db.yml   # 本番・ローカル用 PostgreSQL 設定
├── wl-sticky-note/             # リアルタイム協調型付箋ボード
│   └── src/                    # Next.js + Express + Socket.IO（リアルタイム同期・3D/UI高度化）
├── wl_desktop_app/             # 社員PC常駐用デスクトップアプリ（Personal Linko Agent）
│   ├── app.py                  # メインエントリ（タスクトレイ常駐・ミニポートUI）
│   ├── build_msi.ps1           # MSI インストーラ自動ビルド（自己署名コード署名）
│   └── scripts/                # 署名生成・アンインストールスクリプト
├── docs/                       # 設計書・デプロイ手順・改善プラン・運用マニュアル
├── start_all_servers.ps1       # ローカル開発用：全サーバー一括起動スクリプト（PowerShell）
├── check_ports.ps1             # ポート使用状況確認スクリプト
└── ローカルDockerでテストする手順.md # ローカル環境でのDocker検証マニュアル
```

---

## 2. システム連携アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                   社員 Windows PC / ブラウザ                 │
│                                                             │
│  [wl_desktop_app]            [Webブラウザ]                  │
│   - ミニポート（付箋クイック投稿）  - 付箋ボード (/board/wl)        │
│   - タスク/カレンダーリマインド    - Board System (/boards)      │
│   - リン子ブレスト（SSE/音声）      (Task / Personal / Meeting) │
└──────────────┬───────────────────────────────┬──────────────┘
               │                               │
               ▼ (リバースプロキシ: Nginx)       ▼
┌─────────────────────────────────────────────────────────────┐
│ 本番サーバ (wlboardsys.internal.wonder-link.com / 172.16.1.203) │
│                                                             │
│  ┌────────────────────────┐    ┌──────────────────────────┐ │
│  │ wl-sticky-note (Node)  │    │ board-system             │ │
│  │ - Express + Socket.IO  │◄───┤ - FastAPI Backend (8000) │ │
│  │ - リアルタイム付箋同期 │───►│ - Next.js Frontend(3001) │ │
│  └────────────────────────┘    └─────────────┬────────────┘ │
│                                              │              │
│               ┌──────────────────────────────┼────────────┐ │
│               ▼                              ▼            ▼ │
│      [PostgreSQL (linko-db)]      [社内 Ollama]   [Google API]
│      (ユーザー/タスク/配置データ)   (AI自動仕分け)   (カレンダー)
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 各コンポーネントの役割と主要機能

| コンポーネント | 技術スタック | 主な役割・機能 | 参照ドキュメント |
| :--- | :--- | :--- | :--- |
| **[board-system](board-system/README.md)** | FastAPI, PostgreSQL, Next.js 16, Tailwind CSS v4 | **統合4ボードシステム**: Main（全体構想）、Task（5列・引き取り管理）、Personal（Today/Inbox/Done）、Meeting（朝会スナップショット・ニュース要約）。複数チーム所属（N:M）、管理者認証（JWT）、期限連動ルール、停滞タスクの自動ローテーション（`run_8am`）。 | [board-system/README.md](board-system/README.md) |
| **[wl-sticky-note](wl-sticky-note/README.md)** | Next.js 16, Express, Socket.IO, Three.js | **リアルタイム付箋ボード**: 複数人同時編集、Google Map風パン移動、ホイールズーム（0.3x〜2.5x）、矩形ドラッグ複数選択・一括移動、Esc選択解除、グレー付箋非表示切替、`useRef` 直接DOM操作によるドラッグ超高速化。 | [wl-sticky-note/README.md](wl-sticky-note/README.md) |
| **[wl_desktop_app](wl_desktop_app/README.md)** | Python 3.10+, CustomTkinter, pystray, winotify | **デスクトップ常駐エージェント**: ミニポート（付箋クイック投稿）、タスクトレイ常駐、タスク/カレンダー定時リマインド（期限警告バッジ付）、OS名前付きMutexによる確実な二重起動防止、自前フローティング通知フォールバック、自己署名MSI配布。 | [wl_desktop_app/README.md](wl_desktop_app/README.md) |

---

## 4. 開発環境のセットアップと起動手順

### 前提条件

- **OS**: Windows 10/11 または Linux / macOS（デスクトップアプリのMSIビルドは Windows のみ）
- **ランタイム**: Python 3.10 以上, Node.js 20.x LTS 以上, npm 9.x 以上
- **インフラ**: Docker / Docker Compose（Docker 起動時）

### 4-1. PowerShell 一括起動（Windows 開発時）

リポジトリルートから以下のスクリプトを実行すると、バックエンド・フロントエンド・付箋ボードを各ウィンドウで一括起動できます。

```powershell
.\start_all_servers.ps1
```

- ポート使用状況の確認: `.\check_ports.ps1`

### 4-2. 個別手動起動（開発時）

#### ① Board System Backend

```bash
cd board-system/backend
python -m venv .venv
# Windows: .venv\Scripts\activate / Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# ※ .env の TOKEN_ENCRYPTION_KEY に 32 バイト以上の安全な文字列を必ず設定してください
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### ② Board System Frontend

```bash
cd board-system/frontend
npm install
cp .env.local.example .env.local
npm run dev -- -p 3001
```

#### ③ 付箋ボード (wl-sticky-note)

```bash
cd wl-sticky-note/src
npm install
cp .env.example .env
npm run dev
```

#### ④ デスクトップアプリ (wl_desktop_app)

```powershell
cd wl_desktop_app
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

---

## 5. ローカル Docker による起動検証

付箋ボードと Board System をまとめてコンテナで起動する場合:

```bash
cd board-system
cp .env.example .env
docker compose up -d --build
# 初回マイグレーション
docker exec -it linko-backend alembic upgrade head
```

- **Board System フロント**: [http://localhost:3010](http://localhost:3010) (自動的に `/taskboard` へリダイレクト)
- **付箋ボード**: [http://localhost:3011/board/wl](http://localhost:3011/board/wl)
- **Backend API**: [http://localhost:8010/health](http://localhost:8010/health)

詳細手順は [ローカルDockerでテストする手順.md](ローカルDockerでテストする手順.md) を参照してください。

---

## 6. 本番環境構成とデプロイ

- **本番ドメイン**: `https://wlboardsys.internal.wonder-link.com/` (IP: `172.16.1.203`)
- **Blue/Green デプロイ**: `board-system/deploy/deploy.sh` によるゼロダウンタイム切り替え。
- **静的アセット永続化（改善計画21）**: デプロイ時にフロントエンドコンテナの `.next/static` をホストOS上の `/var/www/wlinko-pj/shared_static/` に同期し、Nginx から直接配信。不在時は純粋な 404 を返却してブラウザ側の自動リロード（ChunkLoadError リカバリ）をトリガー。
- **データベース**: PostgreSQL（`docker-compose.db.yml`）、マイグレーションは Alembic で完全管理。

### 本番デプロイコマンド例

```bash
ssh devuser01@172.16.1.203
cd /var/www/wlinko-pj
git pull
cd board-system/deploy
./deploy.sh
```

---

## 7. セキュリティと環境変数に関する重要事項

> [!IMPORTANT]
>
> 1. **機密情報のコミット禁止**:
>    - 個人情報（PII）、パスワード、APIキー、OAuthシークレット、秘密鍵（`.pfx` 等）を絶対に Git リポジトリへコミット・プッシュしないでください。
>    - `.env` や `config.json` などの設定ファイルは必ず `.gitignore` に含まれていることを確認してください。
> 2. **TOKEN_ENCRYPTION_KEY の必須設定**:
>    - Google カレンダーの OAuth トークンは AES-256 で暗号化されて保存されます。
>    - `TOKEN_ENCRYPTION_KEY` には **32 バイト以上** の安全なランダム文字列を設定してください。未設定時はバックエンドが起動しません。
> 3. **管理者パスワード**:
>    - `ADMIN_PASSWORD`（既定: `admin123`）は本番環境構築時に必ず堅牢な値に変更してください。

---

## 8. 関連ドキュメント一覧

- [docs/本番デプロイ手順_Docker.md](docs/本番デプロイ手順_Docker.md) — 本番 Docker 環境のデプロイ・更新手順
- [docs/本番環境の構成_Docker.md](docs/本番環境の構成_Docker.md) — インフラ構成・ネットワーク設計
- [docs/Googleカレンダー連携の動作確認.md](docs/Googleカレンダー連携の動作確認.md) — OAuth 2.0 連携ガイド
- [docs/ユーザーDB共用と登録方法.md](docs/ユーザーDB共用と登録方法.md) — ユーザーマスタ管理仕様
- [docs/開発・改善プラン/遠藤改善内容/](docs/開発・改善プラン/遠藤改善内容/) — 各種機能改善・バグ修正の詳細仕様書
