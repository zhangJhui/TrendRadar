# coding=utf-8
"""
python -m trendradar.api 启动入口
"""

import argparse

import uvicorn


def main() -> None:
    parser = argparse.ArgumentParser(description="TrendRadar API Server")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true", help="开发模式自动重载")
    args = parser.parse_args()

    uvicorn.run(
        "trendradar.api.app:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
    )


if __name__ == "__main__":
    main()

