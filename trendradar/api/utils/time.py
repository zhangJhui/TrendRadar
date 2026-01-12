# coding=utf-8

from __future__ import annotations

from datetime import datetime
from typing import Optional

import pytz

from trendradar.utils.time import format_date_folder


def resolve_date(date_str: Optional[str], timezone: str) -> str:
    """解析 date，返回 YYYY-MM-DD（兼容 None）。"""
    return format_date_folder(date_str, timezone)


def to_iso_datetime(date_str: str, time_str: Optional[str], timezone: str) -> Optional[str]:
    """
    将 YYYY-MM-DD + (HH-MM/HH:MM) 转成带时区 ISO 字符串。
    """
    if not time_str:
        return None
    t = time_str.strip()
    if not t:
        return None

    fmt = "%H-%M" if "-" in t else "%H:%M" if ":" in t else None
    if fmt is None:
        return None

    try:
        naive = datetime.strptime(f"{date_str} {t}", f"%Y-%m-%d {fmt}")
        tz = pytz.timezone(timezone)
        aware = tz.localize(naive)
        return aware.isoformat()
    except Exception:
        return None


def now_iso(timezone: str) -> str:
    tz = pytz.timezone(timezone)
    return datetime.now(tz).isoformat()

