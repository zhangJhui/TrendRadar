# coding=utf-8

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from fastapi.responses import HTMLResponse

from trendradar.api.models.request import NewsRequest
from trendradar.api.models.response import (
    ApiResponse,
    NewsItemOut,
    PlatformNewsOut,
    RssArticleOut,
    RssFeedOut,
)
from trendradar.api.services.context_provider import get_ctx, get_storage_manager
from trendradar.api.services.refresh_service import RefreshService
from trendradar.api.utils.ids import generate_news_id, generate_rss_id
from trendradar.api.utils.rss import detect_new_rss_urls, rss_items_dict_to_list
from trendradar.api.utils.storage_readers import detect_latest_new_titles, read_rss_from_storage, read_titles_from_storage
from trendradar.api.utils.time import now_iso, resolve_date, to_iso_datetime
from trendradar.core.analyzer import count_rss_frequency


def _match_keywords(title: str, keywords: Optional[List[str]]) -> List[str]:
    if not keywords:
        return []
    title_l = title.lower()
    matched = []
    for k in keywords:
        kk = (k or "").strip()
        if not kk:
            continue
        if kk.lower() in title_l:
            matched.append(kk)
    return matched


def _make_request_id(prefix: str) -> str:
    # 简单可读：req_YYYYMMDD_HHMMSS_xxx
    import random
    import time

    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return f"{prefix}_{ts}_{random.randint(100, 999)}"


class NewsService:
    @staticmethod
    def get_news_json(req: NewsRequest) -> ApiResponse:
        ctx = get_ctx()
        storage = get_storage_manager()

        # 每次调用都先抓取最新数据写入 output（与 CLI 行为一致）
        RefreshService.refresh_news(ctx, storage, platform_ids=req.platforms)
        if req.include_rss:
            RefreshService.refresh_rss(ctx, storage)

        date = resolve_date(req.date, ctx.timezone)

        results, id_to_name, title_info, news_data = read_titles_from_storage(
            storage, date, req.platforms, mode=req.mode
        )

        # 新增标题（用于 is_new）
        new_titles = detect_latest_new_titles(storage, date, req.platforms)

        # 平台维度组织
        platforms_out: Dict[str, PlatformNewsOut] = {}
        total_news = 0
        matched_news = 0
        new_news = 0

        # incremental：只返回“新增”新闻
        if req.mode == "incremental" and new_titles:
            filtered_results = {}
            for pid, titles_map in results.items():
                nt = new_titles.get(pid, {})
                if not nt:
                    continue
                filtered_results[pid] = {t: titles_map[t] for t in titles_map.keys() if t in nt}
            results = filtered_results

        for platform_id, titles_map in results.items():
            platform_name = id_to_name.get(platform_id, platform_id)

            items: List[NewsItemOut] = []
            total_count = 0
            matched_count = 0

            # 排序：按最小排名（越小越热），再按出现次数
            def _rank_key(title: str) -> Tuple[int, int]:
                info = (title_info.get(platform_id, {}) or {}).get(title, {})
                ranks = info.get("ranks") or []
                min_rank = min(ranks) if ranks else 999999
                cnt = int(info.get("count", 1) or 1)
                return (min_rank, -cnt)

            for title in sorted(titles_map.keys(), key=_rank_key):
                info = (title_info.get(platform_id, {}) or {}).get(title, {})
                ranks = info.get("ranks") or []
                first_time = info.get("first_time")
                last_time = info.get("last_time")
                cnt = int(info.get("count", 1) or 1)
                url = info.get("url", "") or ""
                mobile_url = info.get("mobileUrl", "") or ""

                total_count += 1

                matched_kw = _match_keywords(title, req.keywords)
                if req.keywords and not matched_kw:
                    continue

                matched_count += 1

                is_new = bool(new_titles.get(platform_id, {}).get(title))
                if is_new:
                    new_news += 1

                item = NewsItemOut(
                    id=generate_news_id(platform_id, title, date, last_time),
                    title=title,
                    url=url,
                    mobile_url=mobile_url,
                    rank=min(ranks) if ranks else 0,
                    hot_score=None,
                    first_seen=to_iso_datetime(date, first_time, ctx.timezone),
                    last_seen=to_iso_datetime(date, last_time, ctx.timezone),
                    keyword_matched=matched_kw,
                    is_new=is_new,
                    appear_count=cnt,
                    rank_history=[int(r) for r in ranks if isinstance(r, int) or (isinstance(r, str) and str(r).isdigit())],
                )
                items.append(item)

                if len(items) >= req.limit:
                    break

            platforms_out[platform_name] = PlatformNewsOut(
                platform_id=platform_id,
                platform_name=platform_name,
                total_count=total_count,
                matched_count=matched_count,
                news_list=items,
            )

            total_news += total_count
            matched_news += matched_count

        # RSS
        rss_feeds_out: Dict[str, RssFeedOut] = {}
        rss_articles_total = 0
        rss_articles_matched = 0

        if req.include_rss:
            rss_data = read_rss_from_storage(storage, date, req.mode)
            new_items_dict, new_urls = detect_new_rss_urls(storage, rss_data)

            if rss_data and rss_data.items:
                for feed_id, rss_list in rss_data.items.items():
                    feed_name = rss_data.id_to_name.get(feed_id, feed_id)
                    total_count = len(rss_list)
                    matched_count = 0
                    articles: List[RssArticleOut] = []

                    for it in rss_list:
                        title = it.title
                        matched_kw = _match_keywords(title, req.keywords)
                        if req.keywords and not matched_kw:
                            continue

                        matched_count += 1
                        is_fresh = bool(it.url and it.url in new_urls)

                        articles.append(
                            RssArticleOut(
                                id=generate_rss_id(feed_id, title, it.published_at or ""),
                                title=title,
                                url=it.url,
                                published_at=it.published_at or None,
                                author=it.author or "",
                                summary=it.summary or "",
                                keyword_matched=matched_kw,
                                is_fresh=is_fresh,
                            )
                        )

                        if len(articles) >= req.limit:
                            break

                    rss_feeds_out[feed_name] = RssFeedOut(
                        feed_id=feed_id,
                        feed_name=feed_name,
                        feed_url="",
                        total_count=total_count,
                        matched_count=matched_count,
                        articles=articles,
                    )

                    rss_articles_total += total_count
                    rss_articles_matched += matched_count

        summary = {
            "total_platforms": len(platforms_out),
            "active_platforms": len([p for p in platforms_out.values() if p.total_count > 0]),
            "total_news": total_news,
            "matched_news": matched_news,
            "new_news": new_news,
            "rss_articles": rss_articles_total,
            "keywords_found": req.keywords or [],
            "date_range": {"start": f"{date}T00:00:00", "end": f"{date}T23:59:59"},
        }

        return ApiResponse(
            success=True,
            timestamp=now_iso(ctx.timezone),
            request_id=_make_request_id("req"),
            data={
                "platforms": {k: v.model_dump() for k, v in platforms_out.items()},
                "rss_feeds": {k: v.model_dump() for k, v in rss_feeds_out.items()},
                "summary": summary,
            },
        )

    @staticmethod
    def get_news_html(req: NewsRequest) -> HTMLResponse:
        ctx = get_ctx()
        storage = get_storage_manager()

        # 每次调用都先抓取最新数据写入 output（与 CLI 行为一致）
        RefreshService.refresh_news(ctx, storage, platform_ids=req.platforms)
        if req.include_rss:
            RefreshService.refresh_rss(ctx, storage)

        date = resolve_date(req.date, ctx.timezone)

        results, id_to_name, title_info, news_data = read_titles_from_storage(
            storage, date, req.platforms, mode=req.mode
        )
        new_titles = detect_latest_new_titles(storage, date, req.platforms)

        # 热榜 stats（复用现有频率词规则）
        try:
            word_groups, filter_words, global_filters = ctx.load_frequency_words()
        except FileNotFoundError:
            word_groups, filter_words, global_filters = [], [], []

        stats, total_titles = ctx.count_frequency(
            results=results,
            word_groups=word_groups,
            filter_words=filter_words,
            id_to_name=id_to_name,
            title_info=title_info,
            new_titles=new_titles,
            mode=req.mode,
            global_filters=global_filters,
            quiet=True,
        )

        report_data = ctx.prepare_report(
            stats=stats,
            failed_ids=(news_data.failed_ids if news_data else []),
            new_titles=new_titles,
            id_to_name=id_to_name,
            mode=req.mode,
        )

        # RSS stats（复用 count_rss_frequency）
        rss_stats = None
        rss_new_stats = None
        if req.include_rss:
            rss_data = read_rss_from_storage(storage, date, req.mode)
            if rss_data and rss_data.items:
                new_items_dict, _new_urls = detect_new_rss_urls(storage, rss_data)
                new_items_list = None
                if new_items_dict:
                    new_items_list = rss_items_dict_to_list(
                        new_items_dict,
                        rss_data.id_to_name,
                        rss_config=ctx.rss_config,
                        rss_feeds_config=ctx.rss_feeds,
                        timezone=ctx.timezone,
                    )

                if req.mode == "incremental":
                    if new_items_list:
                        rss_stats, _ = count_rss_frequency(
                            rss_items=new_items_list,
                            word_groups=word_groups,
                            filter_words=filter_words,
                            global_filters=global_filters,
                            new_items=new_items_list,
                            max_news_per_keyword=ctx.config.get("MAX_NEWS_PER_KEYWORD", 0),
                            sort_by_position_first=ctx.config.get("SORT_BY_POSITION_FIRST", False),
                            timezone=ctx.timezone,
                            rank_threshold=ctx.rank_threshold,
                            quiet=True,
                        )
                else:
                    all_items_list = rss_items_dict_to_list(
                        rss_data.items,
                        rss_data.id_to_name,
                        rss_config=ctx.rss_config,
                        rss_feeds_config=ctx.rss_feeds,
                        timezone=ctx.timezone,
                    )
                    rss_stats, _ = count_rss_frequency(
                        rss_items=all_items_list,
                        word_groups=word_groups,
                        filter_words=filter_words,
                        global_filters=global_filters,
                        new_items=new_items_list,
                        max_news_per_keyword=ctx.config.get("MAX_NEWS_PER_KEYWORD", 0),
                        sort_by_position_first=ctx.config.get("SORT_BY_POSITION_FIRST", False),
                        timezone=ctx.timezone,
                        rank_threshold=ctx.rank_threshold,
                        quiet=True,
                    )
                    if new_items_list:
                        rss_new_stats, _ = count_rss_frequency(
                            rss_items=new_items_list,
                            word_groups=word_groups,
                            filter_words=filter_words,
                            global_filters=global_filters,
                            new_items=new_items_list,
                            max_news_per_keyword=ctx.config.get("MAX_NEWS_PER_KEYWORD", 0),
                            sort_by_position_first=ctx.config.get("SORT_BY_POSITION_FIRST", False),
                            timezone=ctx.timezone,
                            rank_threshold=ctx.rank_threshold,
                            quiet=True,
                        )

        html = ctx.render_html(
            report_data=report_data,
            total_titles=total_titles,
            is_daily_summary=True,
            mode=req.mode,
            update_info=None,
            rss_items=rss_stats,
            rss_new_items=rss_new_stats,
            ai_analysis=None,
        )
        return HTMLResponse(content=html, media_type="text/html; charset=utf-8")

