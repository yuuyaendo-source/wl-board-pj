# Wonder Linko デスクトップアプリ 自動更新用リリース置き場

このフォルダの **`WonderLinko.msi`** と **`latest.json`** を更新すると、
デスクトップアプリの自動更新が走るようになります。

## 配置ファイル

| ファイル | 説明 |
|---|---|
| `latest.json` | 最新バージョン情報 (`version` と `url`) |
| `WonderLinko.msi` | wl_desktop_app でビルドした MSI (`.\build_msi.ps1` で生成) |

## latest.json 形式

```json
{
  "version": "3.0.1",
  "url": "https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/WonderLinko.msi"
}
```

- `version`: `wl_desktop_app/version.py` と一致させる
- `url`: クライアントが MSI を取得する **絶対 URL**

## ⚠️ 重要: ファイル更新だけでは反映されない

backend Dockerfile は `COPY . .` でこのフォルダを **イメージにビルド時焼き込み**
しているため、ホスト側ファイルを差し替えただけではコンテナから見えません。
**blue/green デプロイで backend イメージを作り直す** ことが必須です。

## アップロード手順 (新バージョンリリース時)

1. **開発側 (dev)**
   - `wl_desktop_app/version.py` の `__version__` を bump (例: `3.0.0` → `3.0.1`)
   - 本書の `latest.json` の `version` を同じ番号に
   - git commit & push

2. **Windows ビルド PC**
   ```powershell
   cd wl-board-pj\wl_desktop_app
   Copy-Item config.production.example.json config.json -Force
   .\build_msi.ps1     # → dist\WonderLinko.msi
   ```

3. **本番サーバへ転送**
   ```powershell
   scp dist\WonderLinko.msi devuser01@wl-board-sys-sv:/var/www/wlinko-pj/board-system/backend/desktop_app_releases/WonderLinko.msi
   ```

4. **本番サーバで反映**
   ```bash
   ssh devuser01@wl-board-sys-sv
   cd /var/www/wlinko-pj
   git pull                        # latest.json 更新を取得
   cd board-system
   ./deploy/deploy.sh              # blue/green デプロイ (backend を再ビルド)
   ```

5. **反映確認**
   ```bash
   curl https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/latest.json
   # → 新 version が返れば成功
   curl -sI https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/WonderLinko.msi | head -3
   # → 200 OK
   ```

6. **クライアント側**
   - 何もしなくて OK。次回起動時の自動チェックで取得 → サイレントインストール
   - トレイ → 「アプリをアップデート」で即時チェックも可能

## やってはいけないこと

- ❌ `latest.json` だけ書き換えて backend 再ビルドしない (反映されない)
- ❌ `docker compose ... up -d --build linko-backend-blue` を直接叩く
  - サービス名は `backend`、container_name は `linko-backend-${COLOR}`。サービス名で指定するか deploy.sh を使う
- ❌ ホスト nginx の reload を忘れる (deploy.sh の中で自動で行うが、手動デプロイ時は要注意)

## クライアント側の設定

デスクトップアプリの `config.json`:

```json
"update_check_url": "https://wl-ai-board.internal.wonder-link.com/api/bs/desktop-app/latest.json"
```

## 詳細な手順とトラブルシューティング

`wl_desktop_app/docs/v3_リリース手順.md` を参照。
deploy.sh の動作・ビルドキャッシュの罠・blue/green の正規フローを記載。
