#!/bin/bash
set -e

# 設定
APP_DIR="/var/www/wlinko-pj/board-system"
NGINX_CONF_DIR="/etc/nginx/conf.d"
ACTIVE_ENV_FILE="$NGINX_CONF_DIR/active_env.conf"
DOCKER_COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"
DOCKER_COMPOSE_DB="$APP_DIR/docker-compose.db.yml"

# ネットワーク作成（存在しない場合）
docker network inspect linko-net >/dev/null 2>&1 || docker network create linko-net

# DB起動（共有リソース）
# 既に起動している場合は何もしない（up -d なので安全）
echo "Ensuring DB is running..."
docker compose -f "$DOCKER_COMPOSE_DB" up -d

# active_env.conf が存在しない場合の初期化
if [ ! -f "$ACTIVE_ENV_FILE" ]; then
    echo "Initializing active_env.conf..."
    cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:3010; }
upstream current_backend { server 127.0.0.1:8010; }
upstream current_sticky { server 127.0.0.1:3011; }
EOF
fi

# 現在のアクティブ環境を確認
if grep -q "3010" "$ACTIVE_ENV_FILE"; then
    CURRENT_COLOR="blue"
    NEW_COLOR="green"
    NEW_PORT_FRONTEND="3020"
    NEW_PORT_BACKEND="8020"
    NEW_PORT_STICKY="3021"
else
    CURRENT_COLOR="green"
    NEW_COLOR="blue"
    NEW_PORT_FRONTEND="3010"
    NEW_PORT_BACKEND="8010"
    NEW_PORT_STICKY="3011"
fi

echo "Current environment: $CURRENT_COLOR"
echo "Deploying to: $NEW_COLOR"

echo "Starting new containers..."
export COLOR=$NEW_COLOR
export PORT_FRONTEND=$NEW_PORT_FRONTEND
export PORT_BACKEND=$NEW_PORT_BACKEND
export PORT_STICKY=$NEW_PORT_STICKY

# DBは別ファイルで起動済みなのでここではアプリのみ起動
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" up -d --build

# ヘルスチェック
echo "Waiting for health check..."
sleep 30

if curl -s "http://localhost:$NEW_PORT_BACKEND/health" | grep "ok"; then
    echo "Health check passed!"
else
    echo "Health check failed!"
    docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" down
    exit 1
fi

# Nginx切り替え
echo "Switching traffic..."
cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:$NEW_PORT_FRONTEND; }
upstream current_backend { server 127.0.0.1:$NEW_PORT_BACKEND; }
upstream current_sticky { server 127.0.0.1:$NEW_PORT_STICKY; }
EOF

# Nginx設定リロード
sudo systemctl reload nginx

echo "Deployment to $NEW_COLOR successful!"

# 旧環境の停止
echo "Stopping old environment ($CURRENT_COLOR)..."
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$CURRENT_COLOR" down

echo "Done."
