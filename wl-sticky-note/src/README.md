# wl-sticky-note（付箋ボード）— アプリ本体

Next.js、Express、Socket.IO を使用したリアルタイム協調型付箋ボードアプリケーション。

- **プロジェクト名**: wl-sticky-note
- **本番サーバ**: 172.16.1.84 / wl-ai-board.internal.wonder-link.co.jp

---

## 機能

- 付箋の作成・編集・移動・削除（ボードから削除）
- 9色のカラーパレット・ピン留め
- 付箋のグループ化
- ボード名の保存・ボードのダウンロード・インポート
- リアルタイム同期（複数ユーザー対応）
- AI-Board・Desktopアプリとの連携API
- **Board System（4ボード）へのリンク**: トップページとボード内ツールバー（📋）から、Board System (Wonder Rinko) を別タブで開ける。`.env` の `NEXT_PUBLIC_BOARD_SYSTEM_URL` でリンク先を変更可能（未設定時は https://wl-ai-board.internal.wonder-link.co.jp/boards）。**本番では同一 FQDN の `/boards` に設定し、必ず再ビルドすること。** 付箋ボードと Board System を同一サーバでデプロイする手順はリポジトリルート [docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md) を参照。

---

## 開発環境

### 必要なもの

- Node.js 18.x 以上
- npm 9.x 以上

### セットアップ・起動

```bash
npm install
npm run dev
```

ブラウザで [http://localhost:3000](http://localhost:3000) を開いてください。ボード例: [http://localhost:3000/board/wl](http://localhost:3000/board/wl)

---

## 本番デプロイ

- **付箋ボード＋Board System を同一サーバで運用**: リポジトリルートの **[docs/本番デプロイ手順.md](../../docs/本番デプロイ手順.md)** を参照（02_1_sticky-note と board-system の clone・ビルド・PM2・Nginx の一連手順）。
- **付箋ボード単体**: プロジェクトルート [docs/デプロイ手順.md](../docs/デプロイ手順.md) を参照。

### 単体デプロイの手順の概要

1. サーバに SSH 接続
2. `/var/www/wl-sticky-note` に wlinko-pj を sparse-checkout で clone（02_1_sticky-note のみ）
3. 本ディレクトリ（`02_1_sticky-note/src`）で `./deploy.sh` を実行

`deploy.sh` は Node.js / PM2 / Nginx のインストール、ビルド、起動、Nginx 設定まで行います。

### 運用コマンド

```bash
pm2 logs wl-sticky-note    # ログ確認
pm2 restart wl-sticky-note # 再起動
pm2 stop wl-sticky-note    # 停止
sudo systemctl status nginx # Nginx 状態
```

### 更新時の反映

```bash
cd /var/www/wl-sticky-note
git pull
cd 02_1_sticky-note/src   # releases の場合は releases/02_1_sticky-note/src
rm -rf .next
npm install
npm run build
pm2 restart wl-sticky-note --update-env
```

`.env` の `NEXT_PUBLIC_*` を変更した場合は必ず再ビルドすること。

---

## プロジェクト構造

```
src/
├── app/                    # Next.js App Router
│   ├── page.js            # ボード一覧
│   └── board/[id]/        # 動的ボードページ
├── components/             # React コンポーネント
│   ├── BoardCanvas.js     # メインボードキャンバス
│   ├── StickyNote.js      # 付箋コンポーネント
│   ├── Toolbar.js         # ツールバー
│   ├── CommentListPanel.js
│   └── ...
├── server.js               # Express + Socket.IO サーバー
├── ecosystem.config.js     # PM2 設定
├── nginx.conf              # Nginx 設定
├── deploy.sh               # デプロイスクリプト
└── package.json
```

---

## 技術スタック

- **フロントエンド**: Next.js 16.x, React 19.x
- **バックエンド**: Express.js, Socket.IO
- **プロセス管理**: PM2
- **Webサーバー**: Nginx
