# Hotlist Crawler 🔥

通用热榜内容爬虫，支持知乎、微博、微信公众号、小红书、抖音、B站等多个平台的内容抓取。

## ✨ 特性

- � **多平台支持**: 知乎、微博、微信、小红书、抖音、B站
- 🔍 **智能识别**: 自动识别URL所属平台
- 🎯 **关键词搜索**: 支持小红书关键词搜索
- 📸 **图片下载**: 自动下载并整理图片资源
- 📝 **多格式输出**: 支持文本和Markdown格式
- 🔐 **登录保持**: 一次登录，长期有效
- ⚡ **批量处理**: 支持多URL并发抓取
- 🛡️ **反检测**: 使用无头浏览器和随机User-Agent

## 📦 安装

### 环境要求

- Python 3.8+
- Node.js (用于小红书JavaScript签名)
- Google Chrome 或 Chromium

### 安装依赖

```bash
# 克隆项目
git clone https://github.com/Bra-Inno/hotlist-crawler.git
cd hotlist-crawler

# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium

# 安装Node.js依赖（用于小红书）
npm install
```

### 配置环境

1. 复制环境配置文件：
```bash
cp .env.example .env
```

2. 编辑 `.env` 文件，配置必要的参数：
```env
# Redis配置（可选，用于缓存）
REDIS_URL=redis://localhost:6379

# 浏览器配置
USER_DATA_DIR=./chrome_user_data
LOGIN_DATA_DIR=${USER_DATA_DIR}/login_data

# Playwright配置
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=90000

# 下载配置
DOWNLOAD_DIR=./downloads
MAX_IMAGE_SIZE=10485760
```

## � 快速开始

### 基本使用

```python
import hotlist_crawler

# 抓取单个内容
success = hotlist_crawler.fetch(
    url="https://www.zhihu.com/question/123456",
    destination="./output"
)

# 小红书关键词搜索
success = hotlist_crawler.fetch(
    url="xhs_keyword:美食",
    destination="./output",
    cookies=cookies  # 需要登录cookies
)
```

### 平台登录

```python
from hotlist_crawler import PlatformType

# 登录知乎
hotlist_crawler.login(PlatformType.ZHIHU)

# 检查登录状态
is_online = hotlist_crawler.is_online(PlatformType.ZHIHU)

# 获取所有平台登录状态
status = hotlist_crawler.get_all_online_status()
```

### 批量抓取

```python
import hotlist_crawler

urls = [
    "https://www.zhihu.com/question/123456",
    "https://weibo.com/123456/status/789",
    "https://mp.weixin.qq.com/s/abcdef"
]

results = hotlist_crawler.batch_fetch(urls, "./output")
```

## 📋 支持平台

| 平台 | URL格式 | 功能 | 登录要求 |
|------|---------|------|----------|
| **知乎** | `https://www.zhihu.com/...` | 问题、文章 | 可选 |
| **微博** | `https://weibo.com/...` | 搜索结果、帖子 | 可选 |
| **微信公众号** | `https://mp.weixin.qq.com/...` | 公众号文章 | 可选 |
| **小红书** | `xhs_keyword:关键词` | 关键词搜索 | **必需** |
| **抖音** | `https://www.douyin.com/...` | 视频信息 | 可选 |
| **B站** | `https://www.bilibili.com/...` | 视频信息 | 可选 |

## 🔐 Cookies管理

### 获取Cookies

对于需要登录的平台（如小红书），需要先获取cookies：

1. **自动获取**：
```python
# 打开浏览器登录
hotlist_crawler.login(PlatformType.XIAOHONGSHU)
```

2. **手动获取**：
   - 打开浏览器开发者工具
   - 访问目标网站并登录
   - 导出cookies保存为JSON文件

### Cookies格式

```json
[
  {
    "name": "sessionid",
    "value": "your_session_value",
    "domain": ".xiaohongshu.com",
    "path": "/",
    "expires": 1735689600
  }
]
```

## �️ API参考

### 核心函数

#### `fetch(url, destination, **kwargs) -> bool`

抓取单个URL内容

**参数：**
- `url` (str): 目标URL或关键词搜索
- `destination` (str): 保存目录
- `save_images` (bool): 是否下载图片，默认True
- `output_format` (str): 输出格式 'markdown'/'text'，默认'markdown'
- `cookies` (list): Cookies列表，默认None

**返回：** 抓取是否成功

#### `batch_fetch(urls, destination, **kwargs) -> dict`

批量抓取多个URL

**参数：**
- `urls` (list): URL列表
- `destination` (str): 保存目录
- `max_concurrent` (int): 最大并发数，默认3

**返回：** 包含成功/失败统计的字典

#### `login(platform, headless=False) -> bool`

登录指定平台

**参数：**
- `platform` (PlatformType): 平台类型
- `headless` (bool): 是否无头模式，默认False

#### `is_online(platform) -> bool`

检查登录状态

#### `get_platform_info(url) -> dict`

分析URL获取平台信息

### 平台类型枚举

```python
from hotlist_crawler import PlatformType

PlatformType.ZHIHU        # 知乎
PlatformType.WEIBO        # 微博
PlatformType.WEIXIN       # 微信公众号
PlatformType.XIAOHONGSHU  # 小红书
PlatformType.DOUYIN       # 抖音
PlatformType.BILIBILI     # B站
```

## 📁 输出结构

```
output/
├── zhihu_问题标题/
│   ├── content.md          # Markdown内容
│   ├── content.txt         # 纯文本内容
│   ├── images/             # 图片文件夹
│   │   ├── image_1.jpg
│   │   └── image_2.png
│   └── metadata.json       # 元数据
└── xhs_美食/
    ├── note_001/
    │   ├── content.md
    │   └── images/
    └── search_results.json # 搜索结果汇总
```

## ⚠️ 注意事项

### 小红书搜索功能

目前小红书搜索功能由于JavaScript签名算法问题暂时不可用：

```
⚠️ 搜索功能暂时不可用（JavaScript依赖问题）
💡 建议: 可以尝试更新小红书的JavaScript签名文件，或暂时使用其他功能
```

### 反爬虫限制

- 建议使用代理IP
- 控制请求频率
- 定期更新cookies

### 存储空间

图片下载可能消耗大量存储空间，建议定期清理。

## 🔧 故障排除

### 常见问题

1. **ImportError: No module named 'xxx'**
   ```bash
   pip install -r requirements.txt
   ```

2. **Playwright 浏览器未安装**
   ```bash
   playwright install chromium
   ```

3. **小红书搜索失败**
   - 检查cookies是否有效
   - 更新JavaScript签名文件
   - 查看日志中的具体错误信息

4. **网络超时**
   - 检查网络连接
   - 调整超时设置
   - 使用代理

### 日志调试

程序使用loguru进行日志记录，默认输出到控制台。如需更详细的日志：

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
python -m pytest

# 代码格式化
black .
isort .
```

## 📄 许可证

MIT License

## 📞 联系

- 项目主页: https://github.com/Bra-Inno/hotlist-crawler
- 问题反馈: https://github.com/Bra-Inno/hotlist-crawler/issues