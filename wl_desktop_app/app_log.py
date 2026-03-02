# -*- coding: utf-8 -*-
"""
アプリログ: ファイルへの出力と直近50行のバッファ。
トレイメニュー「最新ログを表示」で直近50行を表示できる。
"""
import logging
import os
from collections import deque
from datetime import datetime


_BUFFER_MAXLEN = 50
_buffer: deque = deque(maxlen=_BUFFER_MAXLEN)
_logger: logging.Logger | None = None


class BufferHandler(logging.Handler):
    """直近 N 件のログをメモリに保持するハンドラ。"""

    def __init__(self, buffer: deque):
        super().__init__()
        self._buffer = buffer

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self._buffer.append(msg)
        except Exception:
            self.handleError(record)


def setup_app_log() -> logging.Logger:
    """ログを初期化し、ファイルとバッファに出力する Logger を返す。起動時に1回呼ぶ。"""
    global _logger
    if _logger is not None:
        return _logger

    from config_loader import get_app_base_dir
    base_dir = get_app_base_dir()
    log_path = os.path.join(base_dir, "WonderLinko.log")

    logger = logging.getLogger("WonderLinko")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ファイル（追記）
    try:
        fh = logging.FileHandler(log_path, encoding="utf-8", mode="a")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        pass

    # 直近50行バッファ
    bh = BufferHandler(_buffer)
    bh.setLevel(logging.DEBUG)
    bh.setFormatter(fmt)
    logger.addHandler(bh)

    _logger = logger
    logger.info("Wonder Linko ログ開始")
    return logger


def get_recent_log_lines() -> list[str]:
    """直近のログ行を最大50行、古い順で返す。"""
    return list(_buffer)


def get_log_file_path() -> str:
    """ログファイルの絶対パスを返す。"""
    from config_loader import get_app_base_dir
    return os.path.join(get_app_base_dir(), "WonderLinko.log")
