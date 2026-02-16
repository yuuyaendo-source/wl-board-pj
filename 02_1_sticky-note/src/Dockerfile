FROM node:20-alpine

WORKDIR /app

# 依存関係のインストール（キャッシュ効率化のため先にコピー）
COPY package.json ./

# npm install
RUN npm install


# ソースコードのコピー
COPY . .

# CATO Networks SSL対応: 証明書があれば信頼ストアに追加（ローカルでは省略可）
RUN if [ -f cato-ca.crt ]; then cat cato-ca.crt >> /etc/ssl/certs/ca-certificates.crt; fi
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# Next.js ビルド
RUN npm run build

# データ永続化ディレクトリ（docker-compose でボリュームマウント）
ENV DATA_DIR=/app/data
RUN mkdir -p /app/data && echo "[]" > /app/data/boards.json

EXPOSE 3000

# 本番モードで起動
CMD ["npm", "run", "start"]