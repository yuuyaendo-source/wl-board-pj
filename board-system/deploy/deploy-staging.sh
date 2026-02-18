#!/bin/bash
set -e
# 本番を止めずにステージング環境を起動する（同一サーバ・別ポート・別 DB）。
# アクセス: http://staging.wl-sticky-note.local/ （DNS で本番サーバ IP を向けるか、hosts に追加）

APP_DIR="/var/www/wlinko-pj/board-system"
DOCKER_COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
DOCKER_COMPOSE_STAGING="$APP_DIR/docker-compose.staging.yml"
DOCKER_COMPOSE_DB="$APP_DIR/docker-compose.db.yml"
STAGING_HOST="${STAGING_HOST:-staging.wl-sticky-note.local}"
STAGING_DB_NAME="linko_board_system_staging"

docker network inspect linko-net >/dev/null 2>&1 || docker network create linko-net
echo "Ensuring DB is running..."
docker compose -f "$DOCKER_COMPOSE_DB" up -d

# ステージング用 DB がなければ作成（同一 PostgreSQL コンテナ内）
if ! docker exec linko-db psql -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname = '$STAGING_DB_NAME'" | grep -q 1; then
  echo "Creating staging database: $STAGING_DB_NAME"
  docker exec linko-db psql -U postgres -c "CREATE DATABASE $STAGING_DB_NAME OWNER linko_user;"
fi

# .env の値（GEMINI_API_KEY 等）を引き継ぎ、そのうえでステージング用に上書き
if [ -f "$APP_DIR/.env" ]; then
  set -a
  source "$APP_DIR/.env"
  set +a
fi
export COLOR=staging
export PORT_FRONTEND=3030
export PORT_BACKEND=8030
export PORT_STICKY=3031
export NEXT_PUBLIC_API_URL="http://${STAGING_HOST}/api/bs"
export NEXT_PUBLIC_LEGACY_BOARD_URL="http://${STAGING_HOST}"

echo "Building and starting staging (ports 3030/8030/3031, DB: $STAGING_DB_NAME)..."
docker compose -f "$DOCKER_COMPOSE_FILE" -f "$DOCKER_COMPOSE_STAGING" -p board-system-staging up -d --build

echo "Running migrations on staging DB..."
sleep 5
docker exec linko-backend-staging alembic upgrade head 2>/dev/null || true

echo "Staging is up. Ensure ${STAGING_HOST} resolves to this server (DNS or /etc/hosts)."
echo "Add Nginx staging config (nginx/staging.conf) and reload. URL: http://${STAGING_HOST}/"
