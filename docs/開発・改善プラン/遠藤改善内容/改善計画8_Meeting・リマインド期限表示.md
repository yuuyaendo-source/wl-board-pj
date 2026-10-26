# 改善計画8：Meetingボードおよびデスクトップアプリのタスクリマインドへの期限表示機能追加

## 1. 概要・目的

タスク管理における視認性を高めるため、朝会等で利用する **Meetingボード (`/meeting`)** および社員PC上で常駐動作する **デスクトップアプリ (`wl_desktop_app`) のタスクリマインド機能** において、各タスクの期限（`due_date`）を表示できるように改修を行います。

---

## 2. 現状の課題

1. **Meetingボード (`board-system/frontend/app/meeting/page.tsx`)**
   - 現在のMeetingボードでは、各メンバーの「Today」タスク本文 (`note_content`) のみが黄色枠カードで表示されており、付箋に設定された期限（`due_date`）が画面上に現れません。
   - 朝会でのミーティング時に「どのタスクが本日締め切り・期限切れか」をパッと確認できない課題があります。
2. **デスクトップアプリのタスクリマインド (`wl_desktop_app/task_remind_dialog.py` 等)**
   - タスクリマインドの通知およびダイアログにおいて、タスク名（付箋本文）のみが提示されており、締め切り期日が確認できません。

---

## 3. 提案する変更内容 (Proposed Changes)

### ① バックエンド API の確認・拡張 (`board-system/backend`)

* **`app/routers/boards.py` (`get_board_morning`)**:
  - Meetingボード用API (`GET /boards/morning`) のレスポンスにおいて、既に `due_date=n.due_date.isoformat() if n.due_date else None` としてシリアライズして渡されていることを再確認し、既存コードを活かします。
- **`app/routers/task_reminders.py`**:
  - デスクトップアプリが呼び出すリマインド一覧取得API `PendingItem` スキーマに `due_date: Optional[str] = None` フィールドを追加します。
  - `_today_placements` または `get_pending_task_reminders` のループ内で、`StickyNote` の `due_date` を `PendingItem` に設定して返却します。

### ② フロントエンド MeetingボードのUI改修 (`board-system/frontend`)

* **コンポーネントとロジックの共通化**:
  - 既存の `NoteCard.tsx` 内に実装されている `calcDaysLeft`（残り日数計算）、`getDueDateBorderClass`（枠線スタイル）、`DueDateBadge`（パルスアニメーション付きバッジ）などのロジックとUIコンポーネントを、共通のファイル（例: `DueDateBadge.tsx` やユーティリティファイル）に切り出します。
* **`app/meeting/page.tsx`**:
  - 共通化したコンポーネントを活用し、各ユーザーのタスクカード表示部（`byOwner[u.id]` ループ内）で、`p.note_content` の隣または下部に期限バッジを表示します。
  - 共通コンポーネントを利用することで、TaskボードやPersonalボードと完全に統一された見た目・挙動（太い赤枠線＋赤パルスバッジ等）をMeeting画面でも維持し、期限切れや本日締め切りのタスクを視覚的に強調します。

### ③ デスクトップアプリのUI改修 (`wl_desktop_app`)

* **期限判定ロジックの実装**:
  - ダイアログ側でもバックエンド同様に `JST = ZoneInfo("Asia/Tokyo")` を用いて、JSTの当日日付（`datetime.now(JST).date()`）と比較して期限の状況（過去・当日・未来）を判定します。
* **`task_remind_client.py` & `task_remind_dialog.py`**:
  - APIからのJSONから `due_date` を受け取り、`TaskRemindListDialog` クラスの `_add_task_row` でタスク行をレンダリングする際、タイトルの横・または下部に期限を表示します。
  - CustomTkinterのラベル等を利用して、「期限: YYYY-MM-DD」や「⚠️ 期限切れ」などの警告テキスト・色味（`text_color` を赤やオレンジに指定）を付与します。
  - **表示の統一**: `frontend` の `NoteCard.tsx` 内にある `DueDateBadge` と同じ文言（「⚠️ 期限切れ（X日経過）」「🔥 本期日が期限！」「⏰ 期限まであとX日」「📅 期限: YYYY-MM-DD」）および同等のカラーコードに寄せることで、タスクボードとデスクトップアプリの体験を統一します。

---

## 4. User Review Required
>
> [!IMPORTANT]
> **色分けと強調の仕様**
> デスクトップアプリ側 (CustomTkinter) では、CSSほどリッチなアニメーション表現（赤パルス等）は難しいため、文字色とシンプルなアイコンテキスト（⚠️ や 🔥 など）での強調表示とすることを想定していますがよろしいでしょうか。

---

## 5. 検証計画 (Verification Plan)

### Automated / API Tests

* `task_reminders.py` の `GET /api/personal/{user_id}/task_reminders/pending` エンドポイントをテストし、`due_date` が正しく `YYYY-MM-DD` 形式で返却されること。

### Manual Verification

1. **Meetingボードの確認**:
   - パーソナルボードで期限（過去・今日・未来）を設定したタスクを作成・Todayへ移動する。
   - `/meeting` 画面を開き、各ユーザーのカード内で付箋本文に加えて期限バッジ（色分け・警告表記含む）が正しく表示されており、Task/Personalボードと同じデザインが適用されていることを確認する。
2. **デスクトップアプリの確認**:
   - 期限付きタスクを保持した状態でデスクトップアプリのタスクリマインドダイアログを起動し、ダイアログ上に期限表記が追加され、日付の状況に応じて警告アイコンと指定の色味が付与されていることを確認する。
