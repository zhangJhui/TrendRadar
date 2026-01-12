# coding=utf-8

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from trendradar.crawler import DataFetcher
from trendradar.crawler.rss import RSSFetcher, RSSFeedConfig
from trendradar.storage import convert_crawl_results_to_news_data
from trendradar.storage.base import NewsData, RSSData


class RefreshService:
    """
    复用 CLI 的抓取+落库逻辑（不走推送/不生成文件），用于 API 在请求时刷新数据。
    """

    @staticmethod
    def refresh_news(ctx, storage_manager, platform_ids: Optional[List[str]] = None) -> NewsData:
        """
        抓取热榜并写入存储（output/news/*.db）。
        """
        if not ctx.config.get("ENABLE_CRAWLER", True):
            raise RuntimeError("爬虫功能已禁用（ENABLE_CRAWLER=False）")

        ids = []
        for platform in ctx.platforms:
            pid = platform.get("id")
            if not pid:
                continue
            if platform_ids is not None and pid not in platform_ids:
                continue
            if "name" in platform:
                ids.append((pid, platform["name"]))
            else:
                ids.append(pid)

        # 代理策略：与 CLI 的本地行为一致（USE_PROXY 开关）
        proxy_url = ctx.config.get("DEFAULT_PROXY") if ctx.config.get("USE_PROXY") else None
        fetcher = DataFetcher(proxy_url=proxy_url)

        results, id_to_name, failed_ids = fetcher.crawl_websites(
            ids_list=ids,
            request_interval=int(ctx.config.get("REQUEST_INTERVAL", 100)),
        )

        crawl_time = ctx.format_time()
        crawl_date = ctx.format_date() if not platform_ids else ctx.format_date()  # 同一天内刷新

        news_data = convert_crawl_results_to_news_data(
            results=results,
            id_to_name=id_to_name,
            failed_ids=failed_ids,
            crawl_time=crawl_time,
            crawl_date=crawl_date,
        )

        storage_manager.save_news_data(news_data)
        return news_data

    @staticmethod
    def refresh_rss(ctx, storage_manager) -> Optional[RSSData]:
        """
        抓取 RSS 并写入存储（output/rss/*.db）。是否启用由配置决定。
        """
        rss_cfg = ctx.rss_config or {}
        if not rss_cfg.get("ENABLED", False):
            return None

        feeds_cfg = ctx.rss_feeds or []
        feeds: List[RSSFeedConfig] = []
        for feed_config in feeds_cfg:
            max_age_days = feed_config.get("max_age_days")
            try:
                max_age_days = int(max_age_days) if max_age_days is not None else None
            except (ValueError, TypeError):
                max_age_days = None

            feed = RSSFeedConfig(
                id=feed_config.get("id", ""),
                name=feed_config.get("name", ""),
                url=feed_config.get("url", ""),
                max_items=feed_config.get("max_items", 50),
                enabled=feed_config.get("enabled", True),
                max_age_days=max_age_days,
            )
            if feed.id and feed.url and feed.enabled:
                feeds.append(feed)

        if not feeds:
            return None

        freshness_cfg = rss_cfg.get("FRESHNESS_FILTER", {})
        fetcher = RSSFetcher(
            feeds=feeds,
            request_interval=int(rss_cfg.get("REQUEST_INTERVAL", 2000)),
            timeout=int(rss_cfg.get("TIMEOUT", 15)),
            use_proxy=bool(rss_cfg.get("USE_PROXY", False)),
            proxy_url=str(rss_cfg.get("PROXY_URL", "")),
            timezone=ctx.timezone,
            freshness_enabled=bool(freshness_cfg.get("ENABLED", True)),
            default_max_age_days=int(freshness_cfg.get("MAX_AGE_DAYS", 3)),
        )

        rss_data = fetcher.fetch_all()
        storage_manager.save_rss_data(rss_data)
        return rss_data

