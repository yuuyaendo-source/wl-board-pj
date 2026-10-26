# 本番環境の構成（Docker 版）

Board System を **Docker** で本番デプロイしている場合の構成の整理です。**ホスト上で alembic や sqlite3 を実行しても本番の DB には届きません。**

---

## 1. 全体像

| 役割 | どこで動く | 使う DB / 設定 |
| ------ | ------------ | ----------------- |
| **データベース** | Docker コンテナ `linko-db`（PostgreSQL） | データはボリューム `postgres_data` に永続化 |
| **Board System API** | Docker コンテナ `linko-backend-blue` または `linko-backend-green` | コンテナの環境変数で **PostgreSQL** に接続 |
| **Board System フロント** | Docker コンテナ `linko-frontend-blue/green` | API の URL はビルド時に埋め込み |
| **付箋ボード** | Docker コンテナ `linko-sticky-note-blue/green` | 付箋データはボリューム `sticky_data` |
| **Nginx** | **ホスト**（Docker の外） | 80/443 で受け、`active_env.conf` の通り Blue または Green のポートに振り分け |

- **本番のアプリ用 DB は PostgreSQL だけ**です。  
- ホストの `/var/www/wlinko-pj/board-system/backend/board.db`（SQLite）は **本番の稼働には使われていません**。  
- ホストの `backend/.env` も、**コンテナ内の API は参照しません**（コンテナは `docker-compose.prod.yml` の `environment` で `DATABASE_URL` などを渡しているため）。

---

## 2. なぜ「SQLite」や「table users already exists」が出たか

- あなたが実行した `alembic upgrade heads` は **ホスト上**（`devuser01@wlboardsys-app-01` のシェル）で動いています。
- そのとき使われるのは **ホストの** `board-system/backend/.env` と、そこに書かれた `DATABASE_URL` です。
- 多くの場合、開発用に `DATABASE_URL=sqlite+aiosqlite:///./board.db` のままなので、**ホスト上の SQLite ファイル（board.db）** に対してマイグレーションが走ります。
- その SQLite が「既にテーブルあり・alembic_version は空」のような状態だと、「table users already exists」になります。
- **本番で実際に使っている PostgreSQL（linko-db）には、この操作は一切反映されません。**

つまり:

- **本番のデータ** → PostgreSQL（コンテナ内）
- **ホストで alembic を実行** → ホストの .env の DB（多くの場合 SQLite）に対して実行される

という「別々の DB」になっています。

---

## 3. 本番でマイグレーションをかける正しいやり方

本番のスキーマを更新するときは、**必ず「API が動いているコンテナの中」で** alembic を実行します。そうすると、そのコンテナの環境変数（PostgreSQL の `DATABASE_URL`）に対してマイグレーションがかかります。

### 3.1 いまどちらのコンテナが本番か確認する

```bash
cat /etc/nginx/conf.d/active_env.conf
```

- `127.0.0.1:8010` と書いてあれば **Blue** が本番 → コンテナ名は `linko-backend-blue`
- `127.0.0.1:8020` と書いてあれば **Green** が本番 → コンテナ名は `linko-backend-green`

### 3.2 そのコンテナ内でマイグレーションを実行する

```bash
# Blue が本番の場合
docker exec -it linko-backend-blue alembic upgrade head

# Green が本番の場合
docker exec -it linko-backend-green alembic upgrade head
```

- 複数 head がある状態を解消したマージリビジョンまで入れたあとであれば、`alembic upgrade head` で 1 回で最新まで適用されます。
- 実行されるのは **PostgreSQL（linko-db）** に対するマイグレーションです。ホストの SQLite は触りません。

### 3.3 複数 head があった場合（stamp が必要な場合）

「DB には既にテーブルがあるが alembic_version が空」のような状態は、**PostgreSQL 側**で起きているかどうかを先に確認する必要があります。確認も **コンテナ内** で行います。

```bash
# 例: Blue が本番の場合
docker exec -it linko-backend-blue python -c "
from app.config import settings
print(settings.database_url)
"
```

ここで `postgresql+asyncpg://...` と出れば、そのコンテナは本番の PostgreSQL を見ています。

PostgreSQL の現在のバージョンは、同じコンテナで:

```bash
docker exec -it linko-backend-blue alembic current
```

で確認できます。  
「複数 head を解消するマージマイグレーション」を入れたうえで、上記のとおり **コンテナ内** で `alembic stamp` や `alembic upgrade head` を実行してください。ホストの `board.db` や `sqlite3` は本番の構成には含まれていません。

---

## 6. PostgreSQL で「relation "users" already exists」が出る場合（stamp 手順）

**原因**: 本番の PostgreSQL にはすでにテーブルが作られているのに、**alembic_version テーブルが空**（または Alembic が「未適用」と判断している）ため、Alembic が最初のマイグレーションから実行し、「users が既に存在する」とエラーになります。

**対処**: DB の実際の状態に合わせて **stamp** で「ここまで適用済み」と記録してから、**upgrade head** で不足分だけ適用します。

### 6.1 PostgreSQL の状態を確認する（ホストから実行）

```bash
# alembic_version の内容（空なら stamp が必要）
docker exec -it linko-db psql -U linko_user -d linko_board_system -c "SELECT * FROM alembic_version;"

# テーブル一覧（どのマイグレーションまで適用されているか判断するため）
docker exec -it linko-db psql -U linko_user -d linko_board_system -c "\dt"
```

- **user_google_tokens** が一覧に出る → ほぼすべて適用済み
- **user_faces** はあるが **user_google_tokens** がない → d4e5 まで適用済み
- **user_faces** もない（users, sticky_notes, board_placements などだけ）→ b2c3 まで適用済みとみなす

### 6.2 状態に合わせて stamp → upgrade（Green が本番の例）

**重要**: マージ用リビジョン `f6a7b8c9d0e1` は、**そのリビジョンを含むイメージをビルドしたコンテナ**でないと参照できません。「Can't locate revision identified by 'f6a7b8c9d0e1'」と出る場合は、**まだデプロイ（再ビルド）していない**か、古いイメージのコンテナで実行しています。

**すべてのテーブル（user_google_tokens 含む）がすでにある場合**は、次のどちらかで対応できます。

---

**方法 A: いったん e5f6 で stamp してから、あとでデプロイ＋upgrade**

1. 現在のイメージのまま、`user_google_tokens` 追加リビジョンで stamp する:

   ```bash
   docker exec -it linko-backend-green alembic stamp e5f6a7b8c9d0
   ```

2. あとでコードを更新してデプロイする（`git pull` → `./deploy.sh`）。新しいイメージにマージ用マイグレーションが入る。

3. デプロイ後、**いま本番になっている方**のコンテナで:

   ```bash
   docker exec -it linko-backend-green alembic upgrade head
   ```

   または Blue に切り替わっていれば `linko-backend-blue`。これでマージリビジョン（f6a7b8c9d0e1）が適用される。

---

**方法 B: 先にデプロイしてから stamp（推奨）**

1. リポジトリを更新してデプロイし、マージ用マイグレーションを含むイメージでコンテナを起動する:

   ```bash
   cd /var/www/wlinko-pj && git pull
   cd board-system/deploy && ./deploy.sh
   ```

2. デプロイ後、本番側のコンテナで stamp する（`active_env.conf` で 8010 なら blue、8020 なら green）:

   ```bash
   docker exec -it linko-backend-green alembic stamp f6a7b8c9d0e1
   ```

   または

   ```bash
   docker exec -it linko-backend-blue alembic stamp f6a7b8c9d0e1
   ```

---

**user_faces はあるが user_google_tokens がない場合**

d4e5 まで適用済みとみなし、そのあと upgrade head で e5f6（user_google_tokens）とマージを適用します。

```bash
docker exec -it linko-backend-green alembic stamp d4e5f6a7b8c9
docker exec -it linko-backend-green alembic upgrade head
```

（コンテナにマージ用マイグレーションが含まれていない場合は、先にデプロイしてから実行してください。）

---

**user_faces もない / どれかわからない場合**

b2c3 まで適用済みとみなし、そのあと upgrade head で残りをまとめて適用します。

```bash
docker exec -it linko-backend-green alembic stamp b2c3d4e5f6a7
docker exec -it linko-backend-green alembic upgrade head
```

### 6.3 確認

```bash
docker exec -it linko-backend-green alembic current
```

`f6a7b8c9d0e1 (head)` と出れば、最新まで一致しています。

---

## 4. 本番の状態を確認するコマンド一覧

| 確認したいこと | コマンド |
| ---------------- | ---------- |
| いまどちらが本番か（Blue/Green） | `cat /etc/nginx/conf.d/active_env.conf` |
| 動いているコンテナ | `docker ps`（`linko-backend-*`, `linko-db`, `linko-frontend-*`, `linko-sticky-note-*` を確認） |
| DB コンテナ（PostgreSQL）の状態 | `docker ps | grep linko-db` |
| 本番 API のヘルス | `curl -s http://localhost:8010/health` または `8020`（active_env.conf のポートに合わせる） |
| コンテナ内のマイグレーション現在値 | `docker exec -it linko-backend-blue alembic current`（または green） |

---

## 5. まとめ

- **本番は Docker 構成**で、**DB は PostgreSQL（linko-db コンテナ）のみ**。
- ホストの `board-system/backend/board.db` や `backend/.env` の SQLite 設定は、**本番の稼働・本番のデータには使われていない**。
- **マイグレーションは必ずコンテナ内で実行する**:  
  `docker exec -it linko-backend-blue alembic upgrade head`（または green）。
- ホストに `sqlite3` が入っていなくても、本番の構成・本番のデータには影響しません。本番のデータはすべて PostgreSQL にあります。
