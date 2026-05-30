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

## 反映方法 (v3.2.3 以降: bind mount 化)

docker-compose.prod.yml で このフォルダを backend コンテナに **bind mount**
しているため、**ホスト側のファイルを差し替えるだけで即反映** されます
(backend 再ビルド・deploy.sh 不要)。

```yaml
# docker-compose.prod.yml backend.volumes
- ./backend/desktop_app_releases:/app/desktop_app_releases
```

FastAPI の StaticFiles はリクエストごとにディスクを読むため、
`latest.json` / `*.msi` を置けばコンテナ再起動すら不要です。

⚠️ **初回のみ**: この bind mount を有効化するには 1 度だけ `./deploy/deploy.sh`
(または `docker compose ... up -d`) で compose 変更を反映する必要があります。
以降は git pull / scp だけで反映されます。

### 旧仕様 (参考・v3.2.2 以前)

bind mount 前は backend Dockerfile の `COPY . .` でイメージに焼き込んでいたため、
ファイル差し替え後に deploy.sh で再ビルドが必須でした。「git pull / deploy.sh
忘れで古い latest.json が配信され続ける」事故が頻発したため bind mount 化。

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

4. **本番サーバで反映** (bind mount 化後)
   ```bash
   ssh devuser01@wl-board-sys-sv
   cd /var/www/wlinko-pj
   git pull                        # latest.json 更新を取得 → bind mount で即反映
   # deploy.sh は不要 (frontend/backend のコード変更時のみ)
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
