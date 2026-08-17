#!/usr/bin/env bash
set -e
# 本番を止めずにステージング環境を起動する（同一サーバ・別ポート・別 DB）。
# アクセス: http://staging.wl-sticky-note.local/ （DNS で本番サーバ IP を向けるか、hosts に追加）

APP_DIR="/var/www/wlinko-pj/board-system"
DOCKER_COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
DOCKER_COMPOSE_STAGING="$APP_DIR/docker-compose.staging.yml"
DOCKER_COMPOSE_DB="$APP_DIR/docker-compose.db.yml"
STAGING_HOST="${STAGING_HOST:-staging.wl-ai-board.internal.wonder-link.com}"
STAGING_DB_NAME="linko_board_system_staging"

docker network inspect linko-net >/dev/null 2>&1 || docker network create linko-net
echo "Ensuring DB is running..."
docker compose -f "$DOCKER_COMPOSE_DB" up -d

# ==========================================
# 1. 確実なDB起動待ち（ベストプラクティス）
# ==========================================
echo "Waiting for PostgreSQL to start..."
until docker exec linko-db pg_isready -U linko_user > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 1
done
echo "PostgreSQL is up and running!"

# ==========================================
# 2. 安全なDB作成（存在確認付き）
# ==========================================
echo "Ensuring staging database exists..."
if ! docker exec linko-db psql -U linko_user -d linko_board_system -tAc "SELECT 1 FROM pg_database WHERE datname = '$STAGING_DB_NAME'" | grep -q 1; then
  echo "Creating staging database: $STAGING_DB_NAME"
  docker exec linko-db psql -U linko_user -d linko_board_system -c "CREATE DATABASE $STAGING_DB_NAME OWNER linko_user;"
else
  echo "Database '$STAGING_DB_NAME' already exists. Skipping creation."
fi

# .env の値（OLLAMA_URL 等）を引き継ぎ、ステージング用に上書き（HTTPS でビルド）
if [ -f "$APP_DIR/.env" ]; then
  set -a
  source "$APP_DIR/.env"
  set +a
fi
export COLOR=staging
export PORT_FRONTEND=3030
export PORT_BACKEND=8030
export PORT_STICKY=3031
export NEXT_PUBLIC_API_URL="https://${STAGING_HOST}/api/bs"
export NEXT_PUBLIC_LEGACY_BOARD_URL="https://${STAGING_HOST}"

echo "Building images for staging..."
docker compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_STAGING" -p board-system-staging build

echo "Running migrations on staging DB..."
docker compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_STAGING" -p board-system-staging run --rm backend alembic upgrade head

echo "Running team seeds on staging DB..."
docker compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_STAGING" -p board-system-staging run --rm backend python scripts/seed_teams.py

echo "Starting staging containers (ports 3030/8030/3031, DB: $STAGING_DB_NAME)..."
docker compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_STAGING" -p board-system-staging up -d

echo "Staging is up. Ensure ${STAGING_HOST} resolves to this server (DNS or /etc/hosts)."
echo "Nginx で staging.conf が include されていること。URL: https://${STAGING_HOST}/"