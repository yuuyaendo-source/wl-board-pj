# Self-Healing 同期照合バッチ（sync_reconciliation）本番切替運用手順書

本ドキュメントは、改善計画23で導入された **Board System (PostgreSQL)** と **付箋ボード (wl-sticky-note / boards.json)** 間の差分照合バッチ (`app/services/sync_reconciliation.py`) について、安全評価を経て `dry_run=True`（ログ採取のみ）から `dry_run=False`（自動データ修復モード）へ切り替えるための基準と手順を定めたものです。

---

## 1. 概要と Source of Truth 規則

本バッチは、毎朝 8:00 の定期処理（`POST /daily_reset/run_8am`）および手動トリガー時に呼び出され、以下の整合性ルールに基づいて不整合を検知・補正します。

| データ項目 | 優先される正（Source of Truth） | 補正アクション |
| :--- | :--- | :--- |
| **付箋本文・物理的存在** | **付箋ボード (wl-sticky-note)** | 付箋ボードにある有効付箋が DB になければ作成。本文が違えば DB を更新。 |
| **タスク状態・完了・期限** | **Board System (PostgreSQL)** | DB で完了・削除された付箋が付箋ボード側で生きていれば、付箋側をグレー化。 |

> [!WARNING]
> **ゾンビ復活防止ガード**:
> 付箋ボード側で既に「グレー（完了・アーカイブ）」になっている付箋は、DB 側に存在しなくても新規タスクとして再作成されません。

---

## 2. 本番有効化の判定基準（切替前チェックリスト）

本番の環境変数 `RECONCILIATION_DRY_RUN` を `false` に切り替える前に、**最低 7 日間（推奨 14 日間）** のログを監視し、以下の条件をすべて満たしていることを確認してください。

- [ ] **エラー件数ゼロ**: ログ内の `errors` 配列が直近 7 日間連続して `[]`（空）であること（通信障害やタイムアウトがないこと）。
- [ ] **差分検出の定常収束**: 日常運用において `created_in_db` および `archived_in_remote` の検出件数が定常的に **0 件**（または手動操作ミスによる正当な差分のみ）に収束していること。
- [ ] **パーソナル専用付箋の隔離確認**: 個人専用メモ（`is_personal_only=True`）がタスクボード側に誤って生成されるログが 1 件も存在しないこと。
- [ ] **最新バックアップの存在**: `board-system/backups/sticky-note/` 配下に有効な `boards_*.json`（100バイト超）が自動保存されていること。

---

## 3. 切替作業手順

### Step 1: 手動 Dry-run による最終安全確認

本番サーバーへ SSH 接続し、手動で Dry-run を実行して現在の差分統計を取得します。

```bash
ssh devuser01@172.16.1.203
curl -s -X POST "[https://wlboardsys.internal.wonder-link.com/api/bs/daily_reset/reconcile?dry_run=true](https://wlboardsys.internal.wonder-link.com/api/bs/daily_reset/reconcile?dry_run=true)" | jq .
