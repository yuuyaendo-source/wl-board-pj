#!/bin/bash

# ========================================
# wl-sticky-note - Ubuntu 初回デプロイ用スクリプト
# ========================================
# 実行場所: 02_1_sticky-note/src（サーバでは /var/www/wl-sticky-note/02_1_sticky-note/src）

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. System Update and Dependencies Installation
echo -e "${YELLOW}📦 Installing system dependencies...${NC}"
sudo apt update
sudo apt install -y curl git nginx

# 2. Install Node.js (using NodeSource - Node.js 20.x LTS)
echo -e "${YELLOW}📦 Installing Node.js 20.x LTS...${NC}"
if ! command -v node &> /dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt install -y nodejs
fi

echo "✅ Node.js version: $(node -v)"
echo "✅ npm version: $(npm -v)"

# 3. Install PM2 globally
echo -e "${YELLOW}📦 Installing PM2...${NC}"
if ! command -v pm2 &> /dev/null; then
    sudo npm install -g pm2
fi

echo "✅ PM2 version: $(pm2 -v)"

# 4. Create logs directory
mkdir -p logs

# 5. Install project dependencies
echo -e "${YELLOW}📦 Installing project dependencies...${NC}"
npm install

# 6. Build Next.js application
echo -e "${YELLOW}🔨 Building Next.js application...${NC}"
npm run build

# 7. Stop existing PM2 process (if any)
echo -e "${YELLOW}🔄 Stopping existing process...${NC}"
pm2 delete wl-sticky-note 2>/dev/null || true

# 8. Start application with PM2
echo -e "${YELLOW}🚀 Starting application with PM2...${NC}"
pm2 start ecosystem.config.js --env production

# 9. Save PM2 process list
pm2 save

# 10. Setup PM2 to start on system boot
echo -e "${YELLOW}⚙️  Setting up PM2 startup...${NC}"
sudo env PATH=$PATH:/usr/bin pm2 startup systemd -u $USER --hp $HOME

# 11. Configure Nginx
echo -e "${YELLOW}⚙️  Configuring Nginx...${NC}"
NGINX_CONF="/etc/nginx/sites-available/wl-sticky-note"
NGINX_ENABLED="/etc/nginx/sites-enabled/wl-sticky-note"

sudo cp nginx.conf $NGINX_CONF

# Remove default site if it exists
sudo rm -f /etc/nginx/sites-enabled/default

# Enable the site
sudo ln -sf $NGINX_CONF $NGINX_ENABLED

# Test Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# 12. Configure firewall (if ufw is installed)
if command -v ufw &> /dev/null; then
    echo -e "${YELLOW}🔒 Configuring firewall...${NC}"
    sudo ufw allow 80/tcp
    sudo ufw allow 22/tcp
    echo "✅ Firewall rules added"
fi

# 13. Display status
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "📊 Application status:"
pm2 list
echo ""
echo "🌐 Access: https://wlboardsys.internal.wonder-link.co.jp または https://172.16.1.203"
echo ""
echo "📝 Useful commands:"
echo "  - View logs:     pm2 logs wl-sticky-note"
echo "  - Restart app:   pm2 restart wl-sticky-note"
echo "  - Stop app:      pm2 stop wl-sticky-note"
echo "  - Nginx status:  sudo systemctl status nginx"
echo ""
