# coding=utf-8

from __future__ import annotations

import hashlib
from typing import Optional


def _compact_date(date_str: str) -> str:
    return date_str.replace("-", "")


def _compact_time(time_str: str) -> str:
    # 支持 "HH-MM" / "HH:MM" / "HHMM"
    t = time_str.strip()
    if ":" in t:
        t = t.replace(":", "")
    if "-" in t:
        t = t.replace("-", "")
    return t


def make_timestamp(date_str: str, time_str: Optional[str]) -> str:
    """
    生成 YYYYMMDDHHMMSS（秒默认为 00）
    """
    d = _compact_date(date_str)
    if not time_str:
        return f"{d}000000"
    t = _compact_time(time_str)
    if len(t) == 4:
        return f"{d}{t}00"
    if len(t) == 6:
        return f"{d}{t}"
    # 兜底：填充/截断到 4 位
    t = (t + "0000")[:4]
    return f"{d}{t}00"


def generate_news_id(platform_id: str, title: str, date_str: str, last_time: Optional[str]) -> str:
    ts = make_timestamp(date_str, last_time)
    hash_str = hashlib.md5(f"{platform_id}_{title}".encode("utf-8")).hexdigest()[:6]
    return f"{platform_id}_{ts}_{hash_str}"


def generate_rss_id(feed_id: str, title: str, published_at: str) -> str:
    hash_str = hashlib.md5(f"{feed_id}_{title}_{published_at}".encode("utf-8")).hexdigest()[:6]
    safe_pub = published_at.replace(":", "").replace("-", "").replace("T", "").replace("Z", "")
    safe_pub = safe_pub[:14] if safe_pub else "unknown"
    return f"{feed_id}_{safe_pub}_{hash_str}"

