# wl-sticky-note（付箋ボード）— アプリ本体

Next.js、Express、Socket.IO を使用したリアルタイム協調型付箋ボードアプリケーション。

- **プロジェクト名**: wl-sticky-note
- **本番サーバ**: 172.16.1.81 / wl-sticky-note.local

---

## 機能

- 付箋の作成・編集・移動・削除（ボードから削除）
- 9色のカラーパレット・ピン留め
- 付箋のグループ化
- ボード名の保存・ボードのダウンロード・インポート
- リアルタイム同期（複数ユーザー対応）
- AI-Board・Desktopアプリとの連携API

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

**正規版のデプロイはプロジェクトルートの [docs/デプロイ手順.md](../docs/デプロイ手順.md) を参照してください。**

### 手順の概要

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
cd 02_1_sticky-note/src
npm install
npm run build
pm2 restart wl-sticky-note
```

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
