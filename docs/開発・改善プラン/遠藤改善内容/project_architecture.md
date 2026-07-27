# プロジェクト構成とファイル・ディレクトリの役割 (board-system)

このドキュメントでは、`wl-board-pj/board-system` プロジェクト全体のアーキテクチャと主要なファイル・ディレクトリの役割について解説します。

## 1. システム全体アーキテクチャ (フローチャート)

```mermaid
graph TD
    Client[ブラウザ / クライアント]

    subgraph Nginx [Nginx / リバースプロキシ]
        Proxy[nginx.conf]
    end

    subgraph Frontend [フロントエンド (Next.js)]
        FE_UI[Next.js App Router]
        FE_Pages[各ページ: admin, taskboard, etc.]
    end

    subgraph Backend [バックエンド (FastAPI)]
        BE_API[FastAPI Routers]
        BE_Logic[Services / Logic]
        BE_AI[AI Integration / Ollama]
    end

    subgraph Database [データベース]
        Postgres[(PostgreSQL)]
    end
    
    subgraph External [外部システム/別プロジェクト]
        StickyNote[wl-sticky-note]
    end

    Client -->|HTTP リクエスト| Proxy
    Proxy -->|静的・UIルーティング| Frontend
    Proxy -->|APIリクエスト (/api)| Backend
    
    Frontend -->|API 呼び出し| Backend
    Backend -->|SQL| Postgres
    Backend -->|連携| StickyNote
    Frontend -->|WebSocket等| StickyNote
```

## 2. ディレクトリ・ファイル構成と役割

プロジェクトのルートである `board-system/` 以下の主要な構成は以下のようになっています。

### ルートディレクトリ

- **`docker-compose.yml`**: ローカル開発用のDocker Compose設定です。データベース(`db`)、バックエンド(`backend`)、フロントエンド(`frontend`)、および外部の付箋システム(`sticky-note`)を一括で起動します。
- **`docker-compose.prod.yml` / `docker-compose.staging.yml`**: 本番環境・ステージング環境用のDocker Compose設定です。
- **`package.json`**: プロジェクト全体のスクリプトを定義しています。`npm run dev`でフロントエンドとバックエンドの起動を簡略化する用途で使われています。
- **`README.md` / `DEPLOY.md`**: プロジェクトの概要やデプロイに関するドキュメントが記載されています。

---

### 📁 `frontend/` (フロントエンド層)

Next.js 16 (App Router) と React 19、Tailwind CSS を利用したユーザーインターフェースの実装コードが配置されています。

- **`app/`**: Next.jsのルーティングの基盤です。各ディレクトリがURLパスに対応します。
  - **`taskboard/` / `admin/` / `main/` / `meeting/` / `morning/` / `personal/`**: それぞれ独立した画面（ボード機能）や管理画面のページです。
  - **`task/`**: 過去のタスク画面のURL。現在は`page.tsx`内で`/taskboard`へリダイレクトされるようになっています。
  - **`components/`**: 複数のページで使い回されるUIパーツ（ボタン、モーダルなど）が格納されています。
  - **`layout.tsx` / `globals.css`**: アプリ全体の共通レイアウトと、Tailwindを含むグローバルなスタイル定義ファイルです。
- **`package.json`**: フロントエンド専用の依存パッケージ（React, Next.js, framer-motion など）が定義されています。

---

### 📁 `backend/` (バックエンド層)

Python と FastAPI を使用したREST APIサーバーのコードが配置されています。

- **`app/`**: サーバーのメインコードが含まれています。
  - **`main.py`**: FastAPIアプリケーションのエントリーポイント（起動ファイル）です。
  - **`config.py`**: 環境変数や設定値の読み込みを行います。
  - **`db.py`**: データベース（PostgreSQL）への接続設定やセッション管理を行います。
  - **`routers/`**: URLエンドポイント（例: `/api/tasks` など）の定義とリクエストの受け付けを担当します。
  - **`services/`**: ビジネスロジック（データの加工や複雑な処理）を担当します。
  - **`models/`**: データベースのテーブル構造を定義する SQLAlchemy モデルです。
  - **`schemas/`**: Pydanticを用いたAPIのリクエスト・レスポンスの型定義・バリデーションを担当します。
  - **`ai/`**: OllamaなどのAIモデルとの連携機能が実装されています。
  - **`scheduler.py`**: 定期実行が必要なバックグラウンドタスクなどを定義していると想定されます。
- **`alembic/` & `alembic.ini`**: データベースのマイグレーション（テーブル定義のバージョン管理と変更の適用）ツールです。
- **`requirements.txt`**: バックエンドで必要なPythonライブラリの一覧です。
- **`Dockerfile`**: バックエンドをコンテナとしてビルドするための設定ファイルです。

---

### 📁 `nginx/` (インフラ・ルーティング層)

Webサーバー（リバースプロキシ）の設定が格納されています。

- **`nginx.conf` 等**: ユーザーからのリクエストを受け取り、パスに応じてフロントエンドのコンテナやバックエンドのAPIコンテナに正しく振り分ける（ルーティングする）ためのルールが定義されています。ステージングや本番など環境ごとの設定が存在します。

---

### 📁 `deploy/` (デプロイ・CI/CD層)

本番環境やステージング環境へアプリケーションを反映させるためのシェルスクリプト群です。

- **`deploy.sh` / `deploy-staging.sh` / `rollback.sh`**: コンテナの再ビルド、再起動、または問題発生時の切り戻し（ロールバック）を自動化するためのスクリプトです。

---

> [!TIP]
> 上記の構造から、Next.jsからバックエンドのFastAPIに通信を行い、バックエンドがPostgreSQLと通信するモダンな構成であることがわかります。UIの修正であれば主に `frontend/` を、APIやデータベースの追加であれば `backend/` を改修することになります。
