#!/usr/bin/env python3
"""
旧環境（SQLite）の board.db を新環境の PostgreSQL に流し込むスクリプト。
使い方:
  SQLITE_DB=./board.db DATABASE_URL=postgresql+psycopg2://linko_user:linko_password@127.0.0.1:5433/linko_board_system python scripts/migrate_sqlite_to_pg.py

事前に新サーバの PostgreSQL で alembic upgrade head を実行し、空のスキーマを用意しておく。
"""
import os
import sqlite3
import sys

# backend をパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main() -> None:
    sqlite_path = os.environ.get("SQLITE_DB", "board.db")
    pg_url = os.environ.get("DATABASE_URL")
    if not pg_url:
        print("DATABASE_URL を設定してください（PostgreSQL の URL）", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(sqlite_path):
        print(f"SQLite ファイルが見つかりません: {sqlite_path}", file=sys.stderr)
        sys.exit(1)

    # psycopg2.connect は postgresql:// のみ受け付ける（+psycopg2 は付けない）
    pg_url = pg_url.replace("postgresql+asyncpg", "postgresql", 1).replace("postgresql+psycopg2", "postgresql", 1)

    import psycopg2
    from psycopg2.extras import execute_batch

    conn_sqlite = sqlite3.connect(sqlite_path)
    conn_sqlite.row_factory = sqlite3.Row
    conn_pg = psycopg2.connect(pg_url)

    tables = ["users", "sticky_notes", "board_placements"]
    for table in tables:
        cur_sqlite = conn_sqlite.execute(f"SELECT * FROM {table}")
        rows = cur_sqlite.fetchall()
        if not rows:
            print(f"  {table}: 0 件")
            continue
        cols = [d[0] for d in cur_sqlite.description]
        placeholders = ", ".join(["%s"] * len(cols))
        cols_str = ", ".join(cols)
        insert_sql = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT (id) DO NOTHING"
        cur_pg = conn_pg.cursor()
        try:
            execute_batch(
                cur_pg,
                insert_sql,
                [tuple(r) for r in rows],
                page_size=500,
            )
            conn_pg.commit()
            print(f"  {table}: {len(rows)} 件")
        except Exception as e:
            conn_pg.rollback()
            print(f"  {table}: エラー - {e}", file=sys.stderr)
            raise
        finally:
            cur_pg.close()

    # シーケンスを MAX(id) に合わせる（次回 INSERT で重複しないように）
    cur_pg = conn_pg.cursor()
    for table in tables:
        try:
            cur_pg.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE((SELECT MAX(id) FROM {table}), 1))")
        except Exception:
            pass
    conn_pg.commit()
    cur_pg.close()

    conn_sqlite.close()
    conn_pg.close()
    print("完了しました。")

if __name__ == "__main__":
    main()
