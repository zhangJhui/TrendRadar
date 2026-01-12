# coding=utf-8
"""
FastAPI 应用入口
"""

from fastapi import FastAPI

from trendradar.api.routes.analysis import router as analysis_router
from trendradar.api.routes.news import router as news_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="TrendRadar API",
        description="TrendRadar 零侵入式 API 接口层",
        version="1.0.0",
        # 避免占用主站 /docs、/openapi.json：统一挂到 /news-api/* 下
        docs_url="/news-api/docs",
        redoc_url="/news-api/redoc",
        openapi_url="/news-api/openapi.json",
    )

    app.include_router(news_router, prefix="/news-api", tags=["news"])
    app.include_router(analysis_router, prefix="/news-api", tags=["analysis"])

    return app


app = create_app()

