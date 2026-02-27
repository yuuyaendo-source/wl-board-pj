#!/usr/bin/env bash
set -e

# 設定
NGINX_CONF_DIR="/etc/nginx/conf.d"
ACTIVE_ENV_FILE="$NGINX_CONF_DIR/active_env.conf"

# 現在のアクティブ環境を確認
if grep -q "3010" "$ACTIVE_ENV_FILE"; then
    CURRENT_PORT="3010"
    TARGET_PORT="3020"
    TARGET_ENV="green"
else
    CURRENT_PORT="3020"
    TARGET_PORT="3010"
    TARGET_ENV="blue"
fi

echo "Rolling back to: $TARGET_ENV ($TARGET_PORT)"

# 単純に Nginx の向き先を元に戻す
cat <<EOF > "$ACTIVE_ENV_FILE"
upstream current_frontend { server 127.0.0.1:$TARGET_PORT; }
# backend, sticky も同様に変数のポート番号を使って戻す必要があるが
# 簡易的に、TARGET_ENV に応じてハードコードするか、deploy.sh と同様のロジックで戻す
EOF

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
