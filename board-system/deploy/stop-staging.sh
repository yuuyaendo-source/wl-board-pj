#!/bin/bash
set -e
# ステージング環境を停止する。本番には影響しない。
APP_DIR="/var/www/wlinko-pj/board-system"
docker compose -f "$APP_DIR/docker-compose.prod.yml" -f "$APP_DIR/docker-compose.staging.yml" -p board-system-staging down
echo "Staging stopped."