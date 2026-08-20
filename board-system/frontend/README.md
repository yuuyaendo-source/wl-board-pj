# Board System Frontend (Wonder Rinko)

Next.js (App Router) + Tailwind CSS + Framer Motion。4ボード View と D&D、1行入力。**本番では basePath `/boards` でビルドし、同一サーバの付箋ボードと Nginx で共存。** 詳細は [docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md) を参照。

## セットアップ

**必ず `frontend` ディレクトリ内で npm を実行してください。** 親の `board-system` で実行すると `tailwindcss` が解決されずエラーになることがあります。

```bash
cd board-system/frontend
npm install
cp .env.local.example .env.local   # 必要に応じて NEXT_PUBLIC_API_URL を編集
npm run dev
```

- フロント: <http://localhost:3000（単体）または> <http://localhost:3001（付箋ボード併用時）>
- **各ボードはバックエンドが起動していないとエラーになります。** 先に `board-system/backend` で `uvicorn app.main:app --port 8000` を起動してください。トップページで「API 接続済み」と表示されれば OK。
- ポート 8000 が使用中な場合: `uvicorn app.main:app --port 8001` で起動し、`.env.local` に `NEXT_PUBLIC_API_URL=http://localhost:8001` を設定。

## ボード（開発状況・引き継ぎ用）

| パス | 説明 |
| ------ | ------ |
| `/main` | Main Board（フリーキャンバス）。付箋をドラッグで配置。1行投稿。AI 仕分け付箋は ✨。 |
| `/taskboard` | **Task Board（5列）**。左から「アイデア」「短期タスク」「長期タスク」「重要」「完了」。付箋ボードから取り込むはメニューバー。ゴミ箱・パーソナルへコピー（メンバードロップ）・**チームへ一括コピー（チームドロップ: 👥 ネットワーク等）**は sticky。付箋色：黄=未引き取り、緑=誰かが引き取り中、灰=誰かが Done。引き取り者を短縮名（例: 浅）で表示。 |
| `/personal` | **Personal Board**。3レーン（Today / タスク / Done）。1行入力で投稿。付箋色：**緑**=タスクボードから取り込んだもの、**青**=パーソナルで投稿したもの、**灰**=Done。ゴミ箱・タスクリリースは横並び。タスクリリースで Personal 配置を削除すると Task ボードに戻る。 |
| `/meeting` | **Meeting ボード**。参加者ごとに MORNING スナップショット。毎朝 10:15 反映 + ニュース要約。「今の Today を反映」テストボタンあり。 |
| `メンバー・チーム管理` | ヘッダーの「メンバー管理」ボタンで開く 2 タブ形式ダイアログ。**メンバー管理**（ユーザー登録・編集・所属チーム選択・削除）と**チーム管理**（チーム新規追加・チーム名変更・チーム削除・所属メンバー確認）を提供。 |
| `/admin/system` | LLM スロット切替などの管理 UI |

- 本番では basePath `/boards` のため、実際の URL は `/boards`、`/boards/taskboard`、`/boards/personal/:slug`、`/boards/meeting`。

## 環境変数

| 変数 | 説明 | 例 |
| ------ | ------ | ----- |
| `NEXT_PUBLIC_API_URL` | バックエンド API の URL | 開発: `http://localhost:8000`、本番: `https://wlboardsys.internal.wonder-link.com/api/bs` |
| `NEXT_PUBLIC_LEGACY_BOARD_URL` | 付箋ボード（02_1）の URL（Task の付箋取り込み用） | 本番: `https://wlboardsys.internal.wonder-link.com` |

本番ビルド時は `NEXT_PUBLIC_API_URL` を本番の API ベース URL に設定すること。`next.config.ts` で `NODE_ENV=production` 時に basePath `/boards` が自動付与される。

## 技術

- Next.js 16 (App Router)
- Tailwind CSS v4
- Framer Motion（アニメーション）
- HTML5 D&D（Task 列・Personal レーン・ゴミ箱・タスクリリース・メンバードロップ）
- カスタム DnD 型 `application/x-board-task-release`（タスクリリース可否を dragover で判定するため）

## 引き継ぎ・本番

- 本番デプロイ・更新手順: リポジトリルート [docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md) の「9. 今後の更新」を参照。
- ビルド前に `rm -rf .next` を推奨。PM2 で `board-system-frontend` として `npm start`（ポート 3001）を運用。
