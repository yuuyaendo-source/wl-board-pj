# wl-sticky-note（付箋ボード）

リアルタイム協調型のブレインストーミング・付箋ボードアプリです。Next.js + Express + Socket.IO で構成され、複数人で同じボード上に付箋を追加・編集・移動できます。AI-Board・デスクトップアプリとの連携APIを提供します。

- **プロジェクト名**: wl-sticky-note
- **本番サーバ**: IP `172.16.1.81` / ドメイン `wl-sticky-note.local`
- **本番ボード（連携先）**: **http://wl-sticky-note.local/board/wl** … AI-Board・Desktopアプリの連携先。本番ではこのボードID `wl` を使用する。
- **リポジトリ**: GitHub の **wlinko-pj** 内に 02_1_sticky-note がある。サーバでは 02_1_sticky-note のみ clone してデプロイ（`docs/デプロイ手順_初回.md` 参照）。

## 主な機能

- **付箋** … 作成・編集・移動・9色のカラーパレット・ピン留め
- **ボード** … 複数ボード対応・保存・ダウンロード・復元
- **協調** … Socket.IO によるリアルタイム同期（複数ユーザー同時編集）
- **グループ化** … 付箋のコメント一覧からグルーピング・解除
- **連携** … AI-Board への付箋通知、デスクトップアプリ向けサマリーAPI

## 必要な環境

- Node.js 18.x 以上
- npm 9.x 以上

## クイックスタート

アプリのソースは `src/` にあります。

```powershell
cd src
npm install
npm run dev
```

または PowerShell から:

```powershell
cd src
.\start_server.ps1
```

起動後、ブラウザで **http://localhost:3000** を開き、ボード一覧からボードを選ぶか、`/board/<ボードID>` にアクセスしてください。  
**CATO 接続の他PCから**: 開発PCの localhost = **172.16.1.251** なので、**http://172.16.1.251:3000** でアクセス可能。詳細は `docs/開発ドキュメント/開発環境_CATO.md`（プロジェクトルート）を参照。

## プロジェクト構成

```
02_1_sticky-note/
├── README.md           # 本ファイル
├── docs/               # 設計書・指示書
│   └── 01_4_ブレストアプリ_AI指示用_ver1.1.md
└── src/                # アプリ本体
    ├── app/            # Next.js App Router（画面）
    ├── components/     # React コンポーネント
    ├── server.js       # Express + Socket.IO サーバー
    ├── boards.json     # ボードデータ（自動作成）
    ├── package.json
    ├── start_server.ps1
    └── README.md       # 詳細な開発・デプロイ手順
```

詳細な開発手順・デプロイ・プロジェクト構造は **`src/README.md`** を参照してください。

## 環境変数

`src/.env` に以下を設定できます（任意）。`src/.env.example` をコピーして編集してください。

| 変数 | 説明 | 例 |
|------|------|-----|
| `PORT` | サーバーのポート | `3000` |
| `NODE_ENV` | 実行環境 | `production` |
| `AI_BOARD_URL` | AI-Board のベースURL（付箋連携用） | `https://127.0.0.1:5000` |

## 提供API（他システム連携用）

| メソッド | パス | 説明 |
|----------|------|------|
| GET | `/api/boards/:id/summary` | ボードのサマリー（付箋数・最終付箋時刻）。デスクトップアプリのポーリング用 |
| POST | `/api/sticky_notes` | 付箋を追加・更新。AI-Board のカメラ検知付箋送信用 |
| POST | `/api/boards/:id/clear` | 指定ボードの付箋・線を全削除 |

- **本番連携先ボード**: `wl` → http://wl-sticky-note.local/board/wl（AI-Board・Desktopアプリの連携先）
- **サマリー例**: `GET /api/boards/wl/summary` → `{ "boardId", "notesCount", "lastNoteAt" }`
- **本番と AI-Board・Desktop の連携の整理**: **`docs/本番連携の整理.md`** を参照（現状・やりたいこと・チェックリスト・通知が届かないときの切り分け）。
- **付箋追加**: `POST /api/sticky_notes` に `{ "boardId": "wl", "note": { "id", "text", "author", ... } }` を送信

## 関連リポジトリ・アプリ

- **AI-Board** … 付箋をカメラで検知して本アプリに送信、AIコメント生成
- **Wonder Rinko Desktop App** … 付箋ボードをポーリングし、新付箋時にトースト通知

## ドキュメント

- **開発の進め方（ローカル・本番の整理）**: `docs/開発の進め方.md` … ローカルと本番の役割、開発フロー、本番反映手順、連携アプリの環境切り替え
- **AI-Board・Desktopアプリの開発の進め方**: `docs/AI-Board・Desktopアプリの開発の進め方.md` … Desktop の本番連携確認とメンバー配布、AI-Board の本番連携を確認しながらの開発
- アプリ設計・機能一覧: `docs/01_4_ブレストアプリ_AI指示用_ver1.1.md`
- **デプロイ（初回・02_1_sticky-note のみ）**: `docs/デプロイ手順_初回.md`（wlinko-pj から 02_1_sticky-note だけ clone してサーバにデプロイ）
- デプロイ（将来のバージョン併存）: `docs/デプロイ手順_バージョン併存.md`
- 開発・デプロイの詳細: `src/README.md`
