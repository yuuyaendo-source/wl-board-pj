#!/usr/bin/env bash
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

# --- 確実なDB起動待ち ---
echo "Waiting for PostgreSQL to start..."
until docker exec linko-db pg_isready -U linko_user > /dev/null 2>&1; do
  echo "PostgreSQL is unavailable - sleeping..."
  sleep 1
done
echo "PostgreSQL is up and running!"
# ------------------------

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

# --- 付箋データ: 共有ボリューム準備 + デプロイ前バックアップ（サイズガード付き） ---
STICKY_BACKUP_DIR="$APP_DIR/backups/sticky-note"
KEEP_BACKUPS=30
mkdir -p "$STICKY_BACKUP_DIR"

# 1) 現在の付箋コンテナから boards.json をバックアップ（空ファイル除外ガード）
CURRENT_STICKY_CONTAINER="linko-sticky-note-${CURRENT_COLOR}"
if docker inspect "$CURRENT_STICKY_CONTAINER" >/dev/null 2>&1; then
    BACKUP_FILE="$STICKY_BACKUP_DIR/boards_$(date +%Y%m%d_%H%M%S).json"
    FILE_SIZE=$(docker exec "$CURRENT_STICKY_CONTAINER" sh -c '[ -f /app/data/boards.json ] && wc -c < /app/data/boards.json || echo 0' 2>/dev/null | tr -cd '0-9')
    FILE_SIZE=${FILE_SIZE:-0}
    if [ "$FILE_SIZE" -gt 100 ]; then
        if docker cp "$CURRENT_STICKY_CONTAINER:/app/data/boards.json" "$BACKUP_FILE" 2>/dev/null; then
            echo "Backed up sticky-note data ($FILE_SIZE bytes) to $BACKUP_FILE"
        fi
    else
        echo "⚠️  Skipped backup: /app/data/boards.json in $CURRENT_STICKY_CONTAINER is empty or too small ($FILE_SIZE bytes)"
    fi
fi

# 古いバックアップを残す件数に制限
if command -v ls >/dev/null 2>&1; then
    (cd "$STICKY_BACKUP_DIR" && ls -t boards_*.json 2>/dev/null | tail -n +$((KEEP_BACKUPS + 1)) | xargs -r rm -- 2>/dev/null || true)
fi

# 2) 付箋用共有ボリューム（blue/green 共通）が無ければ作成
docker volume create sticky_note_data 2>/dev/null || true

# 3) 初回移行用: 共有ボリューム側にデータがなく、現在色の旧ボリュームに正常なデータがある場合のみコピー（上書き巻き戻し防止）
CURRENT_VOLUME_NAME="board-system-${CURRENT_COLOR}_sticky_data"
if docker volume inspect "$CURRENT_VOLUME_NAME" >/dev/null 2>&1; then
    docker run --rm \
        -v "$CURRENT_VOLUME_NAME:/from" \
        -v sticky_note_data:/to \
        alpine sh -c '
            if [ -f /from/boards.json ] && [ ! -s /to/boards.json ]; then
                SIZE=$(wc -c < /from/boards.json | tr -cd "0-9")
                if [ "${SIZE:-0}" -gt 100 ]; then
                    cp -f /from/boards.json /to/boards.json
                    echo "Initial migration: Synced boards.json ($SIZE bytes) to shared volume"
                else
                    echo "⚠️ Skipped syncing: /from/boards.json is too small ($SIZE bytes)"
                fi
            elif [ -s /to/boards.json ]; then
                echo "Shared volume already has boards.json ($(wc -c < /to/boards.json | tr -cd "0-9") bytes), skipping legacy volume sync."
            fi
        '
fi

echo "Starting new containers..."
export COLOR=$NEW_COLOR
export PORT_FRONTEND=$NEW_PORT_FRONTEND
export PORT_BACKEND=$NEW_PORT_BACKEND
export PORT_STICKY=$NEW_PORT_STICKY

# DBは別ファイルで起動済みなのでここではアプリのみ起動
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" up -d --build

# ヘルスチェック
echo "Waiting for health check..."
for i in $(seq 1 18); do
    if curl -sf "http://localhost:$NEW_PORT_BACKEND/health" | grep -q "ok"; then
        echo "Health check passed!"
        break
    fi
    if [ "$i" -eq 18 ]; then
        echo "Health check failed after 90s. Backend logs:"
        docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" logs backend 2>&1 | tail -80
        docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" down
        exit 1
    fi
    echo "  attempt $i/18, retrying in 5s..."
    sleep 5
done

# マイグレーション実行（新コンテナ＝新イメージで実行）
echo "Running database migrations..."
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" exec -T backend alembic -c /app/alembic.ini upgrade head

echo "Running team seeds..."
docker compose -f "$DOCKER_COMPOSE_FILE" -p "board-system-$NEW_COLOR" exec -T backend python scripts/seed_teams.py

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