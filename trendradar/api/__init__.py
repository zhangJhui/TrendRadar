# coding=utf-8
"""
TrendRadar API 模块（FastAPI）

零侵入：只读取现有 SQLite/output 数据，复用现有 report/ai 逻辑，不修改数据库结构与既有业务流程。
"""

from .app import app

__all__ = ["app"]

