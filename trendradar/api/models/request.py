# coding=utf-8

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class NewsRequest(BaseModel):
    date: Optional[str] = Field(default=None, description="YYYY-MM-DD，默认今天")
    platforms: Optional[List[str]] = Field(default=None, description="平台ID列表（如 zhihu/weibo）")
    keywords: Optional[List[str]] = Field(default=None, description="关键词过滤（标题包含匹配）")
    limit: int = Field(default=50, ge=1, le=500, description="每个平台/每个RSS源最多返回条数")
    mode: Literal["current", "daily", "incremental"] = Field(default="current")
    include_rss: bool = Field(default=True)
    outputs: Literal["json", "html"] = Field(default="json")


class AnalysisQuery(BaseModel):
    date: Optional[str] = Field(default=None, description="YYYY-MM-DD，默认今天")
    platforms: Optional[List[str]] = Field(default=None, description="平台ID列表（如 zhihu/weibo）")
    keywords: Optional[List[str]] = Field(default=None, description="关键词过滤（标题包含匹配）")
    limit: int = Field(default=50, ge=1, le=500, description="每个平台最多纳入分析条数")
    mode: Literal["current", "daily", "incremental"] = Field(default="daily")


class AnalysisOptions(BaseModel):
    include_rss: bool = Field(default=False)
    max_news: int = Field(default=50, ge=1, le=200)
    language: str = Field(default="zh-CN")
    analysis_depth: Literal["quick", "standard", "deep"] = Field(default="standard")
    custom_prompt: str = Field(default="")


class AnalysisRequest(BaseModel):
    analysis_type: Literal["news_ids", "query"] = Field(description="news_ids 或 query")
    news_ids: Optional[List[str]] = Field(default=None)
    query: Optional[AnalysisQuery] = Field(default=None)
    options: AnalysisOptions = Field(default_factory=AnalysisOptions)

    # 允许扩展字段（兼容后续版本）
    extra: Dict[str, Any] = Field(default_factory=dict)

