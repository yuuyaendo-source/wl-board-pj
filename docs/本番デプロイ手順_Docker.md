# 本番デプロイ手順（Docker）

付箋ボードとBoard Systemを **Docker** で本番デプロイする手順です。Blue/Green デプロイで切り替え時のダウンタイムを抑えられます。

- **非 Docker**（PM2 + systemd + Nginx）でデプロイする場合は [本番デプロイ手順.md](本番デプロイ手順.md) を参照してください。

---

## 目次

| セクション | 内容 |
|------------|------|
| [クイックチェック](#クイックチェック) | 状況別にやることの一覧 |
| [1. 概要](#1-概要) | 構成・URL・Docker と非 Docker の違い |
| [2. 前提条件](#2-前提条件) | サーバ・Docker・Nginx・リポジトリ |
| [3. 初回デプロイ](#3-初回デプロイ) | リポジトリ配置 → .env → DB 起動 → Nginx → deploy → マイグレーション → 確認 |
| [4. 通常のデプロイ](#4-通常のデプロイ) | コード更新時の手順 |
| [5. ロールバック](#5-ロールバック) | 問題発生時に直前の環境へ戻す |
| [6. 運用](#6-運用) | ログ・永続化・ポート |
| [7. トラブルシューティング](#7-トラブルシューティング) | よくある事象と対処 |
| [8. 参照](#8-参照) | 関連ドキュメント |
| [付録 A: ローカルで Docker を動かす](#付録-a-ローカルで-docker-を動かす) | 本番前に手元で確認する場合 |
| [付録 B: ステージング環境でテスト](#付録-b-ステージング環境でテスト) | 本番を止めずに新機能を検証する |

---

## クイックチェック

| 状況 | やること |
|------|----------|
| **初回デプロイ** | [3. 初回デプロイ](#3-初回デプロイ) を順に実施 |
| **コード更新の反映** | [4. 通常のデプロイ](#4-通常のデプロイ) を実行 |
| **問題発生時** | [5. ロールバック](#5-ロールバック) を実行 |
| **新機能を本番停止なしでテスト** | [付録 B: ステージング環境でテスト](#付録-b-ステージング環境でテスト) を実施 |
| **ステージングで問題なかったので本番へ反映** | [4. 通常のデプロイ](#4-通常のデプロイ) の手順で `./deploy.sh` を実行（[付録 B.5](#b5-ステージングで問題なければ本番へ反映) 参照） |

---

## 1. 概要

### 1.1 サーバ構成（想定）

| 項目 | 内容 |
|------|------|
| ホスト | Windows Server 2022（Hyper-V） |
| ゲスト OS | Ubuntu 24.04 LTS（live-server） |
| IP（例） | 172.16.1.84 |
| VM リソース目安 | メモリ 4 GB、ストレージ 60〜80 GB（PostgreSQL + 3 コンテナ + OS） |

### 1.2 構成の整理

| 項目 | 内容 |
|------|------|
| リポジトリ | wlinko-pj（**02_1_sticky-note** と **board-system** の両方が必要） |
| Docker | `board-system/docker-compose.prod.yml`（アプリ Blue/Green）、`board-system/docker-compose.db.yml`（PostgreSQL） |
| リバースプロキシ | ホストの Nginx が **80 と 443** で受け、`active_env.conf` で Blue/Green のポートに振り分け（SSL は Let's Encrypt） |

### 1.3 URL（Docker 版）

| 用途 | URL（例） |
|------|-----------|
| トップ | https://wl-ai-board.internal.wonder-link.co.jp/ → 302 で /boards/taskboard |
| Board System フロント | https://wl-ai-board.internal.wonder-link.co.jp/boards/（例: /boards/taskboard） |
| 付箋ボード | https://wl-ai-board.internal.wonder-link.co.jp/board/（例: /board/wl） |
| Board System API | https://wl-ai-board.internal.wonder-link.co.jp/api/bs/ |

Nginx: `/` → 302 /boards/taskboard、`/boards/` → Board System フロント、`/board/` → 付箋ボード、`/api/bs/` → Board System API。

---

## 2. 前提条件

- **サーバ**: Ubuntu 24.04 LTS。SSH と sudo が使えること。
- **Docker**: Docker Engine と Docker Compose（v2 の `docker compose`）がインストール済み。
- **Nginx**: ホストに Nginx がインストール済み（設定は 3.4 で行う）。
- **ドメイン・アクセス**: `wl-ai-board.internal.wonder-link.co.jp`（または IP `172.16.1.84`）で Nginx にアクセスできること（DNS でサーバ IP を指す）。

---

## 3. 初回デプロイ

以下を**上から順に**実行する。

### 3.1 リポジトリの配置

compose が `../02_1_sticky-note/src` を参照するため、**02_1_sticky-note と board-system の両方**が必要。sparse-checkout で両方指定するか、フル clone する。

```bash
sudo mkdir -p /var/www/wlinko-pj
sudo chown $USER:$USER /var/www/wlinko-pj
cd /var/www/wlinko-pj
git clone https://github.com/YOUR_ORG/wlinko-pj.git .
# または sparse-checkout で 02_1_sticky-note と board-system を指定
```

結果として `/var/www/wlinko-pj/02_1_sticky-note/` と `/var/www/wlinko-pj/board-system/` が存在すること。

### 3.2 環境変数

```bash
cd /var/www/wlinko-pj/board-system
cp .env.example .env
nano .env
```

少なくとも `OLLAMA_URL`（例: `http://172.16.1.251:11434/v1`）を設定。`NEXT_PUBLIC_API_URL` は本番の API ベース URL（例: `https://wl-ai-board.internal.wonder-link.co.jp/api/bs`）。**SSL 化時は必ず `https://` にすること**。

**CATO 証明書**（社内ネットワークでビルドする場合）: 必要なら `board-system/backend/cato-ca.crt`、`board-system/frontend/cato-ca.crt`、`02_1_sticky-note/src/cato-ca.crt` を配置。不要な環境では Dockerfile の証明書行をコメントアウトするか空ファイルを置く。

### 3.3 ネットワークと DB の起動

```bash
cd /var/www/wlinko-pj/board-system
docker network create linko-net
docker compose -f docker-compose.db.yml up -d
```

PostgreSQL は `postgres_data` ボリュームに永続化される。

### 3.4 Nginx の準備

- `board-system/nginx/nginx.conf` をホストの Nginx から読み込むように配置（`/etc/nginx/nginx.conf` を置き換えるか include）。
- `active_env.conf` を初回用に作成する。

```bash
sudo mkdir -p /etc/nginx/conf.d
sudo tee /etc/nginx/conf.d/active_env.conf << 'EOF'
upstream current_frontend { server 127.0.0.1:3010; }
upstream current_backend { server 127.0.0.1:8010; }
upstream current_sticky { server 127.0.0.1:3011; }
EOF
```

メイン設定で `include /etc/nginx/conf.d/active_env.conf;` が読み込まれるようにする。`sudo nginx -t` で確認し、`sudo systemctl reload nginx` でリロード。

**SSL（HTTPS）化する場合**: 本リポジトリの Nginx 設定は Let's Encrypt を前提にしています。証明書の取得・パス設定・自動更新は [SSL-Setup.md](SSL-Setup.md) を参照してください。証明書を配置したうえで Nginx をリロードすると、80 は 443 へリダイレクトされ、443 で HTTPS が有効になります。

### 3.5 deploy.sh のパス

`board-system/deploy/deploy.sh` の `APP_DIR` を環境に合わせる（既定: `/var/www/wlinko-pj/board-system`）。

### 3.6 初回デプロイの実行

```bash
cd /var/www/wlinko-pj/board-system/deploy
chmod +x deploy.sh
./deploy.sh
```

初回は Blue または Green のいずれかがビルド・起動する。ヘルスチェック成功後に Nginx の `active_env.conf` が更新される。

### 3.7 初回マイグレーション

```bash
docker exec -it linko-backend-blue alembic upgrade head
# または linko-backend-green（稼働中のコンテナ名は active_env.conf で確認）
```

スキーマ変更をデプロイした場合も、デプロイ後に同様に実行する。

### 3.8 動作確認

| 用途 | URL（例） |
|------|-----------|
| Board System フロント | https://wl-ai-board.internal.wonder-link.co.jp/ または https://172.16.1.84/ |
| 付箋ボード | https://wl-ai-board.internal.wonder-link.co.jp/board/ または https://172.16.1.84/board/ |
| Board System API（ヘルス） | https://wl-ai-board.internal.wonder-link.co.jp/api/bs/health または https://172.16.1.84/api/bs/health |

### 3.9 パーソナルボードで投稿できない場合

パーソナルボードは **users テーブルに id 1〜7 のユーザー** が存在することが前提。DB を空のまま立ち上げた場合は、次のいずれかで 7 名分のユーザーを登録する。

**方法 1a: コンテナ内で実行**（backend をシードスクリプト追加後に再ビルド済みの場合）

```bash
docker exec -it linko-backend-blue python scripts/seed_personal_members.py
```

「No such file or directory」の場合は方法 1b を使うか、再デプロイ後に 1a を試す。

**方法 1b: ホストから実行**

```bash
cd /var/www/wlinko-pj/board-system/backend
source .venv/bin/activate
DATABASE_URL="postgresql://linko_user:linko_password@127.0.0.1:5433/linko_board_system" python scripts/seed_personal_members.py
```

（PostgreSQL は docker-compose.db.yml でホスト 5433 にマッピングされている前提。ホストの .venv に psycopg2 が入っていればそのまま使える。）

**方法 2**: API で `POST /api/bs/users` に `{"name": "表示名", "role": null}` を送りユーザーを作成。id 1〜7 を揃えたい場合はシードスクリプトを使う。

---

## 4. 通常のデプロイ

コード更新後は以下で反映する。

```bash
cd /var/www/wlinko-pj
git pull
cd board-system/deploy
./deploy.sh
```

流れ: 非アクティブ側（Blue/Green）を判定 → 新コードでビルド・起動 → ヘルスチェック → Nginx 切り替え → 前の環境を停止。  
マイグレーションが必要な変更を入れた場合は、デプロイ後に `docker exec -it linko-backend-<blue|green> alembic upgrade head` を実行する。

---

## 5. ロールバック

```bash
cd /var/www/wlinko-pj/board-system/deploy
./rollback.sh
```

Nginx の向き先が前の Blue/Green に切り替わり、Nginx がリロードされる。  
**注意**: ロールバック後もコンテナは「前のビルド」のまま。コードを戻したい場合は `git checkout` 等で戻してから再度 `deploy.sh` を実行する。

---

## 6. 運用

### 6.1 ポート割り当て（Blue/Green）

| 環境 | Frontend | Backend | Sticky Note |
|------|----------|---------|-------------|
| Blue | 3010 | 8010 | 3011 |
| Green | 3020 | 8020 | 3021 |

### 6.2 データ永続化

- **PostgreSQL**: `docker-compose.db.yml` の `postgres_data` ボリューム
- **付箋ボード**: `docker-compose.prod.yml` の `sticky_data` ボリューム

### 6.3 ログ確認

本番は `deploy.sh` が `-f docker-compose.prod.yml` とプロジェクト名 `board-system-blue` / `board-system-green` で起動するため、`docker compose logs -f` だけでは対象がなくログが出ない。

**稼働中の環境を確認:**

```bash
cat /etc/nginx/conf.d/active_env.conf
# 127.0.0.1:3010 なら Blue、3020 なら Green
```

**ログの見方:**

```bash
# 方法 1: コンテナ名で直接
docker logs -f linko-backend-blue    # または linko-backend-green
docker logs -f linko-frontend-blue
docker logs -f linko-sticky-note-blue

# 方法 2: docker compose で（プロジェクト・ファイルを指定）
cd /var/www/wlinko-pj/board-system
docker compose -f docker-compose.prod.yml -p board-system-blue logs -f
```

---

## 7. トラブルシューティング

### 7.1 ビルドが遅い・止まる（CATO / プロキシ環境）

```bash
export DOCKER_BUILDKIT=0
docker compose -f docker-compose.prod.yml -p board-system-blue build --no-cache
```

### 7.2 「API の URL が誤っているか…」エラー

1. **Nginx**: `board-system/nginx/nginx.conf` が本番に反映されているか確認。`include /etc/nginx/conf.d/active_env.conf;` と `location /api/bs/` が含まれるようにする。
2. **アクセスする URL と一致させる**: ブラウザで IP（例: https://172.16.1.84/）で開いている場合は、`.env` の `NEXT_PUBLIC_API_URL` も同じ IP（例: `https://172.16.1.84/api/bs`）にし、**再ビルド・再デプロイ**する。ドメインで開く場合は `https://wl-ai-board.internal.wonder-link.co.jp` が DNS でサーバ IP（172.16.1.84）を指しているか確認する。

### 7.3 パーソナルボードで投稿できない

[3.9 パーソナルボードで投稿できない場合](#39-パーソナルボードで投稿できない場合) を参照（users id 1〜7 の登録）。

---

## 8. 参照

- **board-system 配下の要約**: [board-system/DEPLOY.md](../board-system/DEPLOY.md)
- **非 Docker 本番デプロイ**: [本番デプロイ手順.md](本番デプロイ手順.md)
- **本番設定の目安（.env 等）**: [本番設定の目安.md](本番設定の目安.md)
- **ローカルで Docker を試す**: [付録 A](#付録-a-ローカルで-docker-を動かす) または [ローカルDockerでテストする手順.md](../ローカルDockerでテストする手順.md)

---

## 付録 B: ステージング環境でテスト

新しい機能や動作を検証するための**ステージングは本番と同一サーバ**で運用する。本番を止めずに、別ポート（3030/8030/3031）と**別 DB**（`linko_board_system_staging`）でステージングを動かす。同一サーバ上の Nginx が `server_name` で本番とステージングを振り分ける。

### B.1 構成

- **ステージング**: 本番と同じサーバ（例: 172.16.1.84）上で、別ポート・別 DB で起動。
- **アクセス**: http://staging.wl-sticky-note.local/  
  **名前解決**: DNS で `staging.wl-sticky-note.local` を**本番サーバの IP**（例: 172.16.1.84）に向けるか、各 PC の hosts に `172.16.1.84 staging.wl-sticky-note.local` を追加する。
- ステージングは **本番と別のデータベース**（`linko_board_system_staging`）を使用。同一 PostgreSQL 内に別 DB が自動作成され、本番データに影響しない。

### B.2 手順（初回・本番サーバで実施）

1. **本番サーバにリポジトリがある前提**  
   `/var/www/wlinko-pj` に wlinko-pj があり、`board-system/.env` が用意されていること。  
   ステージング用の `NEXT_PUBLIC_API_URL` は deploy-staging.sh のデフォルト（`staging.wl-sticky-note.local`）に合わせて **http://staging.wl-sticky-note.local/api/bs** でビルドされる（環境変数 `STAGING_HOST` で変更可）。

2. **本番サーバの Nginx にステージング用設定を追加**  
   - リポジトリの `board-system/nginx/staging.conf` の内容を、サーバーの **Nginx 設定の読み込み先** に置く。  
   - **よくあるやり方**: `/etc/nginx/conf.d/staging.conf` にコピーする。多くの環境では `/etc/nginx/nginx.conf`（メイン設定ファイル）の `http { }` 内にすでに `include /etc/nginx/conf.d/*.conf;` があるため、`conf.d/` に置くだけで自動的に読み込まれる。  
   - 読み込まれない場合は、`/etc/nginx/nginx.conf` を開き、`http { }` ブロック内の適当な位置に `include /etc/nginx/conf.d/staging.conf;` を 1 行追加する。  
   - 反映: `sudo nginx -t` で確認後、`sudo systemctl reload nginx`。

3. **ステージングの起動（本番サーバで実行）**  
   ```bash
   cd /var/www/wlinko-pj/board-system/deploy
   chmod +x deploy-staging.sh
   ./deploy-staging.sh
   ```
   初回はビルドに数分かかる。完了後、**staging.wl-sticky-note.local** が本番サーバ IP に解決する状態で、ブラウザから http://staging.wl-sticky-note.local/ にアクセスして動作確認。

4. **マイグレーション**  
   `deploy-staging.sh` 内でステージング DB に対して `alembic upgrade head` を実行する。失敗する場合は本番サーバで手動:  
   `docker exec -it linko-backend-staging alembic upgrade head`  
   ステージング用のユーザー（パーソナルボード等）が必要なら、コンテナ内で `python scripts/seed_personal_members.py` を実行するか、画面の「ユーザー管理」から追加する。

### B.3 手順（2回目以降・コード更新して再テスト）

**本番サーバ**（ステージングも動かしている同じサーバ）で:

```bash
cd /var/www/wlinko-pj
git pull
cd board-system/deploy
./deploy-staging.sh
```

ステージングだけが再ビルド・再起動する。本番のコンテナは触らない。

### B.4 ステージングの停止

不要になったら**本番サーバ**で:

```bash
cd /var/www/wlinko-pj/board-system/deploy
./stop-staging.sh
```

本番には影響しない。

### B.5 ステージングで問題なければ本番へ反映

ステージングと本番は**同じリポジトリのコード**を使う。ステージングで確認した内容は、**同じサーバ**で通常デプロイすると本番に反映される。

1. ステージング（http://staging.wl-sticky-note.local/）で動作・表示を確認する。
2. 問題なければ、**本番サーバ**で通常の本番デプロイを行う（[4. 通常のデプロイ](#4-通常のデプロイ) と同じ手順）。

```bash
# 本番サーバで実行（ステージングを動かしているのと同じサーバ）
cd /var/www/wlinko-pj
git pull
cd board-system/deploy
./deploy.sh
```

これで本番の Blue/Green が最新コードに切り替わる。ステージングで試したコードがそのまま本番に出る形になる。

- **スキーマ変更**（マイグレーション追加）を入れた場合は、デプロイ後に本番 Backend で `alembic upgrade head` を実行する（[3.7 初回マイグレーション](#37-初回マイグレーション) と同様）。
- ステージングはそのまま残してよい。本番反映後も同じサーバで次の変更をステージングで試せる。

### B.6 ポート

| 役割       | ステージング |
|------------|--------------|
| Frontend   | 3030         |
| Backend    | 8030         |
| Sticky Note| 3031         |

### B.7 ステージングにアクセスできないときの確認

PC の名前解決はできているがブラウザで開けない場合、**サーバー上**で次を順に確認する。

1. **Nginx がステージング設定を読み込んでいるか**  
   ```bash
   sudo nginx -T 2>/dev/null | grep -E "staging.wl-sticky-note|3030|8030|3031"
   ```  
   `staging.wl-sticky-note.local` や 3030/8030/3031 の記述が出れば読み込み済み。何も出ない場合は `/etc/nginx/nginx.conf` の `http { }` 内に `include /etc/nginx/conf.d/*.conf;` があるか、または `include /etc/nginx/conf.d/staging.conf;` を追加したうえで `sudo systemctl reload nginx` する。

2. **サーバー自身からステージングに届くか**  
   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" -H "Host: staging.wl-sticky-note.local" http://127.0.0.1/
   ```  
   `302` や `200` が返れば、Nginx の振り分けとステージングコンテナは動いている。その場合は **3** へ。

3. **ファイアウォール**  
   同じ PC で本番（例: https://wl-ai-board.internal.wonder-link.co.jp/）にはアクセスできるなら、ポート 443 は開いているので、上記 1 を再確認。本番にもアクセスできない場合は、サーバーのファイアウォール（`ufw` や iptables）で 443 が許可されているか確認する。  
   （ping が通らないだけの場合は、ICMP を止めているだけのことが多く、HTTP には影響しない。）

4. **ステージング用ポートが listen しているか**  
   ```bash
   ss -tlnp | grep -E '3030|8030|3031'
   ```  
   何も出ない場合はステージングコンテナが落ちている可能性がある。`docker ps | grep staging` で確認し、必要なら `./deploy-staging.sh` を再実行する。

---

## 付録 A: ローカルで Docker を動かす

本番デプロイの前に、手元の PC で Docker 構成を動かして確認できる。**Nginx は不要**。`board-system/docker-compose.yml`（ローカル用）を使う。

1. `board-system/.env` に必要なら `OLLAMA_URL`（例: `http://172.16.1.251:11434/v1`）を設定。
2. `cd board-system` → `docker compose up -d --build`
3. 初回のみ `docker exec -it linko-backend alembic upgrade head`
4. アクセス: Board System http://localhost:3010、付箋ボード http://localhost:3011、API http://localhost:8010/health
5. 停止: `docker compose down`

詳細は [ローカルDockerでテストする手順.md](../ローカルDockerでテストする手順.md) を参照。
