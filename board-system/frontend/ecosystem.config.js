// PM2 本番起動用（サーバでは cwd を絶対パスに変更して使用）
// 例: cd /var/www/wl-sticky-note/board-system/frontend && pm2 start ecosystem.config.js
module.exports = {
  apps: [{
    name: 'board-system-frontend',
    script: 'node_modules/next/dist/bin/next',
    args: 'start -p 3001',
    cwd: __dirname,
    env: { NODE_ENV: 'production', PORT: '3001' },
    instances: 1,
    autorestart: true,
    max_restarts: 10,
    min_uptime: '10s',
  }],
};
