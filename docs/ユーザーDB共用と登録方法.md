# ユーザーDB共用と登録方法

パーソナルボード用のユーザーは **Board System の PostgreSQL の `users` テーブル** に格納され、以下で**共通**で利用されます。

- **Board System** … パーソナルボードのメンバー一覧・付箋の持ち主・Google カレンダー連携
- **デスクトップアプリ** … メールアドレスでユーザーを解決し、各自のパーソナルボードを開く（`/users/by_email`）
- **seed スクリプト** … 初回セットアップ時に id 1〜7 などを一括登録

---

## ユーザー登録の方法

### 1. Board System の画面から（推奨）

1. Board System にブラウザでアクセス（例: `/boards/taskboard` や `/boards/personal/5`）
2. **「ユーザー管理」** をクリック
3. **名前（必須）**・**メールアドレス（任意）**・**呼び名（任意）** を入力して **「追加」**

- ここで登録したユーザーはすぐにパーソナルボードのメンバー一覧に表示されます。
- **メールアドレス**を登録しておくと、デスクトップアプリの「ボード」クリック時にメールで紐づけ、その人のパーソナルボードを開けます。
- 同じ `users` テーブルを参照するため、**Linko や他機能ともユーザーDBは共用**です。

#### 既存ユーザーに情報を追加・変更する

すでに作成済みのユーザー（seed や名前のみで追加したユーザー）に、メールアドレスや呼び名を登録する場合:

1. **「ユーザー管理」** を開く
2. 一覧で該当ユーザーの **「編集」** をクリック
3. **名前**・**メールアドレス**・**呼び名** を入力し **「保存」**

- 変更は共通の `users` テーブルに反映され、デスクトップアプリのメール紐づけや Linko 側からも同じ内容が参照されます。

### 2. API から（スクリプト・連携用）

```bash
# 新規作成（name 必須、email / call_name / role は任意）
curl -X POST "https://<Board System API>/users" \
  -H "Content-Type: application/json" \
  -d '{"name":"山田 太郎","email":"yamada@example.com","call_name":"山田"}'
```

### 3. 初回セットアップ用 seed スクリプト

`board-system/backend/scripts/seed_personal_members.py` で、id 1〜7 のユーザーを名前のみで一括登録できます。**同じ users テーブル**に追加されます。

- 運用中のユーザー登録は **Board System の「ユーザー管理」** または API で行い、seed は空 DB の初期投入用として使う想定です。
- seed で追加したユーザーにメールを付ける場合は、Board System の「ユーザー管理」で **「編集」** から登録するか、API で `PATCH /users/{id}` を呼びます。

---

## 顔登録（user_faces）との関係

- **顔画像**は、同じ PostgreSQL 内の **`user_faces`** テーブルに保存されます（1ユーザーあたり複数枚可）。
- **Linko システム側で顔登録**している場合、そのデータもこの `user_faces` を参照しているため、**Board System と Linko で顔データは共用**です。
- 顔の登録・削除・一覧は Board System の API で行えます:
  - `GET /users/{user_id}/faces` … 一覧
  - `POST /users/{user_id}/faces` … 追加（JSON: `body.image` に data URL / base64、または multipart で file）
  - `DELETE /users/{user_id}/faces/{face_id}` … 削除
- Linko 側の管理画面で顔を登録すると、同じユーザーが Board System のパーソナルボード等でも同じ顔データとして参照されます。

---

## データベース

- **本番**: Docker の PostgreSQL（`linko-db`、DB 名 `linko_board_system`）
- **開発**: SQLite または PostgreSQL（`board-system/backend` の `DATABASE_URL`）
- Board System のバックエンドがこの DB に接続し、**`users`** と **`user_faces`**（顔画像）を読み書きします。デスクトップアプリや Linko は Board System の API 経由で同じユーザー・顔データを参照します。
