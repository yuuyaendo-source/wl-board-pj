# wl-sticky-note（付箋ボード）

リアルタイム協調型のブレインストーミング・付箋ボードアプリです。Next.js + Express + Socket.IO で構成され、複数人で同じボード上に付箋を追加・編集・移動できます。AI-Board・デスクトップアプリとの連携APIを提供します。

- **プロジェクト名**: wl-sticky-note
- **本番サーバ**: IP `172.16.1.81` / ドメイン `wl-sticky-note.local`
- **本番ボード（連携先）**: **http://wl-sticky-note.local/board/wl** … AI-Board・Desktopアプリの連携先。本番ではこのボードID `wl` を使用する。
- **Board System との本番同一サーバ運用**: 付箋ボードと Board System（Task / Personal / Meeting）を同一サーバで動かす場合は、**wlinko-pj ルートの [docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md)** に従う（02_1_sticky-note と board-system をまとめて clone・ビルド・Nginx 設定）。単体デプロイの場合は下記「本番デプロイ」を参照。
- **リポジトリ**: GitHub の **wlinko-pj** 内に 02_1_sticky-note があります。サーバでは sparse-checkout で 02_1_sticky-note と board-system の両方を取得してデプロイする構成も可。

---

## 主な機能

- **付箋** … 作成・編集・移動・9色のカラーパレット・ピン留め・ボードから削除
- **ボード** … 複数ボード対応・ボード名の保存・ダウンロード・インポート
- **協調** … Socket.IO によるリアルタイム同期（複数ユーザー同時編集）
- **グループ化** … 付箋のコメント一覧からグルーピング・解除
- **連携** … AI-Board への付箋送信、デスクトップアプリ向けサマリーAPI（新付箋通知）

---

## 必要な環境

- Node.js 18.x 以上
- npm 9.x 以上

---

## クイックスタート（ローカル開発）

アプリのソースは `src/` にあります。

```powershell
cd src
npm install
npm run dev
```

または:

```powershell
cd src
.\start_server.ps1
```

起動後、ブラウザで **http://localhost:3000** を開き、ボード一覧からボードを選ぶか、`/board/<ボードID>` にアクセスしてください。

---

## 本番デプロイ

- **付箋ボード＋Board System を同一サーバで運用する場合**: リポジトリルートの **[docs/本番デプロイ手順.md](../docs/本番デプロイ手順.md)** を参照（推奨。clone・付箋ボード deploy・Board System backend/frontend・Nginx の一連手順）。
- **付箋ボード単体のみデプロイする場合**: [docs/デプロイ手順.md](docs/デプロイ手順.md) を参照。サーバで 02_1_sticky-note のみ clone（sparse-checkout）、`src/deploy.sh` で Node.js / PM2 / Nginx のセットアップ〜起動。アクセス: http://wl-sticky-note.local

---

## プロジェクト構成

```
02_1_sticky-note/
├── README.md           # 本ファイル
├── docs/               # 設計書・デプロイ手順
│   ├── デプロイ手順.md   # 本番デプロイ（正規版）
│   ├── 本番連携の整理.md
│   └── AI-Board・Desktopアプリの開発の進め方.md
└── src/                # アプリ本体
    ├── app/            # Next.js App Router（画面）
    ├── components/     # React コンポーネント
    ├── server.js       # Express + Socket.IO サーバー
    ├── boards.json     # ボードデータ（自動作成）
    ├── package.json
    ├── deploy.sh       # 本番デプロイ用スクリプト
    └── README.md       # 開発・デプロイの詳細
```

---

## 環境変数

`src/.env` に以下を設定できます（任意）。`src/.env.example` をコピーして編集してください。

| 変数 | 説明 | 例 |
|------|------|-----|
| `PORT` | サーバーのポート | `3001` |
| `NODE_ENV` | 実行環境 | `production` |
| `AI_BOARD_URL` | AI-Board のベースURL（付箋連携用） | 本番: `http://wl-ai-board.local` / ローカル: `http://127.0.0.1:5000` |
| `BOARD_SYSTEM_API_URL` | Board System API の URL（連携用） | 本番: `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_BOARD_SYSTEM_URL` | Board System フロントの URL（ツールバー「Board System」のリンク先）。**ビルド時に埋め込まれるため変更時は再ビルド必須** | 本番: `http://wl-sticky-note.local/boards` |

---

## 提供API（他システム連携用）

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/health` | 死活確認（Express API 稼働確認用） |
| GET | `/api/boards/:id/summary` | ボードのサマリー（付箋数・最終付箋時刻）。Desktopアプリのポーリング用 |
| GET | `/api/boards/:id/notes` | **付箋全件取得**。`{ boardId, notes: [{ id, text, author, createdAt }] }` を返す。AI-Board の「付箋を全件取得」ボタン用。 |
| POST | `/api/sticky_notes` | 付箋を追加・更新。AI-Board のカメラ検知付箋送信用 |
| POST | `/api/boards/:id/clear` | 指定ボードの付箋・線を全削除 |

- **本番連携先ボード**: `wl` → http://wl-sticky-note.local/board/wl
- **本番と AI-Board・Desktop の連携**: [docs/本番連携の整理.md](docs/本番連携の整理.md) を参照

---

## 関連アプリ

- **AI-Board** … 付箋をカメラで検知して本アプリに送信、AIコメント・音声生成。また `GET /api/boards/:id/notes` で付箋を全件取得し、ローテーション表示する「付箋を全件取得」ボタンを提供。
- **Wonder Rinko Desktop App** … 付箋ボードをポーリングし、新付箋時にトースト通知

---

## ドキュメント

| ドキュメント | 内容 |
|--------------|------|
| [docs/デプロイ手順.md](docs/デプロイ手順.md) | 本番デプロイ（正規版・唯一の手順） |
| [docs/本番連携の整理.md](docs/本番連携の整理.md) | 本番と AI-Board・Desktop の連携・チェックリスト |
| [docs/AI-Board・Desktopアプリの開発の進め方.md](docs/AI-Board・Desktopアプリの開発の進め方.md) | Desktop 配布・AI-Board の本番連携 |
| [docs/開発の進め方.md](docs/開発の進め方.md) | ローカル開発フロー・本番反映 |
| [src/README.md](src/README.md) | 開発・デプロイの詳細・プロジェクト構造 |
