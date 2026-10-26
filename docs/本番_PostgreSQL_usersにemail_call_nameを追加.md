# 本番 PostgreSQL: users に email / call_name が無い場合の追加手順

**エラー**: `column users.email does not exist` でアプリ起動失敗。

**原因**: DB には `user_faces` や `user_google_tokens` はあるが、`users` テーブルに `email` / `call_name` を追加するマイグレーション（d4e5f6a7b8c9）が適用されていない。

**対処**: PostgreSQL に直接カラムとインデックスを追加してから、Alembic を stamp する。

---

## 1. PostgreSQL でカラム追加（本番サーバで実行）

```bash
docker exec -it linko-db psql -U linko_user -d linko_board_system -c "
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS call_name VARCHAR(255);
CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users(email);
"
```

- `IF NOT EXISTS` のため、すでに存在していてもエラーにならない。

---

## 2. Alembic を「適用済み」に stamp（本番の backend コンテナで）

いま本番になっている方の backend で実行（Green が本番なら green）。

```bash
# 本番が Green の場合
docker exec -it linko-backend-green alembic stamp e5f6a7b8c9d0
```

- マージ用マイグレーション（f6a7b8c9d0e1）がイメージに入っている場合は、次で head まで stamp してもよい:

  ```bash
  docker exec -it linko-backend-green alembic stamp f6a7b8c9d0e1
  ```

---

## 3. デプロイを再実行

```bash
cd /var/www/wlinko-pj/board-system/deploy
./deploy.sh
```

- 手順1で `users` に `email` / `call_name` を追加済みなので、lifespan の `seed_personal_users()` が通り、ヘルスチェックも通る想定。

---

## 4. デプロイ成功後に stamp がまだなら

デプロイで Blue に切り替わったあと、マージリビジョンまで揃えたい場合:

```bash
docker exec -it linko-backend-blue alembic current
# e5f6a7b8c9d0 なら、マージを適用したいときのみ:
docker exec -it linko-backend-blue alembic upgrade head
```
