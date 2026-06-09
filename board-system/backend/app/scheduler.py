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
    # 毎日 10:00 JST: ニュース付箋のみクリア
    _scheduler.add_job(
        lambda: _post("/news/clear"),
        "cron",
        hour=10,
        minute=0,
        id="clear_news",
    )
    # 毎日 10:15 JST: Personal Today を MORNING にコピー（Meeting ボード反映）
    _scheduler.add_job(
        lambda: _post("/daily_reset/sync_to_morning"),
        "cron",
        hour=10,
        minute=15,
        id="sync_to_morning",
    )
    # 毎日 10:15 JST: ニュース取得・要約して MORNING に付箋追加
    _scheduler.add_job(
        lambda: _post("/news/fetch"),
        "cron",
        hour=10,
        minute=15,
        id="fetch_news",
    )
    cal_interval = getattr(settings, "scheduler_calendar_interval_minutes", 0)
    if cal_interval not in (None, 0):
        try:
            cal_min = int(cal_interval)
            if cal_min >= 5:
                _scheduler.add_job(
                    lambda: _post("/api/personal/calendar_sync_all"),
                    "interval",
                    minutes=cal_min,
                    id="calendar_sync_all",
                )
                logger.info("カレンダー予定の定期同期を %s 分間隔で追加", cal_min)
        except (TypeError, ValueError):
            pass
    if getattr(settings, "scheduler_news_interval_minutes", 0) not in (None, 0):
        try:
            interval_min = int(settings.scheduler_news_interval_minutes)
            if interval_min >= 1:
                _scheduler.add_job(
                    lambda: _post("/news/fetch"),
                    "interval",
                    minutes=interval_min,
                    id="fetch_news_interval",
                )
                logger.info("ニュース取得を %s 分間隔で追加（テスト用）", interval_min)
        except (TypeError, ValueError):
            pass
    _scheduler.start()
    logger.info(
        "日次スケジューラ開始（日本時間 Asia/Tokyo）: 8:00 run_8am, 10:00 clear_news, 10:15 sync_to_morning + fetch_news (BASE_URL=%s)",
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
