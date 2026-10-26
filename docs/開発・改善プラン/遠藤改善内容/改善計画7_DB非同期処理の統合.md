# 改善計画7：DB処理の完全非同期化（コネクション枯渇問題の解消）

## 1. 現状の課題とリスク
- **該当箇所**: `board-system/backend` 内の `orchestrator.py` や `llm_settings.py`
- **現状**: FastAPIのメインAPIは非同期（`AsyncSession`）で動いていますが、AIの担当者解決や設定読み込みの際に、わざわざ `create_engine` を使って**都度「同期用のDBコネクション」を生成・破棄**しています。
- **リスク**: リクエストごとに同期プールが生成・破棄されるため、アクセス集中時（高負荷時）にDBコネクションの枯渇や重大なパフォーマンス低下（オーバーヘッド）が発生する危険性があります。

## 2. 改善方針（ベストプラクティス：完全非同期化）
「一時的な同期エンジンの都度生成」を完全に廃止し、FastAPIがリクエスト開始時に生成している `AsyncSession` をそのまま活用する「完全非同期化」へリファクタリングします。

## 3. 具体的な変更提案（Proposed Changes）

### 3.1. `orchestrator.py` の非同期リファクタリング（2重SELECTクエリの解消）
- **対象**: `_resolve_assignee_to_user_id_sync` 関数
- **変更内容**: 
  - 同期用のエンジン生成（`_sync_database_url` および `create_engine`）を完全に削除します。
  - 単に ID を返すのではなく、最初から `User` インスタンスを直接返す `_resolve_assignee_user_async(assignee_name: str, db: AsyncSession) -> User | None` へリファクタリングします。
  - **メリット**: 呼び出し元の `process_new_note_ai` 内で行われていた「ID解決後の再度の `User` 検索（2重クエリ）」を排除でき、DBアクセスを1回削減して処理を高速化します。
  - `process_new_note_ai` 内では既存の `db: AsyncSession` を引数として渡し、`asyncio.to_thread` を使わずにそのまま `await` で呼び出します。

### 3.2. `llm_settings.py` の非同期リファクタリングとフォールバック設計
- **対象**: `get_db_llm_target_sync` / `get_resolved_ollama_sync` 関数
- **現状の課題**: `client.py`（`run_triage`, `run_matrix_scoring`）等の内部で、AI通信を行う直前に同期エンジンを作って `system_settings` テーブルを直接参照しています。
- **変更内容**:
  - `llm_settings.py` に `get_db_llm_target_async(db: AsyncSession)` を新設し、非同期で安全に設定を取得できるようにします。
  - ルーター層や `orchestrator.py` 側で事前取得した設定値（LLMターゲット・URL等）を AI 処理関数へオプショナル引数として渡す設計にします。
  - **フォールバック設計**: `client.py` などの引数が省略された場合は、環境変数（`settings`）からフォールバック解決するようにし、他のルーター（`brainstorm.py`, `news.py`）や `main.py`（起動時ログ）等への影響を最小限に抑えます。

### 3.3. セッション管理とエラーハンドリング
- `orchestrator.py` は呼び出し元から受け取った `AsyncSession` で動作するため、AI通信失敗等の例外発生時に親セッションが汚染されないよう、適切な try-except 境界および `db.flush()` / ロールバックの管理を徹底します。

## 4. 検証計画（Verification Plan）
- **機能・回帰検証**: 
  - タスクボードから付箋を作成し、AIによる「担当者の自動アサイン（敬称除去・完全一致・部分一致の検索ロジック含む）」と「マトリクス自動配置（Ollama呼び出し）」が正常に機能することを確認。
- **パフォーマンス・接続検証**: 
  - バックエンドのログ等を確認し、付箋作成時に `create_engine` による不要な同期接続ログが発生しないこと。
  - 2重クエリの解消によりDBアクセスコストが削減されていることを確認。