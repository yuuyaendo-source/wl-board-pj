# wl-sticky-note（付箋ボード）

Next.js、Express、Socket.ioを使用したリアルタイム協調型付箋ボードアプリケーション。プロジェクト名: **wl-sticky-note**。本番サーバ: **172.16.1.81** / **wl-sticky-note.local**

## 機能

- 📝 付箋の作成・編集・移動
- 🎨 9色のカラーパレット
- 🔗 付箋のグループ化
- 📌 付箋のピン留め
- 💾 ボードの保存・ダウンロード・復元
- 🔄 リアルタイム同期（複数ユーザー対応）
- 📱 レスポンシブデザイン
- 🖱️ ドラッグ&ドロップ対応

## 開発環境

### 必要なもの

- Node.js 18.x以上
- npm 9.x以上

### セットアップ

```bash
# 依存関係のインストール
npm install

# 開発サーバーの起動
npm run dev
```

ブラウザで [http://localhost:3000/board/test](http://localhost:3000/board/test) を開いてください。

## 本番環境へのデプロイ（Ubuntu Server）

### 前提条件

- Ubuntu Server（20.04 LTS以降推奨）
- SSHアクセス権限
- sudoコマンドの実行権限

### デプロイ手順

#### 1. サーバーにSSH接続

```bash
ssh user@172.16.1.81
# または
ssh user@wl-sticky-note.local
```

#### 2. 02_1_sticky-note のみ clone（wlinko-pj から sparse-checkout）

wlinko-pj リポジトリ全体ではなく、**02_1_sticky-note だけ**をサーバに取り出します。

```bash
sudo mkdir -p /var/www/wl-sticky-note
sudo chown $USER:$USER /var/www/wl-sticky-note
cd /var/www/wl-sticky-note

# wlinko-pj を sparse で clone（YOUR_ORG を実際の GitHub ユーザー/組織に置換）
git clone --filter=blob:none --sparse https://github.com/YOUR_ORG/wlinko-pj.git .
git sparse-checkout set 02_1_sticky-note
git checkout
```

→ `/var/www/wl-sticky-note/02_1_sticky-note/` 以下にだけファイルが展開されます。

#### 3. デプロイスクリプトの実行

```bash
cd /var/www/wl-sticky-note/02_1_sticky-note/src
chmod +x deploy.sh
./deploy.sh
```

このスクリプトは以下を自動で行います：
- システムアップデート
- Node.js、npm、PM2、Nginxのインストール
- プロジェクトの依存関係インストール
- Next.jsアプリケーションのビルド
- PM2でのアプリケーション起動
- Nginxの設定
- ファイアウォールの設定

#### 4. アクセス確認

デプロイ完了後、以下のURLでアクセスできます：
```
http://wl-sticky-note.local/board/test
http://172.16.1.81/board/test
```

### 初回デプロイ（02_1_sticky-note のみ・推奨）

前バージョンなしで新規デプロイする手順（wlinko-pj から 02_1_sticky-note だけ clone）は、プロジェクトルートの **`docs/デプロイ手順_初回.md`** を参照してください。

### 同一サーバで前バージョン残し・新バージョン追加でデプロイする場合

将来、旧版を残したまま新版を追加する場合は **`docs/デプロイ手順_バージョン併存.md`** を参照してください。

- バージョン別デプロイ用スクリプト: **`deploy-versioned.sh`**（例: `./deploy-versioned.sh v2 3001`）
- Nginx で旧・新を併存させる設定例: **`nginx.versioned.conf.example`**

### 運用コマンド

```bash
# アプリケーションのログ確認
pm2 logs wl-sticky-note

# アプリケーションの再起動
pm2 restart wl-sticky-note

# アプリケーションの停止
pm2 stop wl-sticky-note

# アプリケーションのステータス確認
pm2 status

# Nginxのステータス確認
sudo systemctl status nginx

# Nginxの再起動
sudo systemctl restart nginx
```

### トラブルシューティング

#### アプリケーションが起動しない場合

```bash
# PM2のログを確認
pm2 logs wl-sticky-note

# PM2を再起動
pm2 restart wl-sticky-note
```

#### Nginxエラーの場合

```bash
# Nginx設定のテスト
sudo nginx -t

# Nginxエラーログの確認
sudo tail -f /var/log/nginx/wl-sticky-note_error.log
```

#### ポートが使用中の場合

```bash
# ポート3000を使用しているプロセスを確認
sudo lsof -i :3000

# ポート80を使用しているプロセスを確認
sudo lsof -i :80
```

## プロジェクト構造

```
src/
├── app/                    # Next.js App Router
│   └── board/[id]/        # 動的ボードページ
├── components/            # Reactコンポーネント
│   ├── BoardCanvas.js    # メインボードキャンバス
│   ├── StickyNote.js     # 付箋コンポーネント
│   ├── Toolbar.js        # ツールバー
│   └── CommentListPanel.js  # コメント一覧
├── server.js             # Express + Socket.io サーバー
├── ecosystem.config.js   # PM2設定
├── nginx.conf           # Nginx設定
└── deploy.sh            # デプロイスクリプト
```

## 技術スタック

- **フロントエンド**: Next.js 16.x, React 19.x
- **バックエンド**: Express.js, Socket.io
- **プロセス管理**: PM2
- **Webサーバー**: Nginx
- **リアルタイム通信**: Socket.io

## ライセンス

Private

## 開発者

wl-sticky-note
