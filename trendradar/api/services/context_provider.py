# coding=utf-8

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from trendradar.context import AppContext
from trendradar.core import load_config


def _load_dotenv_if_present() -> None:
    """
    与 CLI 行为对齐：如果安装了 python-dotenv，则自动加载 .env（cwd 优先，其次项目根目录）。
    """
    try:
        from dotenv import load_dotenv  # type: ignore
    except Exception:
        return

    # 1) 当前工作目录
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        return

    # 2) 项目根目录（trendradar/ 的上一级）
    project_root = Path(__file__).resolve().parents[2]
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)


@lru_cache(maxsize=1)
def get_ctx() -> AppContext:
    _load_dotenv_if_present()
    config = load_config()
    return AppContext(config)


def get_storage_manager():
    return get_ctx().get_storage_manager()

