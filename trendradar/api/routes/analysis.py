# coding=utf-8

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from trendradar.api.models.request import AnalysisRequest
from trendradar.api.services.analysis_service import AnalysisService


router = APIRouter()


@router.post("/analysis")
def post_analysis(req: AnalysisRequest):
    try:
        return AnalysisService.run_analysis(req)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

