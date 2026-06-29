# -*- coding: utf-8 -*-
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from network_readiness import resolve_probe_url, unreachable_backoff_sec  # noqa: E402


def test_resolve_probe_url_prefers_explicit():
    cfg = {
        "update_network_check_url": "https://example.internal/probe",
        "update_check_url": "https://example.internal/latest.json",
    }
    assert resolve_probe_url(cfg) == "https://example.internal/probe"


def test_resolve_probe_url_uses_update_check_url():
    cfg = {"update_check_url": "https://example.internal/latest.json"}
    assert resolve_probe_url(cfg) == "https://example.internal/latest.json"


def test_resolve_probe_url_board_health():
    cfg = {"board_system_url": "https://example.internal/api/bs"}
    assert resolve_probe_url(cfg) == "https://example.internal/api/bs/health"


def test_unreachable_backoff_default():
    assert unreachable_backoff_sec({}) == 30


if __name__ == "__main__":
    test_resolve_probe_url_prefers_explicit()
    test_resolve_probe_url_uses_update_check_url()
    test_resolve_probe_url_board_health()
    test_unreachable_backoff_default()
    print("test_network_readiness: OK")
