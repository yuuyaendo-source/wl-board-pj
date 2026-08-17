#!/usr/bin/env bash
set -e

# 設定
NGINX_CONF_DIR="/etc/nginx/conf.d"
ACTIVE_ENV_FILE="$NGINX_CONF_DIR/active_env.conf"

# 現在のアクティブ環境を確認
if grep -q "3010" "$ACTIVE_ENV_FILE"; then
    TARGET_ENV="green"
else
    TARGET_ENV="blue"
fi

echo "Rolling back to: $TARGET_ENV"

# Nginx の向き先を元に戻す
if [ "$TARGET_ENV" = "blue" ]; then
    cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:3010; }
upstream current_backend { server 127.0.0.1:8010; }
upstream current_sticky { server 127.0.0.1:3011; }
EOF
else
    cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:3020; }
upstream current_backend { server 127.0.0.1:8020; }
upstream current_sticky { server 127.0.0.1:3021; }
EOF
fi

# Nginx設定リロード
sudo systemctl reload nginx

echo "Rollback successful!"