# -*- coding: utf-8 -*-
"""
初期チームデータ投入スクリプト。
SEED_TEAMS ("ネットワーク", "構築") を作成し、初期ユーザー (1-8) にチームを割り当てる。
"""
import asyncio
import os
import sys

# app モジュールをインポートできるようにパス追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import seed_teams


def main() -> None:
    asyncio.run(seed_teams())


if __name__ == "__main__":
    main()
