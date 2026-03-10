# -*- coding: utf-8 -*-
"""
朝会用ニュース取得・要約。はてなブックマーク RSS から取得し、Ollama でリン子キャラの要約を生成。
"""
import logging
from typing import Any

import feedparser

from app.ai.client import generate_text
from app.config import settings

logger = logging.getLogger(__name__)

RSS_IT = "https://b.hatena.ne.jp/hotentry/it.rss"
RSS_FUN = "https://b.hatena.ne.jp/hotentry/fun.rss"
TOP_N = 3

NEWS_PROMPT_TEMPLATE = """あなたは明るくて優秀なアシスタント「リン子」です。
今日の朝会（Meeting）のために、以下のニュース一覧からトピックを2つ選んで紹介してください。

【条件】
1. 「💻 テック」から1つ、「🤣 おもしろ」から1つを選んでください。
2. 堅苦しくならず、「おはようございます！今日のリン子ピックアップです✨」という感じで、絵文字を使って楽しくまとめてください。
3. 選んだニュースの最後には、必ずMarkdown形式でリンクを貼ってください。
   出力例： [👉 記事を詳しく読む](URLをそのまま入れる)

【今日のニュース一覧】
{news_text}
"""


def _format_entry(entry: Any, tag: str) -> str:
    title = getattr(entry, "title", "") or ""
    link = getattr(entry, "link", "") or ""
    summary = getattr(entry, "summary", "") or ""
    if len(summary) > 200:
        summary = summary[:200] + "..."
    return f"{tag} {title}\n  URL: {link}\n  概要: {summary}\n"


def fetch_rss_text() -> str:
    """
    テック・おもしろ RSS からそれぞれ上位 TOP_N 件を取得し、
    ジャンルタグと URL 付きの1つのテキストにフォーマットして返す。
    """
    lines = []
    for url, tag in [(RSS_IT, "[💻 テック]"), (RSS_FUN, "[🤣 おもしろ]")]:
        try:
            parsed = feedparser.parse(url)
            entries = getattr(parsed, "entries", [])[:TOP_N]
            for e in entries:
                lines.append(_format_entry(e, tag))
        except Exception as e:
            logger.error("RSS 取得失敗 %s: %s", url, e)
    return "\n".join(lines) if lines else ""


def fetch_and_summarize_news() -> str | None:
    """
    RSS を取得し、Ollama で要約テキスト（Markdown）を生成する。
    OLLAMA_URL 未設定時・失敗時は None。
    """
    if not settings.ollama_url:
        logger.info("ニュース要約: OLLAMA_URL が未設定のためスキップ")
        return None
    news_text = fetch_rss_text()
    if not news_text.strip():
        logger.warning("ニュース要約: 取得したニュースが空でした")
        return None
    prompt = NEWS_PROMPT_TEMPLATE.format(news_text=news_text)
    result = generate_text(prompt)
    if not result or not result.strip():
        logger.warning("ニュース要約: LLM が空の応答を返しました")
        return None
    return result.strip()
