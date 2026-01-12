# coding=utf-8

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from trendradar.storage.base import NewsData, RSSData


def read_titles_from_storage(
    storage_manager,
    date: Optional[str],
    platform_ids: Optional[List[str]] = None,
) -> Tuple[Dict, Dict, Dict, Optional[NewsData]]:
    """
    读取指定日期热榜（SQLite）并转换成 core.count_word_frequency 所需结构：
    - results: {source_id: {title: {"ranks": [...], "url": "...", "mobileUrl": "..."}}}
    - id_to_name: {source_id: source_name}
    - title_info: {source_id: {title: {"first_time","last_time","count","ranks","url","mobileUrl"}}}
    """
    news_data: Optional[NewsData] = storage_manager.get_today_all_data(date)
    if not news_data or not news_data.items:
        return {}, {}, {}, news_data

    results: Dict = {}
    id_to_name: Dict = {}
    title_info: Dict = {}

    for source_id, news_list in news_data.items.items():
        if platform_ids is not None and source_id not in platform_ids:
            continue

        source_name = news_data.id_to_name.get(source_id, source_id)
        id_to_name[source_id] = source_name
        results[source_id] = {}
        title_info[source_id] = {}

        for item in news_list:
            title = item.title
            ranks = getattr(item, "ranks", [item.rank])
            first_time = getattr(item, "first_time", item.crawl_time)
            last_time = getattr(item, "last_time", item.crawl_time)
            count = getattr(item, "count", 1)

            results[source_id][title] = {
                "ranks": ranks,
                "url": item.url or "",
                "mobileUrl": item.mobile_url or "",
            }
            title_info[source_id][title] = {
                "first_time": first_time,
                "last_time": last_time,
                "count": count,
                "ranks": ranks,
                "url": item.url or "",
                "mobileUrl": item.mobile_url or "",
            }

    return results, id_to_name, title_info, news_data


def detect_latest_new_titles(
    storage_manager,
    date: Optional[str],
    platform_ids: Optional[List[str]] = None,
) -> Dict:
    """
    按 core.data.detect_latest_new_titles_from_storage 的逻辑实现，但支持传入 date。
    返回：{source_id: {title: {"ranks":[rank], "url":"", "mobileUrl":""}}}
    """
    latest_data: Optional[NewsData] = storage_manager.get_latest_crawl_data(date)
    if not latest_data or not latest_data.items:
        return {}

    all_data: Optional[NewsData] = storage_manager.get_today_all_data(date)
    if not all_data or not all_data.items:
        return {}

    latest_time = latest_data.crawl_time

    # 最新批次标题
    latest_titles: Dict[str, Dict] = {}
    for source_id, news_list in latest_data.items.items():
        if platform_ids is not None and source_id not in platform_ids:
            continue
        latest_titles[source_id] = {}
        for item in news_list:
            latest_titles[source_id][item.title] = {
                "ranks": [item.rank],
                "url": item.url or "",
                "mobileUrl": item.mobile_url or "",
            }

    # 历史标题（first_time < latest_time）
    historical_titles: Dict[str, set] = {}
    for source_id, news_list in all_data.items.items():
        if platform_ids is not None and source_id not in platform_ids:
            continue
        historical_titles[source_id] = set()
        for item in news_list:
            first_time = getattr(item, "first_time", item.crawl_time)
            if first_time < latest_time:
                historical_titles[source_id].add(item.title)

    has_historical_data = any(len(titles) > 0 for titles in historical_titles.values())
    if not has_historical_data:
        return {}

    new_titles: Dict[str, Dict] = {}
    for source_id, source_latest_titles in latest_titles.items():
        historical_set = historical_titles.get(source_id, set())
        source_new_titles = {}
        for title, title_data in source_latest_titles.items():
            if title not in historical_set:
                source_new_titles[title] = title_data
        if source_new_titles:
            new_titles[source_id] = source_new_titles

    return new_titles


def read_rss_from_storage(
    storage_manager,
    date: Optional[str],
    mode: str,
) -> Optional[RSSData]:
    if mode == "current":
        return storage_manager.get_latest_rss_data(date)
    return storage_manager.get_rss_data(date)

