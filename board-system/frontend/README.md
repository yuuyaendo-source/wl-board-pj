# Board System Frontend (Wonder Linko)

Next.js 16 (App Router) + Tailwind CSS v4 + Framer Motion による統合ボードシステムのフロントエンド。  
本番環境では basePath `/boards` でビルドされ、同一サーバ上の付箋ボード（`wl-sticky-note`）と Nginx でシームレスに共存します。

---

## セットアップ

> [!WARNING]
> **必ず `frontend` ディレクトリ内で `npm` を実行してください。**  
> 親の `board-system` ディレクトリで実行すると、Tailwind CSS や Next.js の依存解決に失敗する原因になります。

```bash
cd board-system/frontend
npm install
cp .env.local.example .env.local
npm run dev -- -p 3001
```

- フロントエンドURL: <http://localhost:3001>（付箋ボード併用時）または <http://localhost:3000>
- **バックエンドが起動している必要があります。** 先に `board-system/backend` で FastAPI（ポート 8000）を起動してください。
- ルート URL（`/`）にアクセスすると、自動的にタスクボード（`/taskboard`）へリダイレクトされます。

---

## ボード画面仕様

| パス | 画面名 | 仕様・機能 |
| :--- | :--- | :--- |
| `/taskboard` | **Task Board（5列）** | **タスク管理の中核**。左から「アイデア」「短期タスク」「長期タスク」「重要」「完了」。付箋の色で状態を可視化（黄: 未引き取り、緑: 引き取り中、灰: 完了）。引き取り者の短縮名表示。**期限バッジ（DueDateBadge）表示**。付箋ボードからのワンクリック取り込み。チームドロップによるメンバー全員への一括コピー。 |
| `/personal/:id` | **Personal Board** | **個人作業用3レーン**（Today / タスク / Done）。1行入力での新規投稿（`is_personal_only` フラグが付与され、AIによるタスク化をスキップ）。Google カレンダー「今日の予定」連携。付箋色（緑: タスクボード由来、青: パーソナル独自、灰: Done）。タスクリリースボタン（タスクボードへ戻す）。安全なゴミ箱（タスク由来は配置のみ削除、独自付箋は完全削除）。 |
| `/meeting` | **Meeting ボード** | **朝会用スナップショット**。毎朝 10:15 に全社員の Personal Today を MORNING レーンへ同期。参加者別リストに期限バッジ・期限警告枠線を表示。日次ニュース要約付箋の反映。「今の Today を反映」手動テスト機能。 |
| `/main` | **Main Board** | **全体構想用フリーキャンバス**。ドラッグ＆ドロップによる自由配置。1行投稿で作成された付箋は AI Worker により自動仕分け（AI判定付箋には ✨ マーク付与）。 |
| `/admin/system` | **システム管理** | LLM スロット切替（社内 Ollama 1〜3 の指定）などのバックエンド設定変更 UI（要管理者認証）。 |

※ 本番ビルド時は basePath `/boards` が付与されるため、実際の URL は `/boards/taskboard`、`/boards/personal/:id`、`/boards/meeting`、`/boards/main` となります。

---

## 主要 UI コンポーネント & 新機能

### 1. メンバー・チーム管理モーダル
ヘッダーの「メンバー管理」ボタンから開く 2 タブ形式ダイアログ:
- **メンバー管理タブ**: ユーザーの追加・編集・削除。**複数チームへの所属**（チェックボックス選択）に対応し、ユーザー一覧ではチームごとに色分けされたバッジが表示されます。
- **チーム管理タブ**: チームの新規作成・チーム名変更・チーム削除（削除時は所属メンバーの紐付けを安全に解除）。
- **管理者認証モーダル連携**: ユーザーやチームの削除、LLM切替などの破壊的操作を行う際、自動的に管理者認証モーダル（パスワード入力）が表示され、認証後に操作が継続されます（トークンは `sessionStorage` で安全に保持）。

### 2. 期限バッジ共通コンポーネント (`DueDateBadge`)
Taskボード、Personalボード、Meetingボードで共通の期限判定・デザイン表示を提供:
- **判定ロジック**: JST基準で当日との差分を計算。
- **バッジ表示**:
  - 期限切れ: `⚠️ 期限切れ (X日経過)`（赤バッジ）
  - 本日期限: `🔥 本期日が期限！`（オレンジバッジ）
  - 直前: `⏰ 期限まであとX日`（黄バッジ）
  - 先: `📅 あとX日`（青バッジ）
- **カード枠線強調**: 期限切れ・本日期限のカードには自動的に赤枠やオレンジ枠のスタイルを適用。

### 3. 直感的な D&D 操作
- Task ボードの 5 列移動
- Personal ボードのレーン間移動（Done にすると Task 側も「完了」に連動）
- ゴミ箱ドロップ（タスク由来か独自付箋かを自動判定し、不整合やタスクの勝手な復活を防止）
- メンバーアイコン・チームアイコンへのドロップ（個人への譲渡・チーム全員への一括コピー）

---

## 環境変数

`frontend/.env.local` に設定します。

| 変数名 | 説明 | 開発時 | 本番時 |
| :--- | :--- | :--- | :--- |
| `NEXT_PUBLIC_API_URL` | バックエンド API のベース URL | `http://localhost:8000` | `https://wlboardsys.internal.wonder-link.com/api/bs` |
| `NEXT_PUBLIC_LEGACY_BOARD_URL` | 付箋ボードのベース URL（タスク取り込み用） | `http://localhost:3000` | `https://wlboardsys.internal.wonder-link.com` |
| `NEXT_PUBLIC_BASE_PATH` | 本番の basePath 指定（未指定時は production で `/boards`） | `""` | `/boards` |

---

## 技術スタック

- **Framework**: Next.js 16 (App Router)
- **UI & Styling**: React 19, Tailwind CSS v4
- **Animation**: Framer Motion
- **Drag & Drop**: Native HTML5 Drag and Drop API
