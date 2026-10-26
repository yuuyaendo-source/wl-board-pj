# Wonder Linko デスクトップアプリ 自動更新用リリース置き場

このディレクトリの **`WonderLinko.msi`**（または `WonderLinko_<version>.msi`）と **`latest.json`** を更新すると、クライアントPCに常駐するデスクトップアプリの自動更新が有効になります[cite: 1]。

---

## 配置ファイル

| ファイル名 | 役割 |
| :--- | :--- |
| `latest.json` | 最新バージョン情報（`version` と MSI 取得先の絶対 `url`）[cite: 1] |
| `WonderLinko.msi` / `WonderLinko_<version>.msi` | `wl_desktop_app` でビルドされた Windows インストーラ（自己署名コード署名済み）[cite: 1] |

---

## `latest.json` 形式

```json
{
  "version": "3.9.8",
  "url": "[https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi](https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi)"
}
```

- `version`: `wl_desktop_app/version.py` の `__version__` と完全に一致させること[cite: 1]。
- `url`: クライアントが MSI をダウンロードする **絶対 URL**。※ サーバ上のファイル名と完全に一致させること[cite: 1]。

---

## 反映方法（bind mount による即時反映）

`docker-compose.prod.yml` において、本ディレクトリが backend コンテナの `/app/desktop_app_releases` に **bind mount** されています[cite: 1]。

```yaml
# docker-compose.prod.yml backend.volumes
- ./backend/desktop_app_releases:/app/desktop_app_releases
```

FastAPI の `StaticFiles` はリクエストごとにホストOSのディレクトリを直接参照するため、**ホスト側のファイルを差し替えるだけで、コンテナの再起動や `deploy.sh` の実行なしに即時反映** されます[cite: 1]。

---

## リリース・アップロード手順（新バージョン公開時）

### 1. バージョン番号の更新

- `wl_desktop_app/version.py` の `__version__` を更新（例: `3.9.8`）[cite: 1]。
- 本ディレクトリの `latest.json` の `version` と `url` を同じバージョン番号に書き換え[cite: 1]。
- Git コミット & プッシュ[cite: 1]。

### 2. Windows ビルド PC での MSI ビルド

```powershell
cd wl-board-pj\wl_desktop_app
# 初回のみ: .\scripts\generate_cert.ps1 で署名証明書を発行し、.env に CERT_PASSWORD を設定
.\build_msi.ps1     # → dist\WonderLinko.msi (自己署名コード署名済み)
```

### 3. 本番サーバへ MSI を転送 (scp)

ロールバック管理のため、バージョン付きファイル名でアップロードします[cite: 1]。

```powershell
scp dist\WonderLinko.msi devuser01@172.16.1.203:/var/www/wlinko-pj/board-system/backend/desktop_app_releases/WonderLinko_3.9.8.msi
```

### 4. 本番サーバでの反映 (git pull)

```bash
ssh devuser01@172.16.1.203
cd /var/www/wlinko-pj
git pull
```

※ `latest.json` が git pull で更新され、bind mount により即時配信されます（`deploy.sh` 不要）[cite: 1]。

### 5. 配信確認

```bash
# JSON が最新バージョンを返しているか
curl [https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/latest.json](https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/latest.json)

# MSI が 200 OK でダウンロード可能か
curl -sI [https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi](https://wlboardsys.internal.wonder-link.com/api/bs/desktop-app/WonderLinko_3.9.8.msi) | head -n 3
```
