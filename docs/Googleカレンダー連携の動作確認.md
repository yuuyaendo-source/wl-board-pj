# Google カレンダー連携の動作確認手順

パーソナルボードの「今日の予定」で Google カレンダーを表示するための、設定と動作確認の手順です。

---

## 1. マイグレーションの確認（user_google_tokens テーブル）

Google のトークンを保存するテーブルが存在する必要があります。

### やること

**Board System バックエンド**のディレクトリで、Alembic を最新まで適用します。

```bash
cd board-system/backend
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
alembic upgrade head
```

### 確認のしかた

- 成功すると `INFO  [alembic.runtime.migration] Running upgrade xxx -> e5f6a7b8c9d0, add user_google_tokens` のような行が出ます。
- すでに適用済みの場合は `INFO  [alembic.runtime.migration] Context impl ... current revision e5f6a7b8c9d0` のように「current revision」が `e5f6a7b8c9d0` と表示されます。
- SQLite を使っている場合: `sqlite3 board.db ".tables"` で `user_google_tokens` が一覧に出れば OK です。

---

## 2. Google の 3 項目を .env に設定

**設定するファイル**: `board-system/backend/.env`（バックエンドの .env のみ。frontend の .env.local ではありません。）

**追加する 3 項目**（値は Google Cloud Console で取得）:

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `GOOGLE_CALENDAR_CLIENT_ID` | OAuth 2.0 クライアント ID | `123456789-xxx.apps.googleusercontent.com` |
| `GOOGLE_CALENDAR_CLIENT_SECRET` | 上記クライアントのシークレット | `GOCSPX-xxxxxx` |
| `GOOGLE_CALENDAR_REDIRECT_URI` | コールバック用の URL（後述） | 下の「リダイレクト URI」を参照 |

### Google Cloud Console での準備

1. [Google Cloud Console](https://console.cloud.google.com/) でプロジェクトを選択（または新規作成）。
2. **API とサービス** → **認証情報** → **認証情報を作成** → **OAuth 2.0 クライアント ID**。
3. アプリケーションの種類: **ウェブアプリケーション**。
4. **承認済みのリダイレクト URI** に、次のどちらかを追加:
   - **ローカル開発**: `http://localhost:8000/auth/google/callback`
   - **本番**: `https://あなたのドメイン/api/bs/auth/google/callback`  
     （Board System API が `/api/bs/` で提供されている場合）
5. 作成後に表示される **クライアント ID** と **クライアントシークレット** をコピーし、`.env` に貼り付けます。

### .env の記述例（ローカル開発）

```env
GOOGLE_CALENDAR_CLIENT_ID=123456789-xxxx.apps.googleusercontent.com
GOOGLE_CALENDAR_CLIENT_SECRET=GOCSPX-xxxxxxxx
GOOGLE_CALENDAR_REDIRECT_URI=http://localhost:8000/auth/google/callback
```

保存したら、**バックエンドを再起動**（`uvicorn` を一度止めてから再度起動）してください。

---

## 3. OAuth の流れで動作確認する

「ログイン → トークン保存 → パーソナルへリダイレクト」までを確認します。

### 前提

- バックエンドが起動している（例: `uvicorn app.main:app --reload --port 8000`）。
- 確認に使う **ユーザー ID** が分かっている（例: 1）。  
  - 不明な場合: `GET http://localhost:8000/users` で一覧を確認するか、Board System のユーザー管理で確認。

### 手順

1. **OAuth 開始**
   - ブラウザで次の URL を開く:  
     `http://localhost:8000/auth/google?user_id=1`  
     （`user_id=1` は実際のユーザー ID に置き換える）
   - 「Google Calendar is not configured」や「google_calendar_redirect_uri is not set」が出る場合 → 上記 2 の .env とバックエンドの再起動を確認。

2. **Google のログイン画面**
   - Google の認証画面に飛べば OK。
   - アカウントを選び、「〇〇があなたの Google カレンダーを表示することを許可しますか？」で **許可** を押す。

3. **コールバック → トークン保存**
   - 許可後、自動で  
     `http://localhost:8000/auth/google/callback?code=...&state=1`  
     にリダイレクトされ、バックエンドがトークンを交換して **user_google_tokens** に保存します。
   - エラーページが出ずに次のステップに進めれば「トークン保存」まで成功しています。

4. **パーソナルへのリダイレクト**
   - バックエンドは最後に **`/personal/{user_id}`** へリダイレクトします。
   - **本番（Nginx で同一ドメイン）**:  
     `https://あなたのドメイン/personal/1` のように開けば、フロントのパーソナルボードが表示されます。
   - **ローカル開発**:  
     リダイレクト先が `http://localhost:8000/personal/1` になるため、**API サーバにはそのパスがない**と 404 になります。  
     その場合は、手動でフロントのパーソナルを開いてください:  
     `http://localhost:3000/personal/1` または `http://localhost:3000/boards/personal/1`（basePath を使っている場合）。

### ここまでで確認できること

- `.env` の Google 3 項目が正しく読まれている  
- `/auth/google?user_id=<id>` で Google へ飛ぶ  
- 許可後にコールバックでトークンが保存される  
- （本番または手動で）パーソナルボードが開ける  

---

## 4. 「今日の予定」の表示まで確認する（任意）

1. パーソナルボード（`/personal/1` など）を開く。
2. 右側の「今日の予定（カレンダー連携）」枠で **「予定を取得」** をクリック。
3. 問題なければ、Google カレンダーの「今日」の予定が一覧に表示されます。  
   - 503 やエラーになる場合: 上記 1〜2（マイグレーション・.env）と、バックエンドのログを確認してください。

---

## トラブルシューティング

| 症状 | 確認すること |
|------|----------------------|
| 「Google Calendar is not configured」 | `board-system/backend/.env` に 3 項目を書いたか。バックエンドを再起動したか。 |
| 「google_calendar_redirect_uri is not set」 | `GOOGLE_CALENDAR_REDIRECT_URI` を書いたか。値の末尾に余計なスラッシュがないか。 |
| コールバックで「redirect_uri_mismatch」 | Google Cloud Console の「承認済みのリダイレクト URI」と .env の `GOOGLE_CALENDAR_REDIRECT_URI` が**完全に一致**しているか（http/https、ポート、パス）。 |
| コールバック後に 404 | ローカルでは 8000 にリダイレクトされるため 404 になり得る。フロントの URL（例: 3000/personal/1）を手動で開く。 |
| 「予定を取得」で 503 | 上記 1〜2 が済んでいるか。`user_google_tokens` に該当 user_id のトークンが保存されているか。 |
