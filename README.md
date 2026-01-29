# 02_Projects

浅川研究室のプロジェクト群です。

## 構成

| ディレクトリ / ファイル | 説明 |
|------------------------|------|
| **02_1_App_postit_board** | Webアプリ（Next.js + Express + Socket.IO）ポート3000 |
| **02_2_AI-Board** | AI-Board（Flask + Socket.IO）ポート5000 |
| **docs** | 共通ドキュメント |
| **start_all_servers.ps1** | 両サーバーを一括起動するスクリプト（推奨） |
| **check_ports.ps1** | ポート使用状況の確認 |
| **サーバー起動手順.md** | サーバー起動の詳細手順 |

## クイックスタート

両方のサーバーを起動する場合（`02_Projects` で実行）：

```powershell
.\start_all_servers.ps1
```

詳細は [サーバー起動手順.md](./サーバー起動手順.md) を参照してください。

## 各プロジェクトのREADME

- [02_1_App_postit_board](02_1_App_postit_board/src/README.md) — Webアプリ
- [02_2_AI-Board](02_2_AI-Board/README.md) — AI-Board
