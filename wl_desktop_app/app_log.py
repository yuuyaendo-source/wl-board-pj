# -*- coding: utf-8 -*-
"""
アプリログ: ファイルへの出力と直近50行のバッファ。
直近50行をメモリに保持する（デバッグ用）。
"""
import logging
import os
import threading
from collections import deque



_BUFFER_MAXLEN = 50
_buffer: deque = deque(maxlen=_BUFFER_MAXLEN)
_logger: logging.Logger | None = None
_log_path: str = ""


class BufferHandler(logging.Handler):
    """直近 N 件のログをメモリに保持するハンドラ（スレッドセーフ）。"""

    _lock = threading.Lock()

    def __init__(self, buffer: deque):
        super().__init__()
        self._buffer = buffer

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            with self._lock:
                self._buffer.append(msg)
        except Exception:
            self.handleError(record)


def _get_log_dir() -> str:
    """ログ出力先ディレクトリを返す。LOCALAPPDATA 優先、無ければホームディレクトリ配下。"""
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "WonderLink")
    try:
        os.makedirs(d, exist_ok=True)
    except Exception:
        pass
    return d


def get_log_file_path() -> str:
    """ログファイルの絶対パスを返す。"""
    return os.path.join(_get_log_dir(), "WonderLinko.log")


def setup_app_log() -> logging.Logger:
    """ログを初期化し、ファイルとバッファに出力する Logger を返す。起動時に1回呼ぶ。"""
    global _logger, _log_path
    if _logger is not None:
        return _logger

    _log_path = get_log_file_path()
    log_path = _log_path

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


def _emit(level: str, msg: str) -> None:
    from datetime import datetime
    line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [{level}] WonderLinko: {msg}"
    with BufferHandler._lock:
        _buffer.append(line)
    if _log_path:
        try:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
        except Exception:
            pass


def log_info(msg: str):
    """メッセージをログに INFO で記録する（バッファ＋ファイル）。"""
    _emit("INFO", msg)


def log_warn(msg: str):
    """メッセージをログに WARN で記録する（バッファ＋ファイル）。"""
    _emit("WARN", msg)


def log_error(msg: str):
    """メッセージをログに ERROR で記録する（バッファ＋ファイル）。"""
    _emit("ERROR", msg)


def get_recent_log_lines() -> list[str]:
    """直近のログ行を最大50行、古い順で返す。"""
    with BufferHandler._lock:
        return list(_buffer)
