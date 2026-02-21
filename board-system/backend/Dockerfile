# ベースイメージ: Python 3.11 軽量版
FROM python:3.11-slim

WORKDIR /app

# PostgreSQL接続用ライブラリのビルドに必要なシステムパッケージ
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# ライブラリ一覧をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir asyncpg psycopg2-binary

# ソースコードをコピー
COPY . .

# CATO Networks SSL対応: 証明書があれば信頼ストアに追加（ローカルでは省略可）
RUN if [ -f cato-ca.crt ]; then cp cato-ca.crt /usr/local/share/ca-certificates/cato-ca.crt && update-ca-certificates; fi
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt

EXPOSE 8000

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# 起動コマンド
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]