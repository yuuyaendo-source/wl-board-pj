# Let's Encrypt による SSL 化手順（wl-board-pj）

各 Nginx 設定は Let's Encrypt の証明書を参照するようにしています。証明書の取得と Nginx への組み込み手順です。

## 前提

- **公開 DNS が必須**: Let's Encrypt は `.local` やプライベート IP には発行できません。**実在する FQDN**（例: `board.example.com`）で DNS をサーバの IP に向けてください。
- Nginx はホストで稼働している想定（`/etc/nginx/` に設定を配置）。

## 1. certbot のインストール（Ubuntu/Debian）

```bash
sudo apt update
sudo apt install -y certbot
# Nginx 連携（プラグイン）を使う場合
sudo apt install -y python3-certbot-nginx
```

## 2. 証明書の取得

### 方法 A: standalone（Nginx を一時停止して取得）

```bash
# 対象ドメインを指定（例: board.example.com）
sudo systemctl stop nginx
sudo certbot certonly --standalone -d board.example.com
sudo systemctl start nginx
```

### 方法 B: webroot（Nginx 稼働中のまま取得）

事前に HTTP の `server` で `location /.well-known/acme-challenge/` を用意したうえで:

```bash
sudo certbot certonly --webroot -w /var/www/html -d board.example.com
```

証明書は次の場所に保存されます。

- **証明書**: `/etc/letsencrypt/live/board.example.com/fullchain.pem`
- **秘密鍵**: `/etc/letsencrypt/live/board.example.com/privkey.pem`

## 3. Nginx 設定での証明書パス

設定ファイル内の証明書パスは、**取得したドメイン名**と一致させる必要があります。

- 現在の例では `wl-sticky-note.local` になっていますが、Let's Encrypt は `.local` に発行できないため、**実際に取得したドメイン**に合わせて書き換えてください。

例: ドメインが `board.example.com` の場合

```nginx
ssl_certificate     /etc/letsencrypt/live/board.example.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/board.example.com/privkey.pem;
```

同様に `server_name` も取得したドメインに合わせて変更します。

```nginx
server_name board.example.com;
```

### 対象ファイル

| ファイル | 用途 |
|----------|------|
| `board-system/nginx/nginx.conf` | Board System 本番（Docker + active_env） |
| `wl-sticky-note/src/nginx.conf` | 付箋ボード単体デプロイ用 |
| `docs/nginx-with-board-system.conf.example` | 設定例（コピーして使う用） |

## 4. Nginx の反映

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## 5. 自動更新（推奨）

certbot のタイマーで期限前に更新されます。Nginx へのリロードも certbot に任せる場合:

```bash
sudo apt install -y python3-certbot-nginx
sudo certbot renew --nginx
```

cron で定期実行する場合（例: 毎日 3 時）:

```bash
sudo crontab -e
# 追加
0 3 * * * certbot renew --quiet --deploy-hook "systemctl reload nginx"
```

## 6. フロントの API URL（HTTPS に統一）

Board System のフロントは `NEXT_PUBLIC_API_URL` 等で API のベース URL を参照します。SSL 化後は **https** に統一してください。

- 例: `NEXT_PUBLIC_API_URL=https://board.example.com/api/bs`
- Docker 本番の場合は `docker-compose.prod.yml` の環境変数や `.env` で設定。

## 7. .local のみで使う場合（社内検証）

`.local` や IP のみの環境では Let's Encrypt は使えません。その場合は次のいずれかで対応してください。

- **自己署名証明書**を生成し、Nginx の `ssl_certificate` / `ssl_certificate_key` をそのパスに変更する。
- 検証時のみ **HTTP のまま**利用し、本番ドメイン取得後に上記手順で SSL 化する。
