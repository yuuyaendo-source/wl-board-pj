# 本番デプロイ手順（Docker）

付箋ボード（02_1_sticky-note）と Board System（Wonder Rinko）を **Docker** で本番デプロイする手順です。  
Blue/Green デプロイにより、切り替え時にダウンタイムを抑えられます。

- **非 Docker でデプロイする場合**（PM2 + systemd + Nginx）は [本番デプロイ手順.md](本番デプロイ手順.md) を参照してください。

---

## サーバ構成（デプロイ計画）

| 項目 | 現行本番 | 新規本番（本手順の対象） |
|------|----------|---------------------------|
| **ホスト** | Windows Server 2022（Hyper-V） | 同一 |
| **ゲスト OS** | ubuntu-ja-22.04-desktop-amd64 | **ubuntu-24.04.3-live-server-amd64** |
| **IP アドレス** | （既存） | **172.16.1.83** |

新サーバ（172.16.1.83）に Ubuntu 24.04 をインストールしたうえで、下記の前提条件・手順に従ってデプロイします。

### 仮想マシン（VM）のリソース目安

| リソース | 最小 | 推奨 | 備考 |
|----------|------|------|------|
| **メモリ** | 2 GB | **4 GB** | PostgreSQL + 3 コンテナ（backend / frontend / sticky-note）+ OS。余裕を持たせるなら 4 GB。 |
| **ストレージ** | 40 GB | **60〜80 GB** | OS 約 10〜15 GB、Docker イメージ・レイヤ 約 5〜10 GB、PostgreSQL・付箋データの増分とログ用に 20 GB 以上あると安心。 |

- ユーザー数や付箋数が多く増える見込みなら、メモリ 8 GB・ストレージ 100 GB 程度を検討してください。
- スワップは 2 GB 程度確保しておくと、メモリ不足時の安定性が上がります。

---

## 現状の構成（把握用）

| 項目 | 内容 |
|------|------|
| **リポジトリ** | wlinko-pj（**02_1_sticky-note** と **board-system** の両方が必要） |
| **Docker 定義** | `board-system/docker-compose.prod.yml`（アプリ Blue/Green）、`board-system/docker-compose.db.yml`（PostgreSQL） |
| **付箋ボード** | `02_1_sticky-note/src/Dockerfile`。compose から `build: ../02_1_sticky-note/src` で参照 |
| **Board System** | `board-system/backend/Dockerfile`、`board-system/frontend/Dockerfile` |
| **DB** | Docker では **PostgreSQL**（本番非 Docker 手順の SQLite とは別） |
| **リバースプロキシ** | ホストの **Nginx** が Port 80 で受け、`active_env.conf` で Blue/Green のポートに振り分け |

### URL の違い（Docker 版 vs 非 Docker 版）

| 用途 | 非 Docker（本番デプロイ手順.md） | Docker（本手順） |
|------|----------------------------------|------------------|
| 付箋ボード | http://wl-sticky-note.local/ | http://wl-sticky-note.local/**board/** |
| Board System フロント | http://wl-sticky-note.local/**boards**/ | http://wl-sticky-note.local/**/** |
| Board System API | http://wl-sticky-note.local/**boards-api**/ | http://wl-sticky-note.local/**api/bs**/ |

Docker 版では Nginx が「`/` → Board System フロント」「`/board/` → 付箋ボード」「`/api/bs/` → Board System API」となっています。

---

## クイックチェック

| 状況 | やること |
|------|----------|
| **初回デプロイ** | 下記 **1. 前提条件** 〜 **5. 初回デプロイ実行** を順に実施 |
| **コード更新の反映** | **6. 通常のデプロイ（Blue/Green）** の手順を実行 |
| **問題発生時** | **7. ロールバック** を実行 |

---

## ローカルで Docker を動かして確認する

本番デプロイの前に、手元の PC で Docker 構成を動かして確認できます。**Nginx は不要**で、`board-system/docker-compose.yml`（ローカル用）を使います。

### 前提

- Docker Desktop（または Docker Engine + Compose）がインストール済み
- リポジトリを clone 済みで、**02_1_sticky-note** と **board-system** の両方があること

### 手順

1. **環境変数（任意）**  
   Board System の AI 機能を使う場合は、`board-system/.env` に `GEMINI_API_KEY` を設定します。
   ```powershell
   cd board-system
   copy .env.example .env
   # .env を編集して GEMINI_API_KEY を設定（任意）
   ```

2. **ビルドと起動**  
   `board-system` で以下を実行します。**cato-ca.crt が無くてもビルドできます**（証明書はオプション）。
   ```powershell
   cd board-system
   docker compose up -d --build
   ```

3. **マイグレーション**  
   初回のみ、PostgreSQL のマイグレーションを実行します。
   ```powershell
   docker exec -it linko-backend alembic upgrade head
   ```

4. **アクセス**  
   - **Board System フロント**: http://localhost:3010  
   - **付箋ボード**: http://localhost:3011  
   - **Board System API**: http://localhost:8010（例: http://localhost:8010/health ）

5. **停止**
   ```powershell
   cd board-system
   docker compose down
   ```

### ポート一覧（ローカル compose）

| サービス | ポート（ホスト:コンテナ） | 用途 |
|----------|----------------------------|------|
| Frontend | 3010:3000 | Board System（Next.js） |
| Sticky Note | 3011:3000 | 付箋ボード |
| Backend | 8010:8000 | Board System API |
| PostgreSQL | 5433:5432 | DB（通常はブラウザから直接は使わない） |

---

## 1. 前提条件

- **サーバ**: **Ubuntu 24.04 LTS（live-server）**（本手順は 172.16.1.83 の新規サーバを想定）。SSH と sudo が使えること。
- **Docker**: Docker Engine と Docker Compose（v2 の `docker compose` コマンド）がインストール済み。
- **Nginx**: ホストに Nginx がインストール済み。設定は後述のとおり行います。
- **ドメイン・アクセス**: 本番では `wl-sticky-note.local`（または任意のドメイン）で Nginx にアクセスできること。新サーバの IP（172.16.1.83）を名前解決または hosts で参照できるようにしておく。

---

## 2. リポジトリの配置

新サーバ（172.16.1.83）に SSH ログインし、付箋ボードと Board System の**両方**が同じサーバ上に必要です。compose が `../02_1_sticky-note/src` を参照するため、**sparse-checkout では足りません**。フル clone または 02_1_sticky-note と board-system の両方をチェックアウトしてください。

```bash
# 例: 新サーバへ SSH したうえで
sudo mkdir -p /var/www/wlinko-pj
sudo chown $USER:$USER /var/www/wlinko-pj
cd /var/www/wlinko-pj

# 例: フル clone
git clone https://github.com/YOUR_ORG/wlinko-pj.git .

# または sparse-checkout で 02_1_sticky-note と board-system の両方を指定
# git clone --filter=blob:none --sparse https://github.com/YOUR_ORG/wlinko-pj.git .
# git sparse-checkout set 02_1_sticky-note board-system
# git checkout
```

結果として次のパスが存在すること。

- `/var/www/wlinko-pj/02_1_sticky-note/`
- `/var/www/wlinko-pj/board-system/`

---

## 3. 環境変数と CATO 証明書（任意）

### 3.1 board-system の .env

```bash
cd /var/www/wlinko-pj/board-system
cp .env.example .env
nano .env
```

少なくとも以下を設定します。

| 変数 | 説明 |
|------|------|
| `GEMINI_API_KEY` | Gemini API キー（AI 自動振り分け等で使用） |
| `DATABASE_URL` | 通常はそのままで可（compose 内で上書きされる想定）。.env.example の PostgreSQL URL は docker-compose.db と一致させる。 |

### 3.2 CATO 証明書（社内ネットワークでビルドする場合）

Dockerfile が `cato-ca.crt` を参照しています。ビルド環境で SSL インスペクション等がある場合は、以下に証明書を配置してください。

- `board-system/backend/cato-ca.crt`
- `board-system/frontend/cato-ca.crt`
- `02_1_sticky-note/src/cato-ca.crt`

不要な環境では、Dockerfile の COPY/RUN で証明書を追加している行をコメントアウトするか、空ファイルを置いてビルドを通す必要があります。

---

## 4. ネットワークと DB の起動

DB は Blue/Green の切り替えに依存せず、常に 1 本だけ起動します。

```bash
cd /var/www/wlinko-pj/board-system

docker network create linko-net
docker compose -f docker-compose.db.yml up -d
```

PostgreSQL のデータは `postgres_data` ボリュームに永続化されます。

---

## 5. 初回デプロイ実行

### 5.1 Nginx 設定の準備

- `board-system/nginx/nginx.conf` を、ホストの Nginx から読み込むように配置します。  
  例: `/etc/nginx/nginx.conf` をこの内容で置き換えるか、`include` で取り込みます。
- **active_env.conf** は `deploy.sh` が書き換えます。初回実行前に空でよいので、次の内容で作成しておきます。

```bash
sudo mkdir -p /etc/nginx/conf.d
# deploy.sh が存在しない場合の初期値（deploy.sh 実行時に上書きされる）
sudo tee /etc/nginx/conf.d/active_env.conf << 'EOF'
upstream current_frontend { server 127.0.0.1:3010; }
upstream current_backend { server 127.0.0.1:8010; }
upstream current_sticky { server 127.0.0.1:3011; }
EOF
```

- メインの Nginx 設定で `include /etc/nginx/conf.d/active_env.conf;` が読み込まれるようにしてください（`board-system/nginx/nginx.conf` を参考にしてください）。
- `sudo nginx -t` で設定を確認し、問題なければ `sudo systemctl reload nginx` でリロードします。

### 5.2 deploy.sh のパス確認

`board-system/deploy/deploy.sh` の先頭で `APP_DIR` を確認します。

```bash
APP_DIR="/var/www/wlinko-pj/board-system"
```

リポジトリを別のパスに置いた場合は、この値を環境に合わせて変更してください。

### 5.3 初回デプロイの実行

```bash
cd /var/www/wlinko-pj/board-system/deploy
chmod +x deploy.sh
./deploy.sh
```

- 初回は「現在の環境」が無いため、Blue または Green のいずれかがビルド・起動されます。
- ヘルスチェック（約 30 秒待機後、backend の `/health` を確認）に成功すると、Nginx の `active_env.conf` がその環境を向くように更新され、旧環境があれば停止されます。

### 5.4 初回マイグレーション（PostgreSQL）

Board System バックエンドは PostgreSQL を使用します。初回デプロイ後に、Alembic でマイグレーションを実行してください。

```bash
# 稼働中の backend コンテナ名は Blue または Green のどちらか（active_env で確認）
docker exec -it linko-backend-blue alembic upgrade head
# または
docker exec -it linko-backend-green alembic upgrade head
```

スキーマ変更を加えたコードをデプロイした場合も、同様にデプロイ後に上記を実行します。

### 5.5 動作確認

| 用途 | URL（例） |
|------|-----------|
| Board System フロント | http://wl-sticky-note.local/ または http://172.16.1.83/ |
| 付箋ボード | http://wl-sticky-note.local/board/ または http://172.16.1.83/board/ |
| Board System API（ヘルス） | http://wl-sticky-note.local/api/bs/health または http://172.16.1.83/api/bs/health |

ドメイン未設定の場合は、上記の 172.16.1.83 でアクセスして確認できます。

---

## 6. 通常のデプロイ（コード更新時）

コードを更新したら、再度 deploy スクリプトを実行します。

```bash
cd /var/www/wlinko-pj
git pull

cd board-system/deploy
./deploy.sh
```

**流れ:**

1. 現在アクティブでない方（Blue または Green）を判定
2. 新しいコードで Docker イメージをビルドし、その環境のコンテナを起動
3. ヘルスチェック（backend `/health`）が成功するまで待機
4. Nginx の `active_env.conf` を新環境のポートに切り替え
5. Nginx をリロード
6. 旧環境のコンテナを停止

**マイグレーションが必要な変更を入れた場合**は、デプロイ後に `docker exec -it linko-backend-<blue|green> alembic upgrade head` を実行してください。

---

## 7. 本番データの移行（旧サーバ → 新サーバ）

現在稼働中の本番サーバ（旧）から、新サーバ（172.16.1.83）へデータだけ移す手順です。**移行するのは (1) PostgreSQL（ユーザー・付箋・配置）と (2) 付箋ボードの boards.json の 2 種類**です。

### 7.1 旧サーバでバックアップを取得

**PostgreSQL**

```bash
# 旧サーバで（board-system があるディレクトリで）
cd /var/www/wlinko-pj/board-system

# DB コンテナ名は linko-db。プロジェクト名でボリュームを参照している場合は compose の -p を確認
docker exec linko-db pg_dump -U linko_user --clean --if-exists linko_board_system > ~/wlinko_pg_backup.sql
```

`~/wlinko_pg_backup.sql` を新サーバへコピーします（scp 等）。

**付箋ボード（boards.json）**

```bash
# 旧サーバで。ボリューム名は compose の -p による（例: board-system_sticky_data）
docker volume ls | grep sticky

# 中身をコピー（例: プロジェクト名が board-system の場合）
docker run --rm -v board-system_sticky_data:/data -v "$HOME:/out" alpine cp /data/boards.json /out/boards.json 2>/dev/null || \
docker run --rm -v linko_sticky_data:/data -v "$HOME:/out" alpine cp /data/boards.json /out/boards.json
```

`~/boards.json` を新サーバへコピーします。ボリューム名が違う場合は `docker volume ls` で確認し、上記の `board-system_sticky_data` 部分を置き換えてください。

### 7.2 新サーバでリストア

**前提**: 新サーバでは「4. ネットワークと DB の起動」まで完了し、**まだ deploy.sh は実行していない**（または DB だけ起動済み）状態を想定します。

**PostgreSQL**

```bash
# 新サーバで
cd /var/www/wlinko-pj/board-system
docker network create linko-net
docker compose -f docker-compose.db.yml up -d

# リストア（バックアップを新サーバのどこかに置いた場合）
docker exec -i linko-db psql -U linko_user -d linko_board_system < /path/to/wlinko_pg_backup.sql
```

エラーで `relation "xxx" does not exist` が出る場合は、バックアップに `--clean` が含まれているため無視してよいことがあります。重要なのは `CREATE TABLE` や `INSERT` が適用されていることです。

**付箋ボード（boards.json）**

新サーバで一度 deploy を実行して `sticky_data` ボリュームを作成してから、中身を上書きします。

```bash
# 初回デプロイでボリューム作成（未実行なら）
cd /var/www/wlinko-pj/board-system/deploy
./deploy.sh

# コンテナを止めてから boards.json を差し替え（プロジェクト名は deploy で使っているものに合わせる）
cd /var/www/wlinko-pj/board-system
docker compose -f docker-compose.prod.yml -p board-system-blue down
# または active が green なら -p board-system-green

# バックアップした boards.json をボリュームにコピー
docker run --rm -v board-system_sticky_data:/data -v "/path/to/boards.json:/src/boards.json" alpine cp /src/boards.json /data/boards.json

# 再度デプロイでコンテナを起動
cd deploy && ./deploy.sh
```

`/path/to/boards.json` は旧サーバからコピーしたファイルのパスに置き換えてください。

### 7.3 移行後の確認

- 新サーバで `http://172.16.1.83/`（またはドメイン）にアクセスし、ユーザー・付箋・タスク・パーソナルが表示されること
- 付箋ボード `http://172.16.1.83/board/` で、旧環境のボード・付箋が表示されること
- 必要に応じて `alembic upgrade head` を実行（スキーマが最新なら不要）

---

## 8. ロールバック

デプロイ後に問題があった場合、直前の環境に戻します。

```bash
cd /var/www/wlinko-pj/board-system/deploy
./rollback.sh
```

Nginx の向き先が前の Blue/Green に切り替わり、`systemctl reload nginx` が実行されます。  
**注意**: ロールバック後、現在動いているコンテナは「前のビルド」のままです。コードを戻したい場合は `git checkout` 等で戻してから再度 `deploy.sh` を実行する運用も検討してください。

---

## 9. 運用メモ

### ポート割り当て（Blue/Green）

| 環境 | Frontend | Backend | Sticky Note |
|------|-----------|----------|-------------|
| Blue | 3010 | 8010 | 3011 |
| Green | 3020 | 8020 | 3021 |

### データ永続化

- **PostgreSQL**: `docker-compose.db.yml` の `postgres_data` ボリューム
- **付箋ボード**: `docker-compose.prod.yml` の `sticky_data` ボリューム

### ログ確認

```bash
# 現在の向き先
cat /etc/nginx/conf.d/active_env.conf

# コンテナログ（例: Blue の backend）
docker logs -f linko-backend-blue
```

### ビルドが遅い・止まる場合（CATO / プロキシ環境）

BuildKit を無効にしてビルドします。

```bash
export DOCKER_BUILDKIT=0
docker compose -f docker-compose.prod.yml -p board-system-blue build --no-cache
```

---

## 10. 参照

- **board-system 配下の詳細**: [board-system/DEPLOY.md](../board-system/DEPLOY.md)
- **非 Docker 本番デプロイ**: [本番デプロイ手順.md](本番デプロイ手順.md)
- **本番設定の目安（.env 等）**: [本番設定の目安.md](本番設定の目安.md)
