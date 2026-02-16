# ローカルで Docker をビルドしてテストする手順

手元の PC で付箋ボード＋Board System を Docker で起動し、動作確認するまでの手順です。

---

## 前提

- **Docker Desktop**（または Docker Engine + Docker Compose v2）がインストール済みであること
- リポジトリを clone 済みで、**02_1_sticky-note** と **board-system** の両方のディレクトリがあること

---

## 手順

### 1. リポジトリの場所に移動

```powershell
cd C:\Users\hisas\Documents\dev\wlinko-pj
# 実際のパスは環境に合わせてください
```

### 2. 環境変数（任意）

Board System の **AI 自動振り分け**を使う場合は、`.env` を用意します。

```powershell
cd board-system
copy .env.example .env
# .env を開いて GEMINI_API_KEY を設定（任意。未設定でも付箋・タスク・パーソナルは利用可能）
cd ..
```

### 3. ビルドと起動

```powershell
cd board-system
docker compose up -d --build
```

- 初回はイメージのビルドで数分かかることがあります
- **cato-ca.crt** が無くてもビルドできます（証明書はオプション）

### 4. マイグレーション（初回のみ）

PostgreSQL のテーブルを作成します。

```powershell
docker exec linko-backend alembic upgrade head
```

> **補足**: `-it` を付けると「The input device is not a TTY」となる環境では、上記のように `-it` なしで実行してください。

### 5. アクセスしてテスト

ブラウザで次の URL を開きます。

| 用途 | URL |
|------|-----|
| **Board System**（タスク・パーソナル・Meeting） | http://localhost:3010 |
| **付箋ボード** | http://localhost:3011 |
| **Board System API**（ヘルス確認） | http://localhost:8010/health |

- 付箋ボードで付箋を作成 → Board System の「取り込み」で取り込み
- タスクボード・パーソナルボード・Meeting の各機能を確認

### 6. 停止するとき

```powershell
cd board-system
docker compose down
```

---

## 検証用に「何もない状態」からやり直す

マイグレーションやデータをゼロから検証したいときは、**ボリュームごと削除**してから起動し直します。

```powershell
cd board-system
docker compose down -v
docker compose up -d --build
```

- `-v` で **named volume**（`postgres_data`・`sticky_data`）も削除されるため、DB と付箋ボードのデータが消えます。
- 再起動後は DB が空なので、**初回だけ**マイグレーションを実行します。

  ```powershell
  docker exec linko-backend alembic upgrade head
  ```

これで「relation already exists」なしに、初期スキーマから最新（応援要請の lane 変更まで）が適用された状態で検証できます。

---

## ポート一覧（ローカル）

| サービス | ホストポート | 用途 |
|----------|--------------|------|
| Frontend | 3010 | Board System（Next.js） |
| Sticky Note | 3011 | 付箋ボード |
| Backend | 8010 | Board System API |
| PostgreSQL | 5433 | DB（通常は直接アクセスしない） |

---

## トラブルシューティング

| 現象 | 対処 |
|------|------|
| ビルドが遅い・止まる | プロキシ環境では `$env:DOCKER_BUILDKIT=0` を設定してから `docker compose up -d --build` を再実行 |
| マイグレーションで「relation already exists」 | DB に既にテーブルがあるため。**スタンプ**してから `upgrade head` する（下記「既存DBでマイグレーションを進める」参照） |
| コンテナが起動しない | `docker compose logs backend` などでログを確認 |

---

## 既存DBでマイグレーションを進める

`alembic upgrade head` で「relation "users" already exists」などと出る場合は、テーブルが既に存在するためです。Alembic に「このリビジョンまで適用済み」と教えてから、その先だけ適用します。

### 手順（Docker で backend を実行している場合）

1. **初期スキーマだけある場合**（users / sticky_notes / board_placements はあるが、`sticky_notes` に `postit_board_id` がない場合）  
   コンテナ内で:
   ```powershell
   docker exec linko-backend alembic stamp 18f12e452b24
   docker exec linko-backend alembic upgrade head
   ```

2. **Postit 用カラムも既にある場合**（`sticky_notes` に `postit_board_id` / `postit_note_id` がある場合）  
   ```powershell
   docker exec linko-backend alembic stamp a1b2c3d4e5f6
   docker exec linko-backend alembic upgrade head
   ```

どちらかで「応援要請」用の `lane` 変更（b2c3d4e5f6a7）まで適用されます。  
`stamp 18f12e452b24` のあと `upgrade head` で「column postit_board_id already exists」が出たら、`stamp a1b2c3d4e5f6` を実行してから再度 `alembic upgrade head` してください。

---

## 参照

- 詳細（本番デプロイ含む）: [docs/本番デプロイ手順_Docker.md](docs/本番デプロイ手順_Docker.md)
- board-system の README: [board-system/README.md](board-system/README.md)
