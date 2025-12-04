# ブレインストーミングアプリ

Next.js、Express、Socket.ioを使用したリアルタイム協調型ブレインストーミングアプリケーション。

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
ssh user@your-server-ip
```

#### 2. プロジェクトディレクトリの準備

```bash
# プロジェクト用ディレクトリを作成
sudo mkdir -p /var/www
cd /var/www

# GitHubからクローン（または他の方法でファイルを転送）
sudo git clone https://github.com/wonder-link-dev/Asakawa-lab.git
cd Asakawa-lab/02_Projects/02_1_App_brain-storming/src

# 所有者を現在のユーザーに変更
sudo chown -R $USER:$USER /var/www/Asakawa-lab
```

#### 3. デプロイスクリプトの実行

```bash
# スクリプトに実行権限を付与
chmod +x deploy.sh

# デプロイ実行
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
http://[サーバーのIPアドレス]/board/test
```

### 運用コマンド

```bash
# アプリケーションのログ確認
pm2 logs brainstorming-app

# アプリケーションの再起動
pm2 restart brainstorming-app

# アプリケーションの停止
pm2 stop brainstorming-app

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
pm2 logs brainstorming-app

# PM2を再起動
pm2 restart brainstorming-app
```

#### Nginxエラーの場合

```bash
# Nginx設定のテスト
sudo nginx -t

# Nginxエラーログの確認
sudo tail -f /var/log/nginx/brainstorming_error.log
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

wonder-link-dev/Asakawa-lab
