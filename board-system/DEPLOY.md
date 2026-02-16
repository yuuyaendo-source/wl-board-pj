# 本番デプロイメント手順 (Docker / Blue-Green Deployment)

本システム（Sticky Note + Board System）をDocker化し、ブルーグリーン・デプロイメントで運用する手順です。

**詳細な手順（前提条件・リポジトリ配置・Nginx・マイグレーション・ロールバック）はプロジェクトルートの [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) を参照してください。** 以下は構成とこのディレクトリでの操作の要約です。

## 1. 構成概要

- **Sticky Note**: Node.js + Express + Socket.IO (Port 3000)
- **Board System Backend**: FastAPI (Port 8000)
- **Board System Frontend**: Next.js (Port 3000 -> 3001)
- **Database**: PostgreSQL (Port 5432)
- **Nginx**: リバースプロキシ & Blue/Green 切り替え (Port 80)

本番環境では、`nginx` が `wl-sticky-note.local` (Port 80) で待ち受け、背後のDockerコンテナ（BlueまたはGreen）に振り分けます。

## 2. ディレクトリ構成

```
board-system/
├── docker-compose.prod.yml  # アプリケーション（Blue/Green）定義
├── docker-compose.db.yml    # データベース定義（永続化・共有）
├── .env.example             # 環境変数テンプレート
├── deploy/
│   ├── deploy.sh            # デプロイスクリプト
│   └── rollback.sh          # ロールバックスクリプト
└── nginx/
    └── nginx.conf           # Nginx設定（パス振り分け）
```

## 3. 初回セットアップ

1. **環境変数の設定**
   ```bash
   cp .env.example .env
   # .env を編集して DATABASE_URL, GEMINI_API_KEY 等を設定
   ```

2. **ネットワークとDBの起動**
   DBはBlue/Green切り替えの影響を受けないよう、独立して起動します。
   ```bash
   # 専用ネットワーク作成
   docker network create linko-net
   
   # DB起動
   docker compose -f docker-compose.db.yml up -d
   ```

3. **Nginx設定の配置**
   `/etc/nginx/nginx.conf` を `board-system/nginx/nginx.conf` の内容で更新するか、include されるように設定します。
   また、`/etc/nginx/conf.d/active_env.conf` が書き込み可能であることを確認してください（`deploy.sh` が書き換えます）。

## 4. デプロイ実行 (Blue/Green)

コードを更新した後、以下のコマンドを実行します。

```bash
cd board-system/deploy
./deploy.sh
```

**スクリプトの動作:**
1. 現在稼働していない側の環境（Blue or Green）を特定
2. 新しいコードでDockerイメージをビルド＆起動
3. ヘルスチェックを実行（DB接続、API応答確認）
4. 成功したら Nginx の向き先 (`active_env.conf`) を切り替え
5. Nginx をリロード
6. 旧環境のコンテナを停止

## 5. ロールバック

デプロイ後に問題が発生した場合、直前の環境に戻します。

```bash
cd board-system/deploy
./rollback.sh
```

## 6. 注意事項

- **マイグレーション**: 初回デプロイ後、およびスキーマ変更をデプロイした後に、backend コンテナで `alembic upgrade head` を実行してください。例: `docker exec -it linko-backend-blue alembic upgrade head`。詳しくは [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) を参照。
- **CATO証明書**: Dockerビルド時に `cato-ca.crt` を読み込んでいます。社内ネットワークでビルドが失敗する場合は、証明書が期限切れでないか、パスが正しいか確認してください。
- **データ永続化**:
  - DBデータ: `docker-compose.db.yml` の `postgres_data` ボリューム
  - Sticky Noteデータ: `docker-compose.prod.yml` の `sticky_data` ボリューム
- **ログ確認**:
  ```bash
  # 現在の環境を確認
  cat /etc/nginx/conf.d/active_env.conf
  
  # ログを表示 (例: Blue環境の場合)
  docker logs -f linko-backend-blue
  ```

## 7. トラブルシューティング

### ローカル開発環境でのDockerビルド
CATOネットワークなどのSSLインスペクション環境下やプロキシ環境下において、`docker compose build` 時に `npm install` や `apt-get` が極端に遅くなる、または停止する場合は、BuildKitを無効化してビルドを試してください。

**Windows (PowerShell):**
```powershell
$env:DOCKER_BUILDKIT=0
docker compose build --no-cache
```

**Linux / Mac:**
```bash
DOCKER_BUILDKIT=0 docker compose build --no-cache
```
