# coding=utf-8

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    timestamp: str
    request_id: str
    data: Dict[str, Any] = Field(default_factory=dict)


class NewsItemOut(BaseModel):
    id: str
    title: str
    url: str = ""
    mobile_url: str = ""
    rank: int = 0
    hot_score: Optional[float] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None
    keyword_matched: List[str] = Field(default_factory=list)
    is_new: bool = False
    appear_count: int = 1
    rank_history: List[int] = Field(default_factory=list)


class PlatformNewsOut(BaseModel):
    platform_id: str
    platform_name: str
    total_count: int
    matched_count: int
    news_list: List[NewsItemOut] = Field(default_factory=list)


class RssArticleOut(BaseModel):
    id: str
    title: str
    url: str
    published_at: Optional[str] = None
    author: str = ""
    summary: str = ""
    keyword_matched: List[str] = Field(default_factory=list)
    is_fresh: bool = False


class RssFeedOut(BaseModel):
    feed_id: str
    feed_name: str
    feed_url: str = ""
    total_count: int
    matched_count: int
    articles: List[RssArticleOut] = Field(default_factory=list)

