#!/bin/bash
# ========================================
# 付箋ボード - バージョン指定デプロイ（前バージョン残し・新バージョン追加）
# ========================================
# 使い方: ./deploy-versioned.sh <バージョン名> <ポート>
# 例:     ./deploy-versioned.sh v1 3000   # 旧版
# 例:     ./deploy-versioned.sh v2 3001   # 新版
# ========================================

set -e

VERSION="${1:-v2}"
PORT="${2:-3001}"
APP_NAME="wl-sticky-note-${VERSION}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}付箋ボード バージョン別デプロイ${NC}"
echo -e "${YELLOW}  バージョン: ${VERSION}  ポート: ${PORT}  PM2名: ${APP_NAME}${NC}"
echo -e "${YELLOW}========================================${NC}"

# 1. 依存関係
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
npm install

# 2. ビルド
echo -e "${YELLOW}🔨 Building Next.js application...${NC}"
npm run build

# 3. ログディレクトリ
mkdir -p logs

# 4. 既存の同名 PM2 プロセスがあれば停止・削除
echo -e "${YELLOW}🔄 Stopping existing process (if any): ${APP_NAME}${NC}"
pm2 delete "$APP_NAME" 2>/dev/null || true

# 5. 起動（PORT を環境変数で渡す）
echo -e "${YELLOW}🚀 Starting ${APP_NAME} on port ${PORT}...${NC}"
PORT="$PORT" NODE_ENV=production pm2 start server.js \
  --name "$APP_NAME" \
  --output "./logs/${VERSION}-out.log" \
  --error "./logs/${VERSION}-err.log" \
  --time \
  --env production

# 6. PM2 保存
pm2 save

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployed: ${APP_NAME} (port ${PORT})${NC}"
echo -e "${GREEN}========================================${NC}"
echo "  pm2 logs ${APP_NAME}"
echo "  pm2 restart ${APP_NAME}"
echo "  pm2 stop ${APP_NAME}"
echo ""
