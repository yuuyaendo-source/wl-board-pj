# Board System (Wonder Rinko)

改善指示書9〜11に基づく「統合ボードシステム」。付箋ボード（02_1）と連携し、Main / Task / Personal / Morning の 4 ボードを提供。**本番は付箋ボードと同一サーバ（wl-sticky-note.local）でデプロイ可能。** 詳細は [docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md) を参照。

## 構成

```
board-system/
├── backend/     # FastAPI + SQLAlchemy (SQLite) + AI Worker
├── frontend/    # Next.js App Router + Tailwind + Framer Motion
└── README.md
```

## 開発状況（引き継ぎ用・2026年2月時点）

| 項目 | 状態 | 備考 |
|------|------|------|
| バックエンド API | 完了 | users / sticky_notes / board_placements、GET /boards/*、AI（triage / matrix / daily_reset） |
| Task ボード | 完了 | **5列**（アイデア・短期タスク・長期タスク・重要・完了）。付箋色（黄/緑/灰）、引き取り者短縮名表示。付箋ボードから取り込むはメニューバー配置。 |
| Personal ボード | 完了 | 3レーン（Today / タスク / Done）。付箋色：**緑**=タスク由来、**青**=パーソナル投稿、**灰**=Done。ゴミ箱・タスクリリースは横並び。Personal で Done にすると Task の「完了」に連動。Done→タスクに戻す対応済み。 |
| Meeting ボード | 完了 | 毎朝 **10:15** に Personal の Today を MORNING にコピー（cron で `POST /daily_reset/sync_to_morning`）。テスト用「今の Today を反映」ボタンあり。 |
| 本番デプロイ | 完了 | 同一サーバで付箋ボード（3000）＋ API（8000）＋ フロント（3001）、Nginx で `/boards` に配信。 |

- **設計・改善履歴**: `docs/開発・改善プラン/改善指示書9.md` 〜 `改善指示書11.md`
- **必須の残タスクはなし。** 認証・PostgreSQL・docker-compose 等は任意。

## 起動の順序（開発時）

**バックエンドを先に起動すること。** フロントだけでは各ボードで API エラーになります。

1. **バックエンド**（ターミナル1）
   ```bash
   cd board-system/backend
   # Windows: .venv\Scripts\Activate.ps1
   source .venv/bin/activate   # Linux/macOS
   uvicorn app.main:app --reload --port 8000
   ```
2. **フロントエンド**（ターミナル2）
   ```bash
   cd board-system/frontend
   npm install
   npm run dev
   # 付箋ボード併用時: npm run dev -- -p 3000
   ```
3. ブラウザで http://localhost:3000 を開く（3001 で起動した場合は http://localhost:3001）。トップで「API 接続済み」と出れば OK。

**付箋ボード（02_1）と併用する場合**: 02_1 を 3000、board-system フロントを 3001 で起動。02_1 の `.env` に `NEXT_PUBLIC_BOARD_SYSTEM_URL=http://localhost:3001`、board-system の `.env.local` に `NEXT_PUBLIC_LEGACY_BOARD_URL=http://localhost:3000` を設定すると相互リンクで行き来可能。

## ローカルで Docker を動かす（付箋ボード＋Board System まとめて）

Docker で付箋ボード・Board System・PostgreSQL をまとめて起動して確認できます。**cato-ca.crt は不要**（無くてもビルド可能）。

```powershell
cd board-system
copy .env.example .env   # 任意: GEMINI_API_KEY を設定
docker compose up -d --build
docker exec -it linko-backend alembic upgrade head   # 初回のみ
```

- **Board System**: http://localhost:3010  
- **付箋ボード**: http://localhost:3011  
- **停止**: `docker compose down`  

詳細は [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) の「ローカルで Docker を動かして確認する」を参照。

## 本番への反映（コード更新時）

リポジトリルートの [docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md) の **「9. 今後の更新」** に従う。要約すると:

- `git pull` のあと、**backend**: `pip install -r requirements.txt` → `alembic upgrade head` → `sudo systemctl restart board-system-api`
- **frontend**: `npm install` → `rm -rf .next` → `npm run build` → `pm2 restart board-system-frontend --update-env`

サーバで `releases` 配下に置いている場合はパスを `releases/board-system/backend` および `releases/board-system/frontend` に読み替える。

## サブディレクトリ

| ディレクトリ | README | 内容 |
|--------------|--------|------|
| [backend/](backend/README.md) | あり | FastAPI、API 一覧、AI Worker、マイグレーション |
| [frontend/](frontend/README.md) | あり | Next.js、ボード別パス、環境変数 |

## 関連ドキュメント

- [docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md) — 付箋ボード＋Board System の本番デプロイ・運用・トラブルシューティング
- [docs/起動手順.md](../docs/起動手順.md) — 開発時の起動順序・ポート一覧
- [docs/開発・改善プラン/改善指示書11.md](../docs/開発・改善プラン/改善指示書11.md) — Task/Personal UI・機能の仕様
