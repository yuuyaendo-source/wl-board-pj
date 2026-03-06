-- placement_source カラム追加（h8c9d0e1f2a3 相当）
-- 本番で alembic upgrade head が実行されていない場合、この SQL を DB に流してください。
ALTER TABLE board_placements
ADD COLUMN IF NOT EXISTS placement_source VARCHAR(32) NULL;
