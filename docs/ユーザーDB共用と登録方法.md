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
- seed で追加したユーザーにメールを付けたい場合は、Board System の API で `PATCH /users/{id}` するか、今後 UI で編集機能を追加して対応できます。

---

## データベース

- **本番**: Docker の PostgreSQL（`linko-db`、DB 名 `linko_board_system`）
- **開発**: SQLite または PostgreSQL（`board-system/backend` の `DATABASE_URL`）
- Board System のバックエンドがこの DB に接続し、`users` を読み書きします。デスクトップアプリや他サービスは Board System の API（`/users`, `/users/by_email`）経由で同じユーザーを参照します。
