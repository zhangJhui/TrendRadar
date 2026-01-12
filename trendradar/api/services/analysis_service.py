# coding=utf-8

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional, Tuple

from trendradar.ai import AIAnalyzer
from trendradar.api.models.request import AnalysisRequest, AnalysisQuery
from trendradar.api.models.response import ApiResponse
from trendradar.api.services.context_provider import get_ctx, get_storage_manager
from trendradar.api.utils.ids import generate_news_id
from trendradar.api.utils.rss import detect_new_rss_urls, rss_items_dict_to_list
from trendradar.api.utils.storage_readers import read_rss_from_storage, read_titles_from_storage
from trendradar.api.utils.time import now_iso, resolve_date
from trendradar.core.analyzer import count_rss_frequency


def _make_request_id(prefix: str) -> str:
    import random
    import time

    ts = time.strftime("%Y%m%d_%H%M%S", time.localtime())
    return f"{prefix}_{ts}_{random.randint(100, 999)}"


def _match_keywords(title: str, keywords: Optional[List[str]]) -> bool:
    if not keywords:
        return True
    title_l = title.lower()
    for k in keywords:
        kk = (k or "").strip()
        if kk and kk.lower() in title_l:
            return True
    return False


def _flatten_platform_names(id_to_name: Dict[str, str], platform_ids: Optional[List[str]]) -> List[str]:
    if not platform_ids:
        return list(id_to_name.values())
    return [id_to_name.get(pid, pid) for pid in platform_ids]


class AnalysisService:
    @staticmethod
    def run_analysis(req: AnalysisRequest) -> ApiResponse:
        ctx = get_ctx()
        storage = get_storage_manager()

        # 解析 query（用于确定 date/platforms/keywords/mode）
        q: AnalysisQuery
        if req.analysis_type == "query":
            if not req.query:
                raise ValueError("analysis_type=query 时必须提供 query")
            q = req.query
        else:
            # news_ids 模式：允许不传 query，默认今天/当日汇总
            q = req.query or AnalysisQuery()

        date = resolve_date(q.date, ctx.timezone)

        results, id_to_name, title_info, _news_data = read_titles_from_storage(
            storage, date, q.platforms
        )

        # 选取要分析的新闻子集
        sub_results: Dict[str, Dict] = {}
        sub_id_to_name: Dict[str, str] = {}
        sub_title_info: Dict[str, Dict] = {}

        if req.analysis_type == "news_ids":
            if not req.news_ids:
                raise ValueError("analysis_type=news_ids 时必须提供 news_ids")

            # 构建 id -> (platform_id, title) 映射（通过同一套规则重算）
            id_map: Dict[str, Tuple[str, str]] = {}
            for platform_id, titles_map in results.items():
                for title in titles_map.keys():
                    info = (title_info.get(platform_id, {}) or {}).get(title, {})
                    last_time = info.get("last_time")
                    nid = generate_news_id(platform_id, title, date, last_time)
                    id_map[nid] = (platform_id, title)

            for nid in req.news_ids:
                hit = id_map.get(nid)
                if not hit:
                    continue
                platform_id, title = hit
                sub_results.setdefault(platform_id, {})[title] = results[platform_id][title]
                sub_id_to_name[platform_id] = id_to_name.get(platform_id, platform_id)
                sub_title_info.setdefault(platform_id, {})[title] = title_info[platform_id][title]

        else:
            # query：按关键词过滤 + 每个平台 limit
            limit = int(q.limit or 50)
            for platform_id, titles_map in results.items():
                # 排序：按最小排名
                def _rank_key(title: str) -> int:
                    info = (title_info.get(platform_id, {}) or {}).get(title, {})
                    ranks = info.get("ranks") or []
                    return min(ranks) if ranks else 999999

                picked = 0
                for title in sorted(titles_map.keys(), key=_rank_key):
                    if not _match_keywords(title, q.keywords):
                        continue
                    sub_results.setdefault(platform_id, {})[title] = titles_map[title]
                    sub_id_to_name[platform_id] = id_to_name.get(platform_id, platform_id)
                    sub_title_info.setdefault(platform_id, {})[title] = title_info[platform_id][title]
                    picked += 1
                    if picked >= limit:
                        break

        # 统计（为确保可分析：强制“全部新闻”分组，不受频率词限制）
        stats, total_titles = ctx.count_frequency(
            results=sub_results,
            word_groups=[],
            filter_words=[],
            id_to_name=sub_id_to_name,
            title_info=sub_title_info,
            new_titles=None,
            mode="daily",
            global_filters=[],
            quiet=True,
        )

        # RSS（可选）
        rss_stats = None
        rss_total = 0
        if req.options.include_rss:
            rss_data = read_rss_from_storage(storage, date, q.mode)
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
                all_items_list = rss_items_dict_to_list(
                    rss_data.items,
                    rss_data.id_to_name,
                    rss_config=ctx.rss_config,
                    rss_feeds_config=ctx.rss_feeds,
                    timezone=ctx.timezone,
                )
                # 按 query.keywords 过滤（仅用于 AI 输入缩小范围）
                if q.keywords:
                    all_items_list = [x for x in all_items_list if _match_keywords(x.get("title", ""), q.keywords)]
                    if new_items_list:
                        new_items_list = [x for x in new_items_list if _match_keywords(x.get("title", ""), q.keywords)]

                rss_total = len(all_items_list)
                rss_stats, _ = count_rss_frequency(
                    rss_items=all_items_list,
                    word_groups=[],
                    filter_words=[],
                    global_filters=[],
                    new_items=new_items_list,
                    max_news_per_keyword=0,
                    sort_by_position_first=False,
                    timezone=ctx.timezone,
                    rank_threshold=ctx.rank_threshold,
                    quiet=True,
                )

        # AI 配置（复用现有 AIAnalyzer）
        ai_cfg = dict(ctx.config.get("AI_ANALYSIS", {}))
        ai_cfg["INCLUDE_RSS"] = bool(req.options.include_rss)
        ai_cfg["MAX_NEWS_FOR_ANALYSIS"] = int(req.options.max_news)

        # 预检：未配置 Key 时直接返回（保持顶层 success=true，但 analysis.success=false）
        api_key = (ai_cfg.get("API_KEY") or "").strip() or os.environ.get("AI_API_KEY", "").strip()
        if not api_key:
            platforms_display = _flatten_platform_names(sub_id_to_name, q.platforms)
            data = {
                "analysis": {
                    "summary": "",
                    "keyword_analysis": "",
                    "sentiment": "",
                    "cross_platform": "",
                    "impact": "",
                    "signals": "",
                    "conclusion": "",
                    "raw_response": "",
                    "success": False,
                    "error": "未配置 AI API Key，请在 config.yaml 或环境变量 AI_API_KEY 中设置",
                },
                "metadata": {
                    "total_news": int(total_titles + rss_total),
                    "analyzed_news": int(total_titles),  # 这里表示“可供分析的热榜条数”
                    "hotlist_count": int(total_titles),
                    "rss_count": int(rss_total),
                    "platforms_analyzed": platforms_display,
                    "keywords_analyzed": q.keywords or [],
                    "analysis_time": now_iso(ctx.timezone),
                    "processing_duration": None,
                    "model_info": {
                        "provider": ai_cfg.get("PROVIDER", ""),
                        "model": ai_cfg.get("MODEL", ""),
                        "api_endpoint": ai_cfg.get("BASE_URL", ""),
                    },
                },
                "news_analyzed": [
                    {
                        "id": generate_news_id(
                            pid,
                            title,
                            date,
                            (sub_title_info.get(pid, {}) or {}).get(title, {}).get("last_time"),
                        ),
                        "title": title,
                        "platform": sub_id_to_name.get(pid, pid),
                        "weight": None,
                    }
                    for pid, tmap in sub_results.items()
                    for title in tmap.keys()
                ],
            }
            return ApiResponse(
                success=True,
                timestamp=now_iso(ctx.timezone),
                request_id=_make_request_id("req"),
                data=data,
            )

        analyzer = AIAnalyzer(ai_cfg, ctx.get_time)
        if req.options.custom_prompt:
            analyzer.user_prompt_template = req.options.custom_prompt

        platforms_display = _flatten_platform_names(sub_id_to_name, q.platforms)
        result = analyzer.analyze(
            stats=stats,
            rss_stats=rss_stats,
            report_mode=q.mode,
            report_type="AI分析",
            platforms=platforms_display,
            keywords=q.keywords,
        )

        data = {
            "analysis": {
                "summary": result.summary,
                "keyword_analysis": result.keyword_analysis,
                "sentiment": result.sentiment,
                "cross_platform": result.cross_platform,
                "impact": result.impact,
                "signals": result.signals,
                "conclusion": result.conclusion,
                "raw_response": result.raw_response,
                "success": result.success,
                "error": result.error,
            },
            "metadata": {
                "total_news": int(getattr(result, "total_news", total_titles + rss_total)),
                "analyzed_news": int(getattr(result, "analyzed_news", total_titles)),
                "hotlist_count": int(getattr(result, "hotlist_count", total_titles)),
                "rss_count": int(getattr(result, "rss_count", rss_total)),
                "platforms_analyzed": platforms_display,
                "keywords_analyzed": q.keywords or [],
                "analysis_time": now_iso(ctx.timezone),
                "processing_duration": None,
                "model_info": {
                    "provider": ai_cfg.get("PROVIDER", ""),
                    "model": ai_cfg.get("MODEL", ""),
                    "api_endpoint": ai_cfg.get("BASE_URL", ""),
                },
            },
            "news_analyzed": [
                {
                    "id": generate_news_id(pid, title, date, (sub_title_info.get(pid, {}) or {}).get(title, {}).get("last_time")),
                    "title": title,
                    "platform": sub_id_to_name.get(pid, pid),
                    "weight": None,
                }
                for pid, tmap in sub_results.items()
                for title in tmap.keys()
            ],
        }

        return ApiResponse(
            success=True,
            timestamp=now_iso(ctx.timezone),
            request_id=_make_request_id("req"),
            data=data,
        )

