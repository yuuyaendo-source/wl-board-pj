# Wonder Linko デスクトップアプリ 自動更新用リリース置き場

このフォルダに **MSI ファイル** と **latest.json** を配置すると、デスクトップアプリの自動更新が利用できます。

## 配置するファイル

| ファイル | 説明 |
|----------|------|
| `latest.json` | 最新バージョン情報。`version` と MSI のダウンロード `url` を記載。 |
| `WonderLinko.msi` | wl_desktop_app でビルドした MSI（`.\build_msi.ps1` で生成）。**このフォルダにコピーする。** |

## latest.json の形式

```json
{
  "version": "2.0.0",
  "url": "https://wl-ai-board.internal.wonder-link.co.jp/api/bs/desktop-app/WonderLinko.msi"
}
```

- **version**: 最新のバージョン番号（wl_desktop_app の `version.py` と一致させる）。
- **url**: 上記 MSI に**クライアントがアクセスするときの絶対 URL**。  
  本番では `https://<あなたのドメイン>/api/bs/desktop-app/WonderLinko.msi` のように、Board System の API ベース URL + `/desktop-app/WonderLinko.msi` にすること。

## アップロード手順（新バージョンリリース時）

1. **wl_desktop_app** で `version.py` の `__version__` を上げる（例: `2.0.0` → `2.0.1`）。
2. `.\build_msi.ps1` で `dist\WonderLinko.msi` をビルドする。
3. このフォルダに **WonderLinko.msi** をコピーする（上書きでよい）。
4. **latest.json** の `version` を同じ番号にし、`url` を実際の公開 URL に合わせて保存する。
5. デプロイ後、クライアントの `config.json` の `update_check_url` を  
   `https://<ドメイン>/api/bs/desktop-app/latest.json` にしておくと、トレイの「更新を確認」や起動時チェックで取得される。

## クライアント側の設定

デスクトップアプリの `config.json` に次を設定する。

```json
"update_check_url": "https://wl-ai-board.internal.wonder-link.co.jp/api/bs/desktop-app/latest.json"
```

※ 本番の Board System の API ベース URL に合わせて変更してください。
