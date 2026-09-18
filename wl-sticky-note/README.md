# wl-sticky-note（付箋ボード）

リアルタイム協調型のオンラインホワイトボード・ブレインストーミング付箋アプリです。  
Next.js 16 + Express + Socket.IO で構成され、複数人で同一ボード上で付箋の作成・移動・編集をリアルタイムに同期します。また、Board System やデスクトップ常駐アプリとの連携 API を提供します。

- **ディレクトリ名**: `wl-sticky-note`
- **本番サーバ**: `wlboardsys-app-01` (IP: `172.16.1.203` / `https://wlboardsys.internal.wonder-link.com`)
- **本番メインボード**: <https://wlboardsys.internal.wonder-link.com/board/wl>（ボードID: `wl`）

---

## 主な機能と操作体系（UI/UX高度化対応）

### 1. 付箋の基本操作

- **作成・編集・削除**: ダブルクリックまたは入力バーから即時作成。9色のカラーパレット、ピン留め、グループ化。
- **ドラッグ描画の高速化（課題5対応）**: React のステート再レンダリングを回避し、`useRef` を用いた直接 DOM 操作（`transform`）により付箋を滑らかに移動。ドラッグ終了時にサーバーへ到達座標を一括送信。

### 2. キャンバスの直感的なナビゲーション（改善計画11・12）

- **Google Map風のパン移動**:
  - `Space キー ＋ マウス左ドラッグ` または `マウス中ボタンドラッグ` でキャンバス全体を掴んで自由にスクロール。
- **カーソル中心のスムーズなホイールズーム**:
  - マウスホイール（トラックパッド）操作により、マウスポインターを中心として 0.3倍 〜 2.5倍 まで滑らかに拡大・縮小。
- **矩形ドラッグによる複数付箋選択（Selection Box）**:
  - キャンバスの空き領域をドラッグして半透明の選択枠を表示し、枠内の付箋を一括選択。
  - `Shift キー` 併用で選択の追加／解除が可能。
  - **Esc キー** を押すと、すべての選択状態を瞬時に全解除。
- **複数付箋の一括移動**:
  - 選択中の複数付箋をまとめてドラッグ移動（ピン留め付箋は自動除外、100ms スロットル通信で負荷を抑制）。
- **グレー付箋の非表示切替（👁️/🙈）**:
  - ツールバーの目のアイコンをクリックすると、完了済み等のグレー付箋を一括で非表示にし、思考キャンバスを整理。

---

## 開発環境とクイックスタート

### 必要な環境

- Node.js 20.x LTS 以上
- npm 9.x 以上

### ローカル起動

ソースコードは `src/` 配下にあります。

```bash
cd wl-sticky-note/src
npm install
cp .env.example .env
npm run dev
```

起動後、ブラウザで **<http://localhost:3000/board/wl>** にアクセスしてください。

---

## 提供 API（他システム連携用 REST エンドポイント）

| メソッド | パス | 説明 |
| :--- | :--- | :--- |
| **GET** | `/api/health` | 死活監視エンドポイント |
| **GET** | `/api/boards/:id/summary` | ボードのサマリー（付箋総数・最終更新日時）。デスクトップアプリの新着監視用 |
| **GET** | `/api/boards/:id/notes` | ボード内の全付箋一覧取得（`dueDate: n.dueDate ?? null` を含む正規化データ） |
| **PATCH** | `/api/boards/:id/notes/:noteId` | 個別付箋のプロパティ更新（期限日 `dueDate`、グレーアウト `gray`、パーソナル専用フラグ `is_personal_only` 等） |
| **DELETE** | `/api/boards/:id/notes/:noteId` | 個別付箋の削除（Board System 側のタスク削除時にも呼び出される） |
| **POST** | `/api/sticky_notes` | 付箋の新規追加・外部連携登録（デスクトップのミニポート投稿等） |
| **POST** | `/api/boards/:id/clear` | 指定ボード内の付箋・描画線を全クリア |

---

## 環境変数

`src/.env` に設定します（`src/.env.example` 参照）。

| 変数名 | 説明 | 既定値・例 |
| :--- | :--- | :--- |
| `PORT` | サーバー起動ポート | `3000` |
| `DATA_DIR` | ボードデータ（`boards.json`）の保存先ディレクトリ | 本番 Docker: `/app/data`、ローカル: `__dirname` |
| `BOARD_SYSTEM_API_URL` | Board System API のベース URL | `http://127.0.0.1:8000` |
| `NEXT_PUBLIC_BOARD_SYSTEM_URL` | ツールバー（📋）リンク先の Board System URL | `https://wlboardsys.internal.wonder-link.com/boards` |
| `AI_BOARD_URL` | AI-Board の URL（付箋連携用） | `http://127.0.0.1:5000` |

---

## 本番デプロイと永続化（Docker Blue/Green）

本番環境では `board-system` と統合管理されています。

- **データ永続化**: Docker 共通ボリューム `sticky_note_data` に `boards.json` を保存。
- **自動バックアップ**: `deploy.sh` 実行時に、既存コンテナの `boards.json` をサイズガード付きで `backups/sticky-note/` 配下へ自動バックアップ（最新30世代を保持）。
- **静的アセット同期（改善計画21）**: デプロイ時にホストOSの `/var/www/wlinko-pj/shared_static/sticky-note` へ同期され、Nginx が直接配信します。

詳細手順: [docs/本番デプロイ手順_Docker.md](../docs/本番デプロイ手順_Docker.md)
