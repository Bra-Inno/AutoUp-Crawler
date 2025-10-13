# 🔥 hotlist-crawler

![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Version](https://img.shields.io/badge/version-2.0.0-green.svg)

**通用热榜内容爬虫包** - 支持知乎、微博、微信公众号等主流平台的智能内容抓取

## 🎯 项目简介

这是一个功能强大的Python内容抓取包，专门设计用于多平台内容获取。支持作为独立包使用，也可以集成到其他项目中。

### ✨ 核心特性

- 🔥 **多平台支持**: 知乎问题/文章、微博搜索、微信公众号等主流平台
- 🚀 **同步接口**: 所有API都是同步的，使用简单，无需async/await
- 🧠 **智能识别**: 根据URL自动识别平台类型和内容类型
- 💾 **登录保持**: 一次登录，长期有效，支持cookies持久化
- 🖼️ **完整内容**: 自动下载图片、视频等媒体文件
- 📄 **多格式输出**: 支持纯文本和Markdown格式
- 🏠 **本地存储**: 智能文件组织，按平台和内容分类存储
- 🚫 **无头运行**: 抓取时无界面运行，登录时显示浏览器
- 📊 **批量处理**: 支持多URL并发抓取

## 🛠️ 技术架构

- **浏览器引擎**: Playwright - 处理JavaScript渲染和反爬虫
- **HTML解析**: BeautifulSoup4 - 高效的网页内容解析
- **HTTP客户端**: httpx/requests - 可靠的网络请求处理
- **存储系统**: 本地文件 + JSON索引 - 无数据库依赖
- **缓存系统**: Redis(可选) + 内存缓存 - 提升性能

## 📦 安装使用

### 环境要求

- Python 3.8+
- Windows/macOS/Linux

### 1. 安装依赖

```bash
# 克隆项目
git clone https://github.com/xfrrn/hotlist-crawler.git
cd hotlist-crawler

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 2. 基础使用

```python
import hotlist_crawler
from hotlist_crawler import PlatformType

# 第一次使用需要登录（会打开浏览器）
hotlist_crawler.login(PlatformType.ZHIHU)
hotlist_crawler.login(PlatformType.WEIBO)

# 单个内容抓取
success = hotlist_crawler.fetch(
    url="https://www.zhihu.com/question/12345",
    destination="./downloads"
)

# 批量抓取
urls = [
    "https://www.zhihu.com/question/11111",
    "https://s.weibo.com/weibo?q=Python",
    "https://mp.weixin.qq.com/s/article123"
]
results = hotlist_crawler.batch_fetch(urls, "./batch_downloads")
```

## 🚀 快速开始

### 登录管理

```python
import hotlist_crawler
from hotlist_crawler import PlatformType

# 登录平台（仅需一次，状态会保存）
success = hotlist_crawler.login(PlatformType.ZHIHU)
print("登录成功" if success else "登录失败")

# 检查登录状态
if hotlist_crawler.is_online(PlatformType.ZHIHU):
    print("知乎已登录")

# 查看所有平台状态
status = hotlist_crawler.get_all_online_status()
for platform, online in status.items():
    print(f"{platform}: {'在线' if online else '离线'}")
```

### 内容抓取

```python
# 基础抓取
success = hotlist_crawler.fetch(
    url="https://www.zhihu.com/question/12345",
    destination="./data"
)

# 高级抓取（自定义参数）
success = hotlist_crawler.fetch(
    url="https://www.zhihu.com/question/12345",
    destination="./data",
    save_images=True,           # 下载图片
    output_format="markdown",   # Markdown格式
    max_answers=5              # 知乎问题最多5个回答
)

# 批量抓取
urls = ["url1", "url2", "url3"]
results = hotlist_crawler.batch_fetch(urls, "./batch_data")

print(f"成功: {results['summary']['success']}")
print(f"失败: {results['summary']['failed']}")
print(f"成功率: {results['summary']['success_rate']}")
```

### 平台识别

```python
# 获取URL平台信息
info = hotlist_crawler.get_platform_info("https://www.zhihu.com/question/12345")
print(f"平台: {info['platform']}")
print(f"支持: {info['supported']}")

# 获取所有支持的平台
platforms = hotlist_crawler.list_supported_platforms()
print(f"支持的平台: {platforms}")
```

## 📋 支持的平台

| 平台 | URL示例 | 功能支持 |
|------|---------|----------|
| 知乎问题 | `https://www.zhihu.com/question/12345` | ✅ 问题+回答+图片 |
| 知乎文章 | `https://zhuanlan.zhihu.com/p/12345` | ✅ 文章+图片 |
| 微博搜索 | `https://s.weibo.com/weibo?q=关键词` | ✅ 第一条帖子+视频 |
| 微信公众号 | `https://mp.weixin.qq.com/s/article_id` | ✅ 文章+图片 |
| 小红书 | `https://www.xiaohongshu.com/explore/12345` | 🚧 开发中 |
| 抖音 | `https://www.douyin.com/video/12345` | 🚧 开发中 |
| 哔哩哔哩 | `https://www.bilibili.com/video/BV12345` | 🚧 开发中 |

## 📁 输出结构

抓取的内容会按以下结构保存：

```
destination/
├── zhihu/                          # 知乎内容
│   └── abc123_问题标题/
│       ├── 问题标题.txt            # 纯文本
│       ├── 问题标题.md             # Markdown格式
│       └── images/                 # 图片文件夹
│           ├── question_images/    # 问题图片
│           └── answer_1_作者名/    # 回答图片
├── weibo/                          # 微博内容
│   └── def456_搜索关键词_作者帖子/
│       ├── 帖子标题.txt
│       ├── 帖子标题.md
│       └── attachments/            # 视频等附件
└── weixin/                         # 微信公众号
    └── ghi789_文章标题/
        ├── 文章标题.txt
        ├── 文章标题.md
        └── images/                 # 文章图片
```

## ⚙️ 配置选项

### 环境变量 (.env文件)

```bash
# Redis配置（可选）
REDIS_URL=redis://localhost:6379
CACHE_EXPIRE_SECONDS=3600

# 下载配置
DOWNLOAD_DIR=./downloads
MAX_IMAGE_SIZE=10485760  # 10MB

# Playwright配置
PLAYWRIGHT_HEADLESS=True
PLAYWRIGHT_TIMEOUT=90000
```

### Redis安装（可选，提升性能）

**Windows:**
```bash
choco install redis-64
redis-server
```

**Ubuntu/Debian:**
```bash
sudo apt-get install redis-server
sudo systemctl start redis-server
```

**macOS:**
```bash
brew install redis
brew services start redis
```

## 🔧 API参考

### 核心接口

| 接口 | 功能 | 返回值 |
|------|------|--------|
| `login(platform, headless=False)` | 平台登录 | `bool` |
| `is_online(platform)` | 检查登录状态 | `bool` |
| `fetch(url, destination, ...)` | 内容抓取 | `bool` |
| `batch_fetch(urls, destination, ...)` | 批量抓取 | `Dict` |
| `get_platform_info(url)` | URL平台分析 | `Dict` |
| `list_supported_platforms()` | 支持的平台列表 | `List[str]` |

详细API文档请参考：[接口简介.md](接口简介.md)

## 🛠️ 开发调试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_fetch.py

# 查看覆盖率
pytest --cov=hotlist_crawler
```

### 代码格式化

```bash
# 格式化代码
black hotlist_crawler/

# 检查代码风格
flake8 hotlist_crawler/
```

## 🚨 常见问题

### 1. Playwright浏览器未安装

```bash
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决方案：**
```bash
playwright install chromium
```

### 2. Windows异步错误

```bash
NotImplementedError: Task exception was never retrieved
```

**解决方案：** 已自动修复，系统会检测Windows环境并应用适当配置。

### 3. 登录状态丢失

如果登录状态经常丢失，检查：
- `chrome_user_data` 目录权限
- 网络连接稳定性
- 平台是否更新了安全策略

### 4. 抓取失败

常见原因和解决方案：
- **网络问题**: 检查网络连接和代理设置
- **反爬虫**: 系统已内置反检测，如仍失败可尝试重新登录
- **URL格式**: 确保URL格式正确且为支持的平台