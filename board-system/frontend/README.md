# Board System Frontend (Wonder Rinko)

Next.js (App Router) + Tailwind CSS + Framer Motion。4ボード View と D&D、1行入力。

## セットアップ

**必ず `frontend` ディレクトリ内で npm を実行してください。** 親の `board-system` で実行すると `tailwindcss` が解決されずエラーになります。

```bash
cd board-system/frontend
npm install
cp .env.local.example .env.local   # 必要に応じて NEXT_PUBLIC_API_URL を編集
npm run dev
```

ルート（board-system）から起動する場合:

```bash
cd board-system
npm run dev
```
（ルートの package.json が `cd frontend && npm run dev` を実行します）

- フロント: http://localhost:3000
- **各ボードはバックエンドが起動していないとエラーになります。** 先に `board-system/backend` で `uvicorn app.main:app --port 8000` を起動してください。トップページで「API 接続済み」と表示されれば OK。
- **ポート 8000 が使用中**（別アプリや前回の uvicorn が残っている）場合: `uvicorn app.main:app --port 8001` で起動し、`frontend/.env.local` に `NEXT_PUBLIC_API_URL=http://localhost:8001` を設定してフロントを再起動。

## ボード

| パス | 説明 |
|------|------|
| `/main` | Main Board（**フリーキャンバス**）。ホワイトボード形式で付箋を好きな位置に配置。ドラッグ終了時に座標を API で保存。1行投稿。AI 仕分け付箋は ✨。 |
| `/task` | Task Board。4象限（緊急・重要）。D&D で象限変更。 |
| `/personal` | Personal Board。3レーン（Inbox / Today / Done）。1行入力で Inbox に追加。D&D でレーン移動。`?owner_id=1` で所有者指定。 |
| `/morning` | Morning Meeting。参加者（users）ごとに Today レーンのスナップショット一覧。 |

## 技術

- Next.js 16 (App Router)
- Tailwind CSS v4
- Framer Motion（アニメーション）
- HTML5 D&D（Personal/Task のレーン・象限へのドロップ）
- Framer Motion の drag（Main Board のフリーキャンバス。React 18 対応）
