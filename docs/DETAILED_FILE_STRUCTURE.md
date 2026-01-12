# TrendRadar 完整文件结构分析

## 项目概述
TrendRadar v5.0.0 是一个智能热点新闻聚合与分析工具，支持多平台新闻抓取、AI分析和多渠道推送。

## 根目录文件

### 📋 项目配置文件
- **`pyproject.toml`** - Python项目配置文件，定义依赖和构建设置
  - 项目版本：5.0.0
  - 主要依赖：requests, PyYAML, fastmcp, websockets, feedparser, boto3
  - 两个入口点：`trendradar` (主程序) 和 `trendradar-mcp` (MCP服务器)

- **`requirements.txt`** - Python依赖列表（与pyproject.toml同步）
- **`uv.lock`** - UV包管理器的锁定文件，确保依赖版本一致性
- **`version`** - 主程序版本号：5.0.0
- **`version_mcp`** - MCP服务器版本号：3.1.5

### 📄 文档文件
- **`README.md`** - 中文主文档 (142KB)
- **`README-EN.md`** - 英文文档 (145KB)
- **`README-Cherry-Studio.md`** - Cherry Studio集成教程
- **`README-MCP-FAQ.md`** - MCP常见问题（中文）
- **`README-MCP-FAQ-EN.md`** - MCP常见问题（英文）
- **`LICENSE`** - 开源许可证文件 (35KB)

### 🚀 启动脚本
- **`setup-mac.sh`** - Mac系统一键部署脚本
  - 自动安装UV包管理器
  - 创建虚拟环境并安装依赖
  - 提供Cherry Studio配置指导

- **`setup-windows.bat`** - Windows部署脚本（中文）
- **`setup-windows-en.bat`** - Windows部署脚本（英文）
- **`start-http.sh`** - HTTP模式启动脚本
- **`start-http.bat`** - Windows HTTP模式启动脚本

### 🌐 Web界面
- **`index.html`** - 新闻报告Web界面 (60KB)

### 🔧 其他配置
- **`.gitignore`** - Git忽略文件配置
- **`.dockerignore`** - Docker构建忽略文件

## 📁 主要目录结构

### 1. `trendradar/` - 核心应用代码
```
trendradar/
├── __init__.py          # 包初始化
├── __main__.py          # 主程序入口 (56KB)
├── context.py           # 应用上下文管理 (15KB)
├── ai/                  # AI分析模块
│   ├── __init__.py
│   ├── analyzer.py      # AI分析器
│   ├── client.py        # AI客户端
│   ├── config.py        # AI配置
│   └── prompt.py        # 提示词管理
├── core/                # 核心功能模块
│   ├── __init__.py
│   ├── analyzer.py      # 数据分析器
│   ├── config.py        # 配置管理
│   ├── data.py          # 数据模型
│   ├── frequency.py     # 关键词频率分析
│   └── loader.py        # 数据加载器
├── crawler/             # 爬虫模块
│   ├── __init__.py
│   ├── fetcher.py       # 主爬虫
│   └── rss/             # RSS订阅模块
│       ├── __init__.py
│       ├── fetcher.py   # RSS获取器
│       └── parser.py    # RSS解析器
├── notification/        # 通知推送模块
│   ├── __init__.py
│   ├── batch.py         # 批量处理
│   ├── dispatcher.py    # 消息分发器
│   ├── formatters.py    # 格式化器
│   ├── push_manager.py  # 推送管理器
│   ├── renderer.py      # 渲染器
│   ├── senders.py       # 发送器
│   └── splitter.py      # 消息分割器
├── report/              # 报告生成模块
│   ├── __init__.py
│   ├── generator.py     # 报告生成器
│   ├── html.py          # HTML报告
│   ├── markdown.py      # Markdown报告
│   ├── renderer.py      # 报告渲染器
│   ├── template.py      # 模板管理
│   ├── txt.py           # 文本报告
│   └── utils.py         # 报告工具
├── storage/             # 存储模块
│   ├── __init__.py
│   ├── base.py          # 存储基类
│   ├── cloud.py         # 云存储
│   ├── local.py         # 本地存储
│   ├── manager.py       # 存储管理器
│   ├── models.py        # 数据模型
│   ├── s3.py            # S3存储
│   ├── sqlite.py        # SQLite存储
│   └── utils.py         # 存储工具
└── utils/               # 工具模块
    ├── __init__.py
    ├── date.py          # 日期工具
    ├── http.py          # HTTP工具
    ├── logger.py        # 日志工具
    └── text.py          # 文本处理工具
```

### 2. `mcp_server/` - MCP AI分析服务器
```
mcp_server/
├── __init__.py          # 包初始化
├── server.py            # MCP服务器主程序 (49KB)
├── services/            # 服务层
│   ├── __init__.py
│   ├── cache_service.py # 缓存服务
│   ├── data_service.py  # 数据服务
│   └── parser_service.py # 解析服务
├── tools/               # MCP工具集 (21个专用工具)
│   ├── __init__.py
│   ├── analytics.py     # 分析工具
│   ├── config_mgmt.py   # 配置管理工具
│   ├── data_query.py    # 数据查询工具
│   ├── search_tools.py  # 搜索工具
│   ├── storage_sync.py  # 存储同步工具
│   └── system.py        # 系统工具
└── utils/               # 工具模块
    ├── __init__.py
    ├── date_parser.py   # 日期解析器
    ├── errors.py        # 错误处理
    └── validators.py    # 验证器
```

### 3. `config/` - 配置文件目录
```
config/
├── config.yaml          # 主配置文件 (16KB)
├── frequency_words.txt  # 关键词配置 (9.7KB)
└── ai_analysis_prompt.txt # AI分析提示词 (4.8KB)
```

**配置文件说明：**
- `config.yaml`: 包含平台配置、通知设置、AI配置等
- `frequency_words.txt`: 定义感兴趣的关键词和过滤规则
- `ai_analysis_prompt.txt`: AI分析的提示词模板

### 4. `docker/` - Docker部署配置
```
docker/
├── .env                 # Docker环境变量 (3.3KB)
├── docker-compose.yml   # Docker Compose配置
├── docker-compose-build.yml # 构建版本配置
├── Dockerfile           # 主程序镜像
├── Dockerfile.mcp       # MCP服务器镜像
├── entrypoint.sh        # 容器入口脚本
└── manage.py            # 容器管理工具 (23KB)
```

**Docker部署特性：**
- 支持两个独立镜像：主程序和MCP服务器
- 内置Web服务器查看报告
- 支持定时任务和手动执行
- 完整的容器管理界面

### 5. `.github/` - GitHub配置
```
.github/
├── workflows/           # GitHub Actions工作流
│   ├── crawler.yml      # 主爬虫工作流 (7.3KB)
│   ├── clean-crawler.yml # 清理工作流
│   └── docker.yml       # Docker构建工作流
└── ISSUE_TEMPLATE/      # Issue模板
    ├── 01-bug-report.yml
    ├── 02-feature-request.yml
    ├── 03-ai-and-config.yml
    └── config.yml
```

**GitHub Actions特性：**
- 零服务器部署，完全基于GitHub基础设施
- 自动定时执行爬虫
- 支持云存储数据持久化
- 完整的Issue模板系统

### 6. `output/` - 输出目录
```
output/
├── index.html           # Web报告首页
├── 2026-01-12/         # 按日期组织的输出
├── news/               # 新闻数据存储
│   ├── baidu/          # 百度热搜
│   ├── bilibili/       # B站热榜
│   ├── cls/            # 财联社
│   ├── douyin/         # 抖音热榜
│   ├── phoenix/        # 凤凰新闻
│   ├── thepaper/       # 澎湃新闻
│   ├── tieba/          # 百度贴吧
│   ├── toutiao/        # 今日头条
│   ├── wallstreet/     # 华尔街见闻
│   ├── weibo/          # 微博热搜
│   └── zhihu/          # 知乎热榜
└── rss/                # RSS订阅数据
```

### 7. `_image/` - 文档图片资源
包含22个图片文件，用于README文档展示：
- 功能演示截图
- 配置界面截图
- 部署教程图片
- 品牌Logo和横幅

### 8. `.venv/` - Python虚拟环境
UV包管理器创建的虚拟环境，包含所有项目依赖。

## 🔧 核心技术栈

### 后端技术
- **Python 3.10+** - 主要编程语言
- **FastMCP** - Model Context Protocol实现
- **Requests** - HTTP请求库
- **PyYAML** - YAML配置解析
- **Feedparser** - RSS/Atom解析
- **Boto3** - AWS S3兼容存储
- **SQLite** - 本地数据库
- **WebSockets** - 实时通信

### 部署技术
- **Docker** - 容器化部署
- **GitHub Actions** - CI/CD和零服务器部署
- **UV** - 现代Python包管理器
- **Supercronic** - 容器内定时任务

### AI集成
- **MCP (Model Context Protocol)** - AI模型集成标准
- **多AI提供商支持** - DeepSeek、OpenAI、Google Gemini
- **21个专用工具** - 数据查询、分析、配置管理

## 📊 项目规模统计

### 代码文件统计
- **Python文件**: 约60个
- **配置文件**: 15个
- **脚本文件**: 8个
- **文档文件**: 6个
- **Docker文件**: 7个

### 功能模块
- **11个新闻平台** - 支持主流中文资讯平台
- **8种通知渠道** - 企业微信、飞书、钉钉、Telegram等
- **3种部署方式** - GitHub Actions、Docker、本地安装
- **21个MCP工具** - 完整的AI分析工具链

### 文件大小分布
- **大型文件** (>50KB): README文档、主程序文件
- **中型文件** (10-50KB): 配置文件、管理脚本
- **小型文件** (<10KB): 大部分Python模块

## 🎯 架构设计特点

### 1. 模块化设计
- 清晰的功能分层：爬虫、存储、通知、分析
- 松耦合架构，便于扩展和维护
- 统一的接口设计

### 2. 多存储后端
- 本地SQLite存储
- S3兼容云存储
- 自动选择最佳存储方案

### 3. 灵活部署
- 支持多种部署方式
- 零配置快速启动
- 完整的容器化支持

### 4. AI原生设计
- 内置MCP服务器
- 21个专用分析工具
- 支持多种AI模型

这个项目展现了现代Python应用的最佳实践，结合了传统的新闻聚合功能与前沿的AI分析能力，为用户提供了一个完整的个性化资讯解决方案。