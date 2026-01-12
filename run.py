#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TrendRadar 启动脚本（支持 .env 文件）
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 加载 .env 文件
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ 已加载环境变量文件: {env_file}")
    else:
        print("⚠️  未找到 .env 文件，使用系统环境变量")
except ImportError:
    print("⚠️  python-dotenv 未安装，无法加载 .env 文件")

# 运行主程序
if __name__ == "__main__":
    from trendradar.__main__ import main
    main()