# 改善計画4_OAuthトークン暗号化保存（確定版）

バックエンド（FastAPI / SQLAlchemy）において、現状平文でデータベースに保存されているGoogle CalendarのOAuthトークン（`access_token` および `refresh_token`）を、`SQLAlchemy-Utils` を用いて暗号化して保存・透過的に復号するセキュアな設計へと変更します。

Pydantic Settings との整合性、Docker環境変数形式の統一、復号エラー時の安全なフォールバック処理、およびテスト計画を含めた最終確定版の実装計画です。

---

## 既存処理の確認結果と課題

1. **トークン保存のリスク**
   * 既存の `user_google_tokens` テーブルでは、`access_token` と `refresh_token` が `Text` 型の平文で保存されています。
   * 万が一DBダンプやバックアップが漏洩した際、ユーザーのGoogleカレンダーへのアクセス権限が流出する重大なセキュリティリスクが存在します。

2. **暗号化手法および設定管理**
   * `SQLAlchemy-Utils` の `StringEncryptedType` を採用し、`cryptography` の `AesEngine` を利用して透過的にAES暗号化/復号を行います。
   * 暗号化キーは `app/config.py`（Pydantic Settings）経由で一元管理し、バイト数（32バイト＝AES-256）のバリデーションを適用します。

---

## Proposed Changes

### バックエンド (FastAPI / SQLAlchemy)

#### 1. [MODIFY] [requirements.txt](file:///c:/Users/yuuya/Documents/dev/wl-board-pj/board-system/backend/requirements.txt)
* 暗号化に必要なライブラリを追加します。
  * `sqlalchemy-utils>=0.41.1`
  * `cryptography>=41.0.0`

#### 2. [MODIFY] [app/config.py](file:///c:/Users/yuuya/Documents/dev/wl-board-pj/board-system/backend/app/config.py)
* `Settings` クラスに `token_encryption_key` フィールドを追加します。
* Pydantic V2 に準拠した `@classmethod` および 32バイト（UTF-8エンコード後）チェックのバリデータ (`@field_validator`) を実装します。

#### 3. [MODIFY] [.env.example](file:///c:/Users/yuuya/Documents/dev/wl-board-pj/board-system/backend/.env.example)
* 暗号化キーの定義例を追加します。
  ```env
  TOKEN_ENCRYPTION_KEY=YourSuperSecretKeyMustBe32Bytes!
  ```

#### 4. [MODIFY] [docker-compose.yml / staging / prod](file:///c:/Users/yuuya/Documents/dev/wl-board-pj/board-system/docker-compose.yml)
* 既存の `docker-compose.yml` の記述スタイル（Key: Value の辞書形式）に合わせて `TOKEN_ENCRYPTION_KEY` を追加します。

#### 5. [MODIFY] [user_google_token.py (model)](file:///c:/Users/yuuya/Documents/dev/wl-board-pj/board-system/backend/app/models/user_google_token.py)
* `access_token` および `refresh_token` を `StringEncryptedType` に変更します。
* 暗号化キーには `lambda: settings.token_encryption_key` を指定し、遅延評価に対応します。

#### 6. [MODIFY] カレンダー取得・同期サービスの復号エラー対策
* トークン復号時にキー不一致やデータ破損で例外（`ValueError`, `PaddingException` 等）が発生した場合に、サービスがクラッシュしないよう catch 処理（フォールバック）を組み込みます。

---

## 修正コード・コピペ用ガイド

### 1. `backend/app/config.py` の修正
`Settings` クラスに `token_encryption_key` とバイト数バリデータ（Pydantic V2対応）を追加します。

```python
# app/config.py (追加箇所)
from pydantic import field_validator

class Settings(BaseSettings):
    # ... 既存の設定 ...

    # OAuthトークン暗号化キー (AES-256用に32バイト推奨)
    token_encryption_key: str = "default-insecure-key-32-bytes-long!"

    @field_validator("token_encryption_key")
    @classmethod
    def validate_encryption_key_length(cls, v: str) -> str:
        key_bytes = v.encode("utf-8")
        if len(key_bytes) < 32:
            # 32バイト未満の場合はパディング（本番環境では32バイト以上の設定を推奨）
            v = v.ljust(32, "0")
        return v[:32]
```

### 2. `backend/app/models/user_google_token.py` の修正
モデルを `StringEncryptedType` を使う構成に全面差し替えします。

```python
# -*- coding: utf-8 -*-
"""user_google_tokens テーブル。ユーザーごとの Google カレンダー OAuth トークン。"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils import StringEncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine

from app.config import settings
from app.db import Base


class UserGoogleToken(Base):
    """ユーザーに紐づく Google OAuth トークン（カレンダー取得用・暗号化保存）。"""

    __tablename__ = "user_google_tokens"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )

    # データベース上は平文ではなくAES暗号化された文字列として保存されます
    access_token: Mapped[str] = mapped_column(
        StringEncryptedType(
            Text,
            lambda: settings.token_encryption_key,
            AesEngine,
            "pkcs5",
        ),
        nullable=False,
    )

    refresh_token: Mapped[str | None] = mapped_column(
        StringEncryptedType(
            Text,
            lambda: settings.token_encryption_key,
            AesEngine,
            "pkcs5",
        ),
        nullable=True,
    )

    token_expiry: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

### 3. `docker-compose.yml` の修正
`backend` サービスの `environment`（辞書形式）に追加します。

```yaml
  backend:
    environment:
      DATABASE_URL: postgresql+asyncpg://linko_user:linko_password@db:5432/linko_board_system
      TOKEN_ENCRYPTION_KEY: ${TOKEN_ENCRYPTION_KEY:-default-insecure-key-32-bytes-long!}
```

### 4. カレンダー取得時のフォールバック処理例 (`auth_google.py` 等)
復号エラーが発生した際に例外をハンドリングし、システムダウンを防ぎます。

```python
# カレンダー取得処理のイメージ
try:
    token_row = await db.scalar(select(UserGoogleToken).where(UserGoogleToken.user_id == user_id))
    if not token_row:
        return []
    access_token = token_row.access_token # このプロパティ参照時に復号が行われる
except Exception as e:
    logger.warning(f"[OAuth] トークンの復号に失敗しました (User: {user_id}): {e}")
    # 復号不能な古い/壊れたトークンは安全のため削除し、再連携を促す
    await db.delete(token_row)
    await db.commit()
    return []
```

---

## User Review Required / 運用手順

> [!IMPORTANT]
> **デプロイ時の既存データクリア処理**
> 既存DBに平文で保存されたトークンが残っている場合、復号時にエラー（上記フォールバックにより安全に削除されます）となります。確実な運用のために、本修正を本番・ステージング環境へ適用する直前に、以下のSQLを本番DB（PostgreSQL）で実行することを推奨します。
> ```sql
> TRUNCATE TABLE user_google_tokens;
> ```
> （※ 影響: 連携済みユーザーは次回カレンダー参照時に一度だけGoogleログイン再連携が必要になります）

---

## Verification Plan

### Automated Tests
1. `tests/test_google_token_encryption.py` を作成し、以下を自動検証する。
   - `UserGoogleToken` 保存時にDB生のクエリ値が暗号化文字列（AesEngineによるエンコード列）になっていること。
   - ORM経由で取得した際に正しい平文トークンへ復号されること。

### Manual Verification
1. `.env` に `TOKEN_ENCRYPTION_KEY` を設定してバックエンドを起動。
2. Web画面より Google OAuth 連携を実施。
3. `docker exec -it linko-db psql -U linko_user -d linko_board_system -c "SELECT user_id, access_token FROM user_google_tokens;"` を実行し、平文ではなく暗号化されたバイト/文字列で保存されていることを確認。
4. パーソナルボードの「今日の予定」で正常にGoogleカレンダーのイベントが取得・表示されることを確認。
