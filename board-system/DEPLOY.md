# Board System 本番デプロイ（Docker）— 要約

本システム（付箋ボード + Board System）を Docker で本番運用する際の、**このディレクトリでの操作**の要約です。

**手順の詳細（前提条件・リポジトリ配置・Nginx・マイグレーション・データ移行・ロールバック・運用・トラブルシューティング）はすべて [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md) にあります。** 初回デプロイや運用で迷ったらそちらを参照してください。

---

## 構成の整理

| 項目 | 内容 |
|------|------|
| アプリ（Blue/Green） | `docker-compose.prod.yml` |
| DB | `docker-compose.db.yml`（PostgreSQL） |
| デプロイ・ロールバック | `deploy/deploy.sh`、`deploy/rollback.sh` |
| Nginx 設定例 | `nginx/nginx.conf` |

本番では Nginx が Port 80 で受け、`active_env.conf` で Blue または Green のポートに振り分けます。

---

## よく使うコマンド

| やりたいこと | コマンド |
|--------------|----------|
| 初回・コード更新のデプロイ | `cd deploy && ./deploy.sh` |
| ロールバック | `cd deploy && ./rollback.sh` |
| マイグレーション | `docker exec -it linko-backend-blue alembic upgrade head`（稼働中は blue または green） |
| ログを見る | `docker logs -f linko-backend-blue`（または green） |
| 稼働中環境の確認 | `cat /etc/nginx/conf.d/active_env.conf` |

---

## 参照

- **詳細手順・運用・トラブルシューティング**: [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md)
- **デプロイ・運用ドキュメントの索引**: [docs/デプロイ・運用.md](../docs/デプロイ・運用.md)
