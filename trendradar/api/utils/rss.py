# coding=utf-8

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from trendradar.storage.base import RSSData, RSSItem
from trendradar.utils.time import is_within_days


def rss_items_dict_to_list(
    items_dict: Dict[str, List[RSSItem]],
    id_to_name: Dict[str, str],
    *,
    rss_config: Dict,
    rss_feeds_config: List[Dict],
    timezone: str,
) -> List[Dict]:
    """
    将 RSSData.items（feed_id -> [RSSItem]）转换为 count_rss_frequency 所需列表格式。
    同时复用主程序的“新鲜度过滤”逻辑（按 feed 的 max_age_days 或默认 MAX_AGE_DAYS）。
    """
    rss_items: List[Dict] = []

    freshness_cfg = rss_config.get("FRESHNESS_FILTER", {}) if rss_config else {}
    freshness_enabled = freshness_cfg.get("ENABLED", True)
    default_max_age_days = freshness_cfg.get("MAX_AGE_DAYS", 3)

    feed_max_age_map: Dict[str, int] = {}
    for feed_cfg in rss_feeds_config or []:
        feed_id = feed_cfg.get("id", "")
        max_age = feed_cfg.get("max_age_days")
        if feed_id and max_age is not None:
            try:
                feed_max_age_map[feed_id] = int(max_age)
            except (ValueError, TypeError):
                pass

    for feed_id, items in (items_dict or {}).items():
        max_days = feed_max_age_map.get(feed_id, default_max_age_days)

        for item in items:
            if freshness_enabled and max_days > 0:
                if item.published_at and not is_within_days(item.published_at, max_days, timezone):
                    continue

            rss_items.append(
                {
                    "title": item.title,
                    "feed_id": feed_id,
                    "feed_name": id_to_name.get(feed_id, feed_id),
                    "url": item.url,
                    "published_at": item.published_at,
                    "summary": item.summary,
                    "author": item.author,
                }
            )

    return rss_items


def detect_new_rss_urls(storage_manager, rss_data: Optional[RSSData]) -> Tuple[Dict, set]:
    """
    返回 (new_items_dict, new_urls_set)
    """
    if not rss_data:
        return {}, set()
    new_items_dict: Dict = storage_manager.detect_new_rss_items(rss_data) or {}
    new_urls = set()
    for _feed_id, items in new_items_dict.items():
        for it in items:
            if getattr(it, "url", ""):
                new_urls.add(it.url)
    return new_items_dict, new_urls

