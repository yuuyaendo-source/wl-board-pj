# Board System (Wonder Rinko) — V2

改善指示書9に基づく「統合ボードシステム」の新規開発用リポジトリ。  
既存の `02_1_sticky-note` とは分離し、ここを V2 としてクリーンに開発する。

## 想定構成

```
board-system/
├── backend/          # FastAPI + SQLAlchemy (SQLite → PostgreSQL)
├── frontend/         # Next.js（後で作成）
├── docker-compose.yml # （後で作成）
└── README.md
```

## 現状

- **backend/**: フェーズ1〜3 完了（FastAPI + SQLAlchemy + Alembic + AI Worker）。
- **frontend/**: フェーズ4 完了（Next.js App Router + Tailwind + Framer Motion、4ボード View）。
- **docker-compose.yml**: 未作成

## 起動の順序（各ボードを開く前に必須）

**フロントだけでは各ボードでエラーになります。先にバックエンドを起動してください。**

1. **バックエンド**（ターミナル1）
   ```powershell
   cd board-system/backend
   .venv\Scripts\Activate.ps1
   uvicorn app.main:app --reload --port 8000
   ```
   **ポート 8000 が使用中でエラーになる場合**: 別ポートで起動し、フロントの `.env.local` で `NEXT_PUBLIC_API_URL=http://localhost:8001` に変更。
   ```powershell
   uvicorn app.main:app --reload --port 8001
   ```
2. **フロントエンド**（ターミナル2）
   ```powershell
   cd board-system/frontend
   npm run dev
   ```
3. ブラウザで http://localhost:3000 を開く。トップで「API 接続済み」と出れば OK。

**付箋ボード（旧 02_1）と併用する場合**: 02_1 を 3000、board-system フロントを 3001 で起動（`npm run dev -- -p 3001`）。02_1 の `.env` に `NEXT_PUBLIC_BOARD_SYSTEM_URL=http://localhost:3001`、board-system の `.env.local` に `NEXT_PUBLIC_LEGACY_BOARD_URL=http://localhost:3000` を設定すると、相互に「Board System を開く」「付箋ボード（旧）を開く」で行き来できる。

## ここまでで完了したこと

| フェーズ | 内容 | 状態 |
|----------|------|------|
| 1 | DB（SQLAlchemy, Alembic, users / sticky_notes / board_placements） | 完了 |
| 2 | Backend API（CRUD、ボード間移動、GET /boards/*） | 完了 |
| 3 | AI Worker（Auto-Triage、Matrix Scoring、Daily Reset API） | 完了 |
| 4 | Frontend（4ボード View、D&D、1行入力、API エラー表示） | 完了 |

**必須の残タスクはありません。**

## 任意・次のステップ候補

開発プラン上の「任意」または「後で」とされていたもの、および運用で便利なものを挙げます。

| 候補 | 説明 | 優先度の目安 |
|------|------|----------------|
| **docker-compose** | バックエンド＋フロントを一括起動。本番に近い環境の確認用。 | 高 |
| **シードデータ** | 開発用ユーザー数名＋サンプル付箋を DB に投入。Morning や Personal の確認がしやすい。 | 中 |
| **認証** | owner_id を body/query で渡す現状から、ログイン・セッションで「自分」を決める方式へ。 | 中〜後回し |
| **Morning 8:50 同期** | 「毎朝 8:50 にスナップショット」の仕様確定（API 時刻トリガー or フロント表示）。 | 低 |
| **PostgreSQL 対応** | 本番用に DATABASE_URL を postgresql+asyncpg にし、必要なら Alembic で検証。 | 本番時 |

次に進めるなら、**docker-compose** か **シードデータ** がおすすめです。

## 開発プラン（詳細）

`docs/開発・改善プラン/改善指示書9_開発プラン.md` を参照。
