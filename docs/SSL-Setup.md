# SSL 化手順（wl-board-pj）

本番では **Let's Encrypt 発行の \*.internal.wonder-link.co.jp** 証明書を、ホストの `~/sv_cert/` に `fullchain.pem` / `privkey.pem` として配置して使用します。Nginx 設定はそのパスを参照するようにしてあります。

## 本番で使用する証明書（board-system / wl-sticky-note）

| 項目 | 内容 |
|------|------|
| **発行** | Let's Encrypt（CN: \*.internal.wonder-link.co.jp、発行: Let's Encrypt） |
| **配置場所** | 開発: `/home/hisashi/dev/sv_cert/` / 本番: `/home/devuser01/sv_cert/` |
| **ファイル** | `fullchain.pem`（証明書）、`privkey.pem`（秘密鍵） |
| **FQDN** | `https://wl-ai-board.internal.wonder-link.co.jp/` |
| **IP** | `172.16.1.84` |

`board-system/nginx/nginx.conf`（開発）・`nginx.conf.production-server`（本番）・`staging.conf`・`wl-sticky-note/src/nginx.conf` はいずれも上記パスを参照しています。別のサーバや別ユーザで運用する場合は、証明書パスと `server_name` を環境に合わせて書き換えてください。

※ linko-system（AI-Board）は別 FQDN（`linko-board.internal.wonder-link.co.jp`）で、同じ証明書ディレクトリを参照しています。

---

## Let's Encrypt で新規取得する場合

以下は、上記とは別に Let's Encrypt で証明書を取得する場合の手順です。

### 前提（Let's Encrypt で取得する場合）

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

### 3. Nginx 設定での証明書パス

**本番（Let's Encrypt \*.internal.wonder-link.co.jp を使う場合）**: リポジトリの Nginx 設定はすでに `~/sv_cert/fullchain.pem` と `privkey.pem` を参照しています。**そのディレクトリに Let's Encrypt で取得した fullchain.pem / privkey.pem を配置**すればそのまま利用できます。変更不要です。

**別ドメインで Let's Encrypt を使う場合**: 設定内の証明書パスと `server_name` を、取得したドメインに合わせて書き換えてください。

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

- 例: `NEXT_PUBLIC_API_URL=https://wl-ai-board.internal.wonder-link.co.jp/api/bs`
- Docker 本番の場合は `docker-compose.prod.yml` の環境変数や `.env` で設定。

## 7. .local のみで使う場合（社内検証）

`.local` や IP のみの環境では Let's Encrypt は使えません。その場合は次のいずれかで対応してください。

- **自己署名証明書**を生成し、Nginx の `ssl_certificate` / `ssl_certificate_key` をそのパスに変更する。
- 検証時のみ **HTTP のまま**利用し、本番ドメイン取得後に上記手順で SSL 化する。
