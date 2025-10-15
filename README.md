# hotlist-crawler 接口简介

## 📦 导入方式
```python
import hotlist_crawler
from hotlist_crawler import PlatformType
```

---

## 🔐 认证接口

### 1. login(platform, headless=False) -> bool
- **功能：** 打开浏览器让用户登录指定平台，自动保存登录状态
- **参数：** platform（平台类型），headless（是否无头模式）
- **返回：** 登录是否成功

### 2. is_online(platform) -> bool
- **功能：** 检查指定平台是否有有效的登录状态
- **返回：** 是否在线

### 3. get_all_online_status() -> Dict
- **功能：** 获取所有平台的登录状态
- **返回：** 平台名称到登录状态的映射

---

## 📥 抓取接口

### 1. fetch(url, destination, save_images=True, output_format="markdown", max_answers=3) -> bool
- **功能：** 自动识别平台并抓取内容到指定目录（核心功能）
- **参数：** URL、目标目录、是否保存图片、输出格式、最大回答数
- **返回：** 抓取是否成功

### 2. batch_fetch(urls, destination, save_images=True, output_format="markdown", max_answers=3) -> Dict
- **功能：** 批量抓取多个URL
- **参数：** URL列表、目标目录、是否保存图片、输出格式、最大回答数
- **返回：** 详细的批量抓取结果统计

### 3. validate_destination(destination) -> bool
- **功能：** 验证目标目录是否有效可用
- **返回：** 目录是否有效

---

## 🎯 平台识别接口

### 1. get_platform_info(url) -> Dict
- **功能：** 分析URL并返回平台信息（平台类型、是否支持等）
- **返回：** 包含平台、支持状态、域名等信息的字典

### 2. list_supported_platforms() -> List[str]
- **功能：** 返回所有支持的平台列表
- **返回：** 平台名称列表 ['zhihu', 'weibo', 'weixin', 'xiaohongshu', 'douyin', 'bilibili']

> **✅ 所有平台通过 fetch() 统一接口爬取:**
> - **知乎** (zhihu): 问题、专栏文章 - `https://www.zhihu.com/...`
> - **微博** (weibo): 搜索结果 - `https://weibo.com/...`
> - **微信** (weixin): 公众号文章 - `https://mp.weixin.qq.com/...`
> - **B站** (bilibili): 视频信息 - `https://www.bilibili.com/...`
> - **小红书** (xiaohongshu): 关键词搜索 ⭐ - `xhs_keyword:关键词`
> - **抖音** (douyin): 视频 - `https://www.douyin.com/video/...`
> 

---

## 🏷️ 类型和常量

### 1. PlatformType (枚举)
- **功能：** 定义所有支持的平台类型
- **值：** ZHIHU, WEIBO, WEIXIN, XIAOHONGSHU, DOUYIN, BILIBILI

### 2. USER_DATA_DIR (字符串)
- **功能：** 浏览器用户数据的存储目录路径
- **值：** chrome_user_data目录的绝对路径

---

## 🧩 便捷别名

### 平台专用函数
- **zhihu()、weibo()、weixin()：** 对应平台的快捷抓取函数
- **等同于：** scrape_zhihu()、scrape_weibo()、scrape_weixin()

---

## 📋 接口总览

| 类别 | 主要接口 | 功能说明 |
|------|----------|----------|
| **认证** | login, is_online | 登录管理和状态检查 |
| **抓取** | fetch, batch_fetch | 单个和批量内容抓取 |
| **平台** | get_platform_info, list_supported_platforms | 平台识别和信息查询 |
| **工具** | validate_destination | 目录验证等辅助功能 |

---

## 🌟 核心特性

- **同步接口：** 所有函数都是同步的，无需async/await
- **自动识别：** 根据URL自动识别平台类型
- **登录保持：** 一次登录，长期有效
- **批量处理：** 支持多URL并发抓取
- **无头模式：** 抓取时默认无头运行，登录时显示界面
- **多格式输出：** 支持文本和Markdown格式
- **图片下载：** 自动下载并整理图片资源