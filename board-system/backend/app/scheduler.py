# -*- coding: utf-8 -*-
"""
日次スケジュール。日本時間（Asia/Tokyo）で 8:00 に run_8am、10:15 に sync_to_morning を実行する。
SCHEDULER_ENABLED が true（既定）のとき有効。SCHEDULER_BASE_URL で自サーバの URL を指定。
"""
import logging
from zoneinfo import ZoneInfo

from app.config import settings

logger = logging.getLogger(__name__)
_scheduler = None
JST = ZoneInfo("Asia/Tokyo")


def _post(path: str) -> None:
    """自サーバへ POST してスケジュール処理を実行。"""
    try:
        import requests
        url = f"{settings.scheduler_base_url.rstrip('/')}{path}"
        r = requests.post(url, timeout=120)
        if r.status_code != 200:
            logger.warning("スケジューラ POST %s: status=%s", url, r.status_code)
        else:
            logger.info("スケジューラ実行完了: %s", path)
    except Exception as e:
        logger.warning("スケジューラ POST 失敗 %s: %s", path, e)


def start_scheduler() -> None:
    """日本時間（JST）で 8:00 run_8am / 10:15 sync_to_morning を登録してスケジューラを開始。"""
    global _scheduler
    if _scheduler is not None:
        return
    if not settings.scheduler_enabled:
        logger.info("スケジューラは無効です（SCHEDULER_ENABLED=false）")
        return
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("APScheduler がインストールされていません。pip install apscheduler で有効にできます。")
        return

    _scheduler = BackgroundScheduler(timezone=JST)
    # 毎日 8:00 JST: Meeting リセット + 全ユーザーカレンダー取得・Today 付箋更新
    _scheduler.add_job(
        lambda: _post("/daily_reset/run_8am"),
        "cron",
        hour=8,
        minute=0,
        id="run_8am",
    )
    # 毎日 10:15 JST: Personal Today を MORNING にコピー（Meeting ボード反映）
    _scheduler.add_job(
        lambda: _post("/daily_reset/sync_to_morning"),
        "cron",
        hour=10,
        minute=15,
        id="sync_to_morning",
    )
    _scheduler.start()
    logger.info(
        "日次スケジューラ開始（日本時間 Asia/Tokyo）: 8:00 run_8am, 10:15 sync_to_morning (BASE_URL=%s)",
        settings.scheduler_base_url,
    )


def shutdown_scheduler() -> None:
    """スケジューラを停止。"""
    global _scheduler
    if _scheduler is None:
        return
    try:
        _scheduler.shutdown(wait=False)
    except Exception as e:
        logger.warning("スケジューラ停止時にエラー: %s", e)
    _scheduler = None
