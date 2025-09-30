# 热榜爬虫项目 - 使用指南

## 🎯 项目简介

这是一个基于 FastAPI 的通用内容抓取 API 服务，现已整合了强大的微信公众号文章抓取功能。项目支持：

- **智能平台识别**：自动识别知乎、微信公众号等平台
- **反爬虫处理**：使用 Playwright 处理 JavaScript 渲染和反爬虫机制
- **图片下载**：自动下载文章中的图片到本地
- **Markdown 转换**：将文章转#### 3. Playwright 浏览器未安装
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决方案：**
```bash
playwright install chromium
```

#### 4. Windows 系统 Playwright 异步错误
```
NotImplementedError: Task exception was never retrieved
```

**解决方案：**
- 已自动修复：系统会检测 Windows 环境并应用适当的事件循环策略
- 如果仍有问题，Playwright 会自动降级到基础 HTTP 抓取
- 降级模式下功能有限（无图片下载、无 Markdown）wn 格式
- **缓存优化**：Redis 缓存避免重复抓取

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium
```

### 2. Redis 配置（可选）

#### 选项 A：使用 Redis（推荐，用于生产环境）

**Windows 用户：**
```bash
# 使用 Chocolatey 安装 Redis
choco install redis-64

# 或者下载 Redis for Windows
# 访问：https://github.com/microsoftarchive/redis/releases

# 启动 Redis 服务
redis-server

# 在新的终端窗口测试连接
redis-cli ping
```

**其他系统：**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis-server

# macOS
brew install redis
brew services start redis

# 测试连接
redis-cli ping
```

#### 选项 B：无 Redis 模式（开发/测试）

如果不安装 Redis，系统会自动使用内存缓存，无需额外配置。

### 3. 启动 API 服务

```bash
uvicorn app.main:app --reload
```

### 4. 访问 API 文档

打开浏览器访问 `http://localhost:8000/docs` 查看 API 文档

## 📋 API 使用示例

### 基础抓取（仅文本）

```bash
curl -X POST "http://localhost:8000/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://mp.weixin.qq.com/s/your-article-url",
       "save_images": false,
       "output_format": "text"
     }'
```

### 高级抓取（包含图片和 Markdown）

```bash
curl -X POST "http://localhost:8000/scrape" \
     -H "Content-Type: application/json" \
     -d '{
       "url": "https://mp.weixin.qq.com/s/your-article-url",
       "save_images": true,
       "output_format": "markdown"
     }'
```

## 📊 响应示例

```json
{
  "platform": "weixin_mp",
  "source_url": "https://mp.weixin.qq.com/s/example",
  "data": {
    "title": "文章标题",
    "author": "作者名称",
    "content": "纯文本内容...",
    "markdown_content": "# 文章标题\n**作者:** 作者名称\n\n文章内容...",
    "images": [
      {
        "original_url": "https://example.com/image.jpg",
        "local_path": "image_1.jpg",
        "alt_text": "图片描述"
      }
    ],
    "save_directory": "./downloads/文章标题"
  },
  "scrape_time": "2025-09-30T10:00:00+08:00"
}
```

## ⚙️ 配置选项

### 环境变量配置（.env 文件）

```bash
# Redis 配置
REDIS_URL=redis://localhost:6379
CACHE_EXPIRE_SECONDS=3600

# 下载配置
DOWNLOAD_DIR=./downloads
MAX_IMAGE_SIZE=10485760  # 10MB

# Playwright 配置
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=90000
```

## 🔧 支持的平台

| 平台 | 域名 | 功能支持 |
|------|------|----------|
| 知乎 | zhuanlan.zhihu.com, www.zhihu.com | 基础文本抓取 |
| 微信公众号 | mp.weixin.qq.com | 全功能（图片、Markdown） |

## 🎨 新功能特点

### 1. 智能图片处理
- 自动下载文章中的图片
- 支持大小限制（默认 10MB）
- 自动重命名避免冲突

### 2. Markdown 转换
- 保持原文格式结构
- 图片自动转换为本地路径
- 支持代码块、引用等格式

### 3. 反爬虫机制
- 使用 Playwright 模拟真实浏览器
- 持久化浏览器上下文
- 反自动化检测

### 4. 缓存优化
- 基于 URL 和参数的智能缓存
- Redis 存储，支持过期时间
- 避免重复抓取

## 🛠️ 扩展开发

### 添加新平台支持

1. 在 `app/providers/` 目录下创建新的 Provider 类
2. 继承 `BaseProvider` 并实现 `fetch_and_parse` 方法
3. 在 `app/config.py` 中添加平台配置
4. 在 `app/main.py` 中注册 Provider

### 自定义抓取规则

修改 `app/config.py` 中的 `PLATFORMS` 配置：

```python
PLATFORMS = {
    "your_platform": {
        "domains": ["example.com"],
        "rules": {
            "title_selector": ".title",
            "content_selector": ".content",
        }
    }
}
```

## 🚨 注意事项

1. **首次使用需要安装 Playwright 浏览器**：`playwright install chromium`
2. **Redis 是可选的**：
   - ✅ 有 Redis：使用持久化缓存，重启服务后缓存依然有效
   - ⚠️ 无 Redis：使用内存缓存，重启服务后缓存会丢失
3. **微信公众号文章可能需要手动处理验证码**（在开发模式 headless=False 时）
4. **图片下载需要足够的磁盘空间**
5. **遵守网站的 robots.txt 和使用条款**

## 📈 性能优化建议

1. 在生产环境中设置 `PLAYWRIGHT_HEADLESS=true`
2. 调整缓存过期时间以平衡性能和数据新鲜度
3. 使用适当的图片大小限制
4. 考虑使用代理或分布式部署处理大量请求

## 🔧 故障排除

### 常见问题

#### 1. Redis 连接错误
```
redis.exceptions.ConnectionError: Error connecting to localhost:6379
```

**解决方案：**
- 系统会自动切换到内存缓存，继续正常工作
- 如需 Redis 缓存，请按照上方说明安装并启动 Redis 服务

#### 2. Playwright 浏览器未安装
```
playwright._impl._api_types.Error: Executable doesn't exist
```

**解决方案：**
```bash
playwright install chromium
```

#### 3. 微信公众号抓取失败
- 某些文章可能有反爬虫保护
- 尝试设置 `PLAYWRIGHT_HEADLESS=false` 进行手动验证
- 检查文章链接是否有效

#### 5. 微信公众号抓取失败
- 某些文章可能有反爬虫保护
- 尝试设置 `PLAYWRIGHT_HEADLESS=false` 进行手动验证
- 检查文章链接是否有效

#### 6. 图片下载失败
- 检查网络连接
- 确保有足够的磁盘空间
- 某些图片可能有防盗链保护

### 日志信息说明

**缓存相关：**
- `✅ Redis 连接成功`：Redis 工作正常
- `⚠️ Redis 连接失败，使用内存缓存`：自动降级到内存缓存
- `⚠️ Redis 读取/写入失败，切换到内存缓存`：运行时切换到内存缓存

**抓取相关：**
- `🌐 正在访问页面`：开始抓取
- `✅ 页面内容已加载`：Playwright 抓取成功
- `⚠️ Playwright 抓取失败`：正在尝试降级方案
- `🔄 使用降级方案：基础 HTTP 抓取`：使用简化抓取模式
- `✅ 使用选择器 'xxx' 找到标题/作者/内容`：降级方案成功匹配
- `✅ 降级方案抓取成功`：降级方案完成
- `📄 Markdown 文件已保存到`：文件保存成功

## � 快速测试

运行测试脚本验证所有功能：
```bash
python test_api.py
```

测试脚本会验证：
- API 健康检查
- 多个微信公众号链接的抓取
- 高级功能（图片下载 + Markdown）
- 错误处理和降级机制

### 运行状态指示

当您看到这些日志时：
- `✅ 页面内容已加载` → Playwright 工作正常，功能完整
- `🔄 使用降级方案` → 自动降级，功能受限但可用
- `✅ 降级方案抓取成功` → 降级方案正常工作
- `⚠️ Redis 连接失败，使用内存缓存` → 缓存降级，正常工作

## �🤝 贡献指南

欢迎提交 Issue 和 Pull Request 来改进项目！

---

**项目维护者**: 请根据实际情况更新文档内容