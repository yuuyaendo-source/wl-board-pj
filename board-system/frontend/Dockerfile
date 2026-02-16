# ベースイメージ: Node.js 20 軽量版
FROM node:20-alpine

WORKDIR /app

# 依存関係ファイルだけ先にコピー（キャッシュ効率化）
COPY package.json package-lock.json* ./

# インストール実行
RUN npm install


# ソースコードをコピー
COPY . .

# CATO Networks SSL対応: 証明書があれば信頼ストアに追加（ローカルでは省略可）
RUN if [ -f cato-ca.crt ]; then cat cato-ca.crt >> /etc/ssl/certs/ca-certificates.crt; fi
ENV NODE_EXTRA_CA_CERTS=/etc/ssl/certs/ca-certificates.crt

# ビルド時に環境変数を受け取る（NEXT_PUBLIC_* はビルド時に埋め込まれる）
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ARG NEXT_PUBLIC_BASE_PATH=""
ARG NEXT_PUBLIC_LEGACY_BOARD_URL=http://localhost:3000

ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
ENV NEXT_PUBLIC_BASE_PATH=${NEXT_PUBLIC_BASE_PATH}
ENV NEXT_PUBLIC_LEGACY_BOARD_URL=${NEXT_PUBLIC_LEGACY_BOARD_URL}

# Next.js ビルド
ENV NODE_ENV=production
RUN npm run build

EXPOSE 3000

# 本番モードで起動
CMD ["npm", "run", "start"]