#!/bin/bash

# Deployment Script for Brainstorming App (Ubuntu)

# 1. Update system and install dependencies
sudo apt update
sudo apt install -y nodejs npm nginx

# 2. Install PM2 globally
sudo npm install -g pm2

# 3. Setup Project Directory (Assuming /var/www/brainstorming)
# sudo mkdir -p /var/www/brainstorming
# sudo chown -R $USER:$USER /var/www/brainstorming

# 4. Install Project Dependencies
npm install

# 5. Build Next.js App
npm run build

# 6. Start with PM2
pm2 start server.js --name "brainstorming-app" --env production

# 7. Save PM2 list
pm2 save
pm2 startup

# 8. Nginx Configuration (Example)
# Create /etc/nginx/sites-available/brainstorming
# server {
#     listen 80;
#     server_name your-domain.com;
#
#     location / {
#         proxy_pass http://localhost:3000;
#         proxy_http_version 1.1;
#         proxy_set_header Upgrade $http_upgrade;
#         proxy_set_header Connection 'upgrade';
#         proxy_set_header Host $host;
#         proxy_cache_bypass $http_upgrade;
#     }
# }

echo "Deployment setup complete! Don't forget to configure Nginx."
