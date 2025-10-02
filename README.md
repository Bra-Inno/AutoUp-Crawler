# 🔥 热榜爬虫 (Hotlist Crawler)# 热榜爬虫项目 - 使用指南



一个基于 FastAPI 的多平台内容爬虫系统，支持微信公众号、知乎、微博等主流平台的内容抓取，具备智能存储、图片下载、多格式输出等功能。## 🎯 项目简介



![Python](https://img.shields.io/badge/python-v3.8+-blue.svg)这是一个基于 FastAPI 的通用内容抓取 API 服务，现已整合了强大的微信公众号文章抓取功能。项目支持：

![FastAPI](https://img.shields.io/badge/FastAPI-0.68+-green.svg)

![License](https://img.shields.io/badge/license-MIT-blue.svg)- **智能平台识别**：自动识别知乎、微信公众号等平台

- **反爬虫处理**：使用 Playwright 处理 JavaScript 渲染和反爬虫机制

## 🎯 功能特性- **图片下载**：自动下载文章中的图片到本地

- **Markdown 转换**：将文章转#### 3. Playwright 浏览器未安装

- 🔥 **多平台支持**: 支持微信公众号、知乎问题/文章、微博搜索等主流平台```

- 🚀 **异步处理**: 基于FastAPI的高性能异步架构playwright._impl._api_types.Error: Executable doesn't exist

- 🧠 **智能解析**: 使用Playwright处理JavaScript渲染页面```

- 💾 **智能缓存**: Redis缓存提升性能，内存缓存作为备选

- 📱 **移动适配**: 模拟移动设备访问，获取最佳内容**解决方案：**

- 🖼️ **图片处理**: 自动下载和处理文章中的图片和视频```bash

- 📄 **多格式输出**: 支持纯文本、HTML、Markdown格式playwright install chromium

- 🏠 **本地存储**: 自动保存所有内容到本地，按平台分类```

- 📂 **智能组织**: 每篇文章独立目录，包含文本、图片、元数据

- 🔍 **存储管理**: 提供API查看和管理本地存储内容#### 4. Windows 系统 Playwright 异步错误

```

## 🛠️ 技术栈NotImplementedError: Task exception was never retrieved

```

- **Web框架**: FastAPI

- **浏览器自动化**: Playwright**解决方案：**

- **HTML解析**: BeautifulSoup4- 已自动修复：系统会检测 Windows 环境并应用适当的事件循环策略

- **数据验证**: Pydantic- 如果仍有问题，Playwright 会自动降级到基础 HTTP 抓取

- **缓存系统**: Redis (可选)- 降级模式下功能有限（无图片下载、无 Markdown）wn 格式

- **HTTP客户端**: httpx- **缓存优化**：Redis 缓存避免重复抓取

- **数据库**: 本地文件存储 + JSON索引

## 🚀 快速开始

## 📦 安装部署

### 1. 安装依赖

### 环境要求

```bash

- Python 3.8+pip install -r requirements.txt

- Node.js (用于Playwright)playwright install chromium

- Redis (可选，用于缓存)```



### 1. 克隆项目### 2. Redis 配置（可选）



```bash#### 选项 A：使用 Redis（推荐，用于生产环境）

git clone https://github.com/xfrrn/hotlist-crawler.git

cd hotlist-crawler**Windows 用户：**

``````bash

# 使用 Chocolatey 安装 Redis

### 2. 安装依赖choco install redis-64



```bash# 或者下载 Redis for Windows

# 安装Python依赖# 访问：https://github.com/microsoftarchive/redis/releases

pip install -r requirements.txt

# 启动 Redis 服务

# 安装Playwright浏览器redis-server

playwright install chromium

```# 在新的终端窗口测试连接

redis-cli ping

### 3. Redis 配置（可选但推荐）```



#### Windows 用户：**其他系统：**

```bash```bash

# 使用 Chocolatey 安装 Redis# Ubuntu/Debian

choco install redis-64sudo apt-get install redis-server

sudo systemctl start redis-server

# 或者下载 Redis for Windows

# 访问：https://github.com/microsoftarchive/redis/releases# macOS

brew install redis

# 启动 Redis 服务brew services start redis

redis-server

# 测试连接

# 在新的终端窗口测试连接redis-cli ping

redis-cli ping```

```

#### 选项 B：无 Redis 模式（开发/测试）

#### 其他系统：

```bash如果不安装 Redis，系统会自动使用内存缓存，无需额外配置。

# Ubuntu/Debian

sudo apt-get install redis-server### 3. 启动 API 服务

sudo systemctl start redis-server

```bash

# macOSuvicorn app.main:app --reload

brew install redis```

brew services start redis

### 4. 访问 API 文档

# 测试连接

redis-cli ping打开浏览器访问 `http://localhost:8000/docs` 查看 API 文档

```

## 📋 API 使用示例

#### 无 Redis 模式（开发/测试）

如果不安装 Redis，系统会自动使用内存缓存，无需额外配置。### 基础抓取（仅文本）



### 4. 启动服务```bash

curl -X POST "http://localhost:8000/scrape" \

```bash     -H "Content-Type: application/json" \

# 方式一：使用启动脚本     -d '{

python run_server.py       "url": "https://mp.weixin.qq.com/s/your-article-url",

       "save_images": false,

# 方式二：使用uvicorn       "output_format": "text"

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000     }'

```

# 方式三：使用批处理文件 (Windows)

start_server.bat### 高级抓取（包含图片和 Markdown）

```

```bash

### 5. 访问服务curl -X POST "http://localhost:8000/scrape" \

     -H "Content-Type: application/json" \

- **API文档**: http://localhost:8000/docs     -d '{

- **健康检查**: http://localhost:8000/       "url": "https://mp.weixin.qq.com/s/your-article-url",

       "save_images": true,

## 🚀 快速开始       "output_format": "markdown"

     }'

### API调用示例```



#### 1. 抓取微信公众号文章## 📊 响应示例



```python```json

import requests{

  "platform": "weixin_mp",

response = requests.post("http://localhost:8000/scrape", json={  "source_url": "https://mp.weixin.qq.com/s/example",

    "url": "https://mp.weixin.qq.com/s/your-article-url",  "data": {

    "save_images": True,    "title": "文章标题",

    "output_format": "markdown",    "author": "作者名称",

    "force_save": True    "content": "纯文本内容...",

})    "markdown_content": "# 文章标题\n**作者:** 作者名称\n\n文章内容...",

    "images": [

print(response.json())      {

```        "original_url": "https://example.com/image.jpg",

        "local_path": "image_1.jpg",

#### 2. 抓取知乎问题        "alt_text": "图片描述"

      }

```python    ],

import requests    "save_directory": "./downloads/文章标题"

  },

response = requests.post("http://localhost:8000/scrape", json={  "scrape_time": "2025-09-30T10:00:00+08:00"

    "url": "https://www.zhihu.com/question/123456789",}

    "save_images": True,```

    "output_format": "markdown",

    "force_save": True## ⚙️ 配置选项

})

### 环境变量配置（.env 文件）

print(response.json())

``````bash

# Redis 配置

#### 3. 抓取微博搜索结果REDIS_URL=redis://localhost:6379

CACHE_EXPIRE_SECONDS=3600

```python

import requests# 下载配置

DOWNLOAD_DIR=./downloads

response = requests.post("http://localhost:8000/scrape", json={MAX_IMAGE_SIZE=10485760  # 10MB

    "url": "https://s.weibo.com/weibo?q=搜索关键词",

    "save_images": True,# Playwright 配置

    "output_format": "markdown", PLAYWRIGHT_HEADLESS=true

    "force_save": TruePLAYWRIGHT_TIMEOUT=90000

})```



print(response.json())## 🔧 支持的平台

```

| 平台 | 域名 | 功能支持 |

### curl 命令示例|------|------|----------|

| 知乎 | zhuanlan.zhihu.com, www.zhihu.com | 基础文本抓取 |

```bash| 微信公众号 | mp.weixin.qq.com | 全功能（图片、Markdown） |

# 基础抓取（仅文本）

curl -X POST "http://localhost:8000/scrape" \\## 🎨 新功能特点

     -H "Content-Type: application/json" \\

     -d '{### 1. 智能图片处理

       "url": "https://mp.weixin.qq.com/s/your-article-url",- 自动下载文章中的图片

       "save_images": false,- 支持大小限制（默认 10MB）

       "output_format": "text"- 自动重命名避免冲突

     }'

### 2. Markdown 转换

# 高级抓取（包含图片和 Markdown）- 保持原文格式结构

curl -X POST "http://localhost:8000/scrape" \\- 图片自动转换为本地路径

     -H "Content-Type: application/json" \\- 支持代码块、引用等格式

     -d '{

       "url": "https://mp.weixin.qq.com/s/your-article-url",### 3. 反爬虫机制

       "save_images": true,- 使用 Playwright 模拟真实浏览器

       "output_format": "markdown",- 持久化浏览器上下文

       "force_save": true- 反自动化检测

     }'

```### 4. 缓存优化

- 基于 URL 和参数的智能缓存

### 查看存储内容- Redis 存储，支持过期时间

- 避免重复抓取

```python

import requests## 🛠️ 扩展开发



# 获取所有平台存储摘要### 添加新平台支持

response = requests.get("http://localhost:8000/storage/platforms")

print(response.json())1. 在 `app/providers/` 目录下创建新的 Provider 类

2. 继承 `BaseProvider` 并实现 `fetch_and_parse` 方法

# 获取特定平台内容3. 在 `app/config.py` 中添加平台配置

response = requests.get("http://localhost:8000/storage/platform/weixin_mp")4. 在 `app/main.py` 中注册 Provider

print(response.json())

```### 自定义抓取规则



## 📁 目录结构修改 `app/config.py` 中的 `PLATFORMS` 配置：



``````python

hotlist-crawler/PLATFORMS = {

├── app/                          # 应用核心代码    "your_platform": {

│   ├── __init__.py        "domains": ["example.com"],

│   ├── main.py                   # FastAPI应用主文件        "rules": {

│   ├── config.py                 # 配置管理            "title_selector": ".title",

│   ├── cache.py                  # 缓存系统            "content_selector": ".content",

│   ├── models.py                 # 数据模型        }

│   ├── storage.py                # 存储管理系统    }

│   └── providers/                # 平台提供者}

│       ├── __init__.py```

│       ├── base.py               # 基础提供者类

│       ├── weixin.py             # 微信公众号爬虫## 🚨 注意事项

│       ├── zhihu.py              # 知乎爬虫

│       └── weibo.py              # 微博爬虫1. **首次使用需要安装 Playwright 浏览器**：`playwright install chromium`

├── downloads/                    # 本地存储目录2. **Redis 是可选的**：

│   ├── weixin_mp/               # 微信公众号内容   - ✅ 有 Redis：使用持久化缓存，重启服务后缓存依然有效

│   ├── zhihu/                   # 知乎内容   - ⚠️ 无 Redis：使用内存缓存，重启服务后缓存会丢失

│   └── weibo/                   # 微博内容3. **微信公众号文章可能需要手动处理验证码**（在开发模式 headless=False 时）

├── chrome_user_data/            # 浏览器用户数据4. **图片下载需要足够的磁盘空间**

├── requirements.txt             # Python依赖5. **遵守网站的 robots.txt 和使用条款**

├── run_server.py               # 启动脚本

├── start_server.bat            # Windows启动脚本## 📈 性能优化建议

├── test_*.py                   # 测试脚本

└── README.md                   # 项目说明1. 在生产环境中设置 `PLAYWRIGHT_HEADLESS=true`

```2. 调整缓存过期时间以平衡性能和数据新鲜度

3. 使用适当的图片大小限制

## 📂 存储结构4. 考虑使用代理或分布式部署处理大量请求



每个平台的内容都会按以下结构存储：## 🔧 故障排除



```### 常见问题

downloads/

├── weixin_mp/                   # 微信公众号#### 1. Redis 连接错误

│   ├── <文章ID>_<标题>/```

│   │   ├── <标题>.txt          # 纯文本内容redis.exceptions.ConnectionError: Error connecting to localhost:6379

│   │   ├── <标题>.md           # Markdown格式```

│   │   ├── metadata.json       # 元数据信息

│   │   ├── images/             # 文章图片**解决方案：**

│   │   └── attachments/        # 附件文件- 系统会自动切换到内存缓存，继续正常工作

│   └── articles_index.json     # 文章索引- 如需 Redis 缓存，请按照上方说明安装并启动 Redis 服务

├── zhihu/                      # 知乎内容

│   ├── <问题ID>_<标题>/#### 2. Playwright 浏览器未安装

│   │   ├── <标题>.txt```

│   │   ├── <标题>.mdplaywright._impl._api_types.Error: Executable doesn't exist

│   │   ├── data.json           # 完整问题和回答数据```

│   │   ├── metadata.json

│   │   └── images/**解决方案：**

│   │       ├── question_images/ # 问题描述图片```bash

│   │       ├── answer_1_<作者>/ # 回答1的图片playwright install chromium

│   │       └── answer_2_<作者>/ # 回答2的图片```

└── weibo/                      # 微博内容

    ├── <搜索词>_<作者>_<时间>/#### 3. 微信公众号抓取失败

    │   ├── <标题>.txt- 某些文章可能有反爬虫保护

    │   ├── <标题>.md- 尝试设置 `PLAYWRIGHT_HEADLESS=false` 进行手动验证

    │   ├── post_data.json      # 完整帖子数据- 检查文章链接是否有效

    │   ├── metadata.json

    │   ├── images/             # 帖子图片#### 5. 微信公众号抓取失败

    │   └── attachments/        # 视频文件- 某些文章可能有反爬虫保护

```- 尝试设置 `PLAYWRIGHT_HEADLESS=false` 进行手动验证

- 检查文章链接是否有效

## 📊 API响应示例

#### 6. 图片下载失败

```json- 检查网络连接

{- 确保有足够的磁盘空间

  "platform": "weixin_mp",- 某些图片可能有防盗链保护

  "source_url": "https://mp.weixin.qq.com/s/example",

  "data": {### 日志信息说明

    "title": "文章标题",

    "author": "作者名称",**缓存相关：**

    "content": "纯文本内容...",- `✅ Redis 连接成功`：Redis 工作正常

    "markdown_content": "# 文章标题\\n**作者:** 作者名称\\n\\n文章内容...",- `⚠️ Redis 连接失败，使用内存缓存`：自动降级到内存缓存

    "images": [- `⚠️ Redis 读取/写入失败，切换到内存缓存`：运行时切换到内存缓存

      {

        "original_url": "https://example.com/image.jpg",**抓取相关：**

        "local_path": "./downloads/weixin_mp/article_123/images/image_1.jpg",- `🌐 正在访问页面`：开始抓取

        "alt_text": "图片描述"- `✅ 页面内容已加载`：Playwright 抓取成功

      }- `⚠️ Playwright 抓取失败`：正在尝试降级方案

    ],- `🔄 使用降级方案：基础 HTTP 抓取`：使用简化抓取模式

    "save_directory": "./downloads/weixin_mp/article_123"- `✅ 使用选择器 'xxx' 找到标题/作者/内容`：降级方案成功匹配

  },- `✅ 降级方案抓取成功`：降级方案完成

  "scrape_time": "2025-10-02T10:00:00+08:00"- `📄 Markdown 文件已保存到`：文件保存成功

}

```## � 快速测试



## 🔧 支持的平台运行测试脚本验证所有功能：

```bash

| 平台 | 域名 | 功能支持 | 特殊功能 |python test_api.py

|------|------|----------|----------|```

| 微信公众号 | mp.weixin.qq.com | ✅ 全功能 | 图片下载、Markdown转换、移动端适配 |

| 知乎问题 | www.zhihu.com/question | ✅ 全功能 | 自动登录、问题展开、多回答抓取 |测试脚本会验证：

| 知乎文章 | zhuanlan.zhihu.com | ✅ 全功能 | 文章内容、图片下载 |- API 健康检查

| 微博搜索 | s.weibo.com/weibo | ✅ 全功能 | 搜索结果、图片/视频下载、互动数据 |- 多个微信公众号链接的抓取

- 高级功能（图片下载 + Markdown）

## ⚙️ 配置选项- 错误处理和降级机制



### 环境变量配置（.env 文件）### 运行状态指示



```bash当您看到这些日志时：

# 服务器配置- `✅ 页面内容已加载` → Playwright 工作正常，功能完整

HOST=0.0.0.0- `🔄 使用降级方案` → 自动降级，功能受限但可用

PORT=8000- `✅ 降级方案抓取成功` → 降级方案正常工作

DEBUG=True- `⚠️ Redis 连接失败，使用内存缓存` → 缓存降级，正常工作



# Redis配置 (可选)## �🤝 贡献指南

REDIS_HOST=localhost

REDIS_PORT=6379欢迎提交 Issue 和 Pull Request 来改进项目！

REDIS_PASSWORD=

REDIS_DB=0---



# 存储配置**项目维护者**: 请根据实际情况更新文档内容
DOWNLOAD_DIR=./downloads
MAX_FILE_SIZE=100MB

# Playwright配置
PLAYWRIGHT_TIMEOUT=90000
BROWSER_HEADLESS=False
```

### 请求参数说明

| 参数 | 类型 | 必需 | 默认值 | 说明 |
|------|------|------|--------|------|
| url | string | ✅ | - | 要抓取的文章链接 |
| save_images | boolean | ❌ | true | 是否下载图片到本地 |
| output_format | string | ❌ | "markdown" | 输出格式："text", "markdown", "html" |
| force_save | boolean | ❌ | true | 是否强制保存所有内容到本地 |

## 🧪 测试

### 运行测试脚本

```bash
# 测试微信公众号功能
python test_weixin_integration.py

# 测试知乎功能  
python test_zhihu_integration.py

# 测试微博功能
python test_weibo_integration.py

# 测试存储功能
python test_storage.py
```

### 单元测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_providers/
```

## 🚨 注意事项

### 登录要求
- **微信公众号**: 无需登录，直接抓取
- **知乎**: 首次使用需要手动登录，登录状态会保持
- **微博**: 首次使用需要手动登录，登录状态会保持

### 使用限制
- 请合理使用，避免对目标网站造成过大压力
- 建议设置合适的请求间隔
- 遵守目标网站的robots.txt和服务条款
- 仅用于学习和个人使用

### 性能优化
- 使用Redis缓存可以显著提高性能
- 调整`PLAYWRIGHT_TIMEOUT`适应网络环境
- 对于大量抓取任务，建议使用队列系统

## 🐛 故障排除

### 常见问题

#### 1. Playwright浏览器未安装
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决方案：**
```bash
playwright install chromium
```

#### 2. Redis连接失败
```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**解决方案：**
- 系统会自动切换到内存缓存，继续正常工作
- 如需Redis缓存，请按照上方说明安装并启动Redis服务

#### 3. Windows系统Playwright异步错误
```
NotImplementedError: Task exception was never retrieved
```

**解决方案：**
- 已自动修复：系统会检测Windows环境并应用适当的事件循环策略
- 如果仍有问题，Playwright会自动降级到基础HTTP抓取

#### 4. 图片下载失败
- 检查网络连接和磁盘空间
- 某些图片可能有防盗链保护
- 检查图片大小是否超过限制

#### 5. 抓取内容为空
- 检查URL是否有效
- 某些页面可能需要登录
- 尝试设置`BROWSER_HEADLESS=False`手动处理

### 调试模式

```bash
# 启用调试模式
export DEBUG=True
python run_server.py

# 查看详细日志
tail -f logs/debug.log
```

## 📈 性能特点

- ⚡ **异步处理** - 使用异步架构提高并发性能
- 🔄 **智能重试** - 网络请求失败时自动重试
- 💾 **内存优化** - 流式下载大文件，避免内存溢出
- 🎯 **精确抓取** - 智能选择器确保内容准确提取
- 📦 **缓存优化** - 避免重复抓取，提升响应速度

## 🔄 更新日志

### v2.0.0 (2025-10-02)
- ✨ 新增微博搜索页面支持
- ✨ 新增知乎问题页面完整支持
- ✨ 实现统一存储管理系统
- 🚀 完整重构代码架构
- 📦 新增多格式输出支持

### v1.0.0 (初始版本)
- ✨ 基础微信公众号文章抓取
- 🔨 FastAPI框架搭建
- 💾 Redis缓存系统

## 🤝 贡献指南

欢迎提交Issues和Pull Requests！

### 开发环境设置

```bash
# Fork项目并克隆
git clone https://github.com/your-username/hotlist-crawler.git
cd hotlist-crawler

# 创建开发分支
git checkout -b feature/your-feature

# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest
```

### 提交规范
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关

### 添加新平台支持

1. 在 `app/providers/` 目录下创建新的 Provider 类
2. 继承 `BaseProvider` 并实现 `fetch_and_parse` 方法
3. 在 `app/config.py` 中添加平台配置
4. 在 `app/main.py` 中注册 Provider

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代化的Web框架
- [Playwright](https://playwright.dev/) - 浏览器自动化工具
- [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/) - HTML解析库
- [Pydantic](https://pydantic-docs.helpmanual.io/) - 数据验证库

## 📮 联系方式

- 项目地址: https://github.com/xfrrn/hotlist-crawler
- 问题反馈: https://github.com/xfrrn/hotlist-crawler/issues
- 作者: xfrrn

---

⭐ 如果这个项目对你有帮助，请给个Star支持一下！