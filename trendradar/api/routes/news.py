# coding=utf-8

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from trendradar.api.models.request import NewsRequest
from trendradar.api.services.news_service import NewsService


router = APIRouter()


@router.post("/news")
def post_news(req: NewsRequest):
    try:
        if req.outputs == "html":
            return NewsService.get_news_html(req)
        return NewsService.get_news_json(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

