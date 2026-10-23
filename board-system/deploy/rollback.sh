#!/usr/bin/env bash
set -e

# 設定
APP_DIR="/var/www/wlinko-pj/board-system"
NGINX_CONF_DIR="/etc/nginx/conf.d"
ACTIVE_ENV_FILE="$NGINX_CONF_DIR/active_env.conf"
DOCKER_COMPOSE_FILE="$APP_DIR/docker-compose.prod.yml"

# .env ファイルが存在する場合は環境変数を読み込む
if [ -f "$APP_DIR/.env" ]; then
  set -a
  source "$APP_DIR/.env"
  set +a
fi

# 現在のアクティブ環境を確認し、切り替え先（旧環境）を特定
if grep -q "3010" "$ACTIVE_ENV_FILE"; then
    CURRENT_ENV="blue"
    TARGET_ENV="green"
    TARGET_PORT_FRONTEND="3020"
    TARGET_PORT_BACKEND="8020"
    TARGET_PORT_STICKY="3021"
else
    CURRENT_ENV="green"
    TARGET_ENV="blue"
    TARGET_PORT_FRONTEND="3010"
    TARGET_PORT_BACKEND="8010"
    TARGET_PORT_STICKY="3011"
fi

echo "Current active environment: $CURRENT_ENV"
echo "Target rollback environment: $TARGET_ENV"

# 1. 切り替え先（旧環境）の環境変数をエクスポートし、コンテナを起動
echo "Starting rollback environment containers ($TARGET_ENV)..."
export COLOR=$TARGET_ENV
export PORT_FRONTEND=$TARGET_PORT_FRONTEND
export PORT_BACKEND=$TARGET_PORT_BACKEND
export PORT_STICKY=$TARGET_PORT_STICKY

docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$TARGET_ENV" up -d

# 2. ヘルスチェック（旧環境のバックエンドが応答するまで待機）
echo "Waiting for health check on $TARGET_ENV..."
for i in $(seq 1 18); do
    if curl -sf "http://localhost:$TARGET_PORT_BACKEND/health" | grep -q "ok"; then
        echo "Health check passed!"
        break
    fi
    if [ "$i" -eq 18 ]; then
        echo "Health check failed after 90s for $TARGET_ENV. Rollback aborted."
        exit 1
    fi
    echo "  attempt $i/18, retrying in 5s..."
    sleep 5
done

# 3. Nginx の upstream 設定を旧環境に切り替え
echo "Switching Nginx traffic to $TARGET_ENV..."
cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:$TARGET_PORT_FRONTEND; }
upstream current_backend { server 127.0.0.1:$TARGET_PORT_BACKEND; }
upstream current_sticky { server 127.0.0.1:$TARGET_PORT_STICKY; }
EOF

# 4. Nginx 設定リロード
sudo systemctl reload nginx

echo "Rollback to $TARGET_ENV successful!"

# 5. 障害のあった環境のコンテナを停止
echo "Stopping failed environment ($CURRENT_ENV)..."
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$CURRENT_ENV" down

echo "Done."