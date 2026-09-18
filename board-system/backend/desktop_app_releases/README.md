# Wonder Linko デスクトップアプリ 自動更新用リリース置き場

このディレクトリの **`WonderLinko.msi`**（または `WonderLinko_<version>.msi`）と **`latest.json`** を更新すると、クライアントPCに常駐するデスクトップアプリの自動更新が有効になります。

---

## 配置ファイル

| ファイル名 | 役割 |
| :--- | :--- |
| `latest.json` | 最新バージョン情報（`version` と MSI 取得先の絶対 `url`） |
| `WonderLinko.msi` | `wl_desktop_app` でビルドされた Windows インストーラ（`build_msi.ps1` で生成・署名） |

---

## `latest.json` 形式

```json
{
  "version": "3.9.8",
  "url": "https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi"
}
```

- `version`: `wl_desktop_app/version.py` の `__version__` と完全に一致させること。
- `url`: クライアントが MSI をダウンロードする **絶対 URL**。

---

## 反映方法（bind mount による即時反映）

`docker-compose.prod.yml` において、本ディレクトリが backend コンテナの `/app/desktop_app_releases` に **bind mount** されています。

```yaml
# docker-compose.prod.yml backend.volumes
- ./backend/desktop_app_releases:/app/desktop_app_releases
```

FastAPI の `StaticFiles` はリクエストごとにホストOSのディレクトリを直接参照するため、**ホスト側のファイルを差し替えるだけで、コンテナの再起動や `deploy.sh` の実行なしに即時反映** されます。

---

## リリース・アップロード手順（新バージョン公開時）

### 1. バージョン番号の更新

- `wl_desktop_app/version.py` の `__version__` を更新（例: `3.9.8`）。
- 本ディレクトリの `latest.json` の `version` と `url` を同じバージョン番号に書き換え。
- Git コミット & プッシュ。

### 2. Windows ビルド PC での MSI ビルド

```powershell
cd wl-board-pj\wl_desktop_app
# 初回のみ: .\scripts\generate_cert.ps1 で署名証明書を発行し、.env に CERT_PASSWORD を設定
.\build_msi.ps1     # → dist\WonderLinko.msi (自己署名コード署名済み)
```

### 3. 本番サーバへ MSI を転送 (scp)

```powershell
scp dist\WonderLinko.msi devuser01@172.16.1.203:/var/www/wlinko-pj/board-system/backend/desktop_app_releases/WonderLinko_3.9.8.msi
```

### 4. 本番サーバでの反映 (git pull)

```bash
ssh devuser01@172.16.1.203
cd /var/www/wlinko-pj
git pull
```

※ `latest.json` が git pull で更新され、bind mount により即時配信されます（deploy.sh 不要）。

### 5. 配信確認

```bash
# JSON が最新バージョンを返しているか
curl https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/latest.json

# MSI が 200 OK でダウンロード可能か
curl -sI https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi | head -n 3
```

---

## クライアント側の更新挙動

1. **起動時**: デスクトップアプリ起動時にバックグラウンドで `latest.json` を取得（新版があればログ出力）。
2. **手動確認**: トレイアイコンまたは設定ダイアログの「🔄 アップデート確認」をクリックすると、新バージョンをダウンロードし、サイレントインストール後に自動でアプリが再起動します。
