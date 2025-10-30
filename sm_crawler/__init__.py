"""
通用热榜内容爬虫包
支持知乎、微博、微信公众号等平台的内容抓取
"""

import sys
import os
import asyncio
from typing import List, Dict, Any
from loguru import logger

# 版本信息
__version__ = "2.0.0"
__author__ = "hotlist-crawler"
__email__ = ""
__description__ = "通用热榜内容爬虫包，支持知乎、微博、微信公众号等平台的内容抓取"

# Windows 系统异步支持
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 添加当前目录到Python路径，确保可以导入模块
_current_dir = os.path.dirname(os.path.abspath(__file__))
_parent_dir = os.path.dirname(_current_dir)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

try:
    from .crawler import Crawler
    from .config import CrawlerConfig
    from .types import PlatformType
    from .models import ScrapedDataItem

    _import_success = True
    _import_error = None

except ImportError as e:
    try:
        import sm_crawler.crawler as crawler_module
        import sm_crawler.config as config_module
        import sm_crawler.models as models
        import sm_crawler.types as types_module

        Crawler = crawler_module.Crawler
        CrawlerConfig = config_module.CrawlerConfig
        PlatformType = types_module.PlatformType
        ScrapedDataItem = models.ScrapedDataItem

        _import_success = True
        _import_error = None

    except ImportError as e2:
        _import_success = False
        _import_error = str(e2)

        def _import_error_func(*args, **kwargs):
            raise ImportError(f"hotlist_crawler模块导入失败: {_import_error}")

        Crawler = _import_error_func
        CrawlerConfig = _import_error_func
        PlatformType = None
        ScrapedDataItem = None

__all__ = [
    "Crawler",
    "CrawlerConfig",
    "PlatformType",
    "ScrapedDataItem",
    "__version__",
]


def get_supported_platforms() -> List[str]:
    """获取支持的平台列表"""
    return ["zhihu", "weibo", "weixin_mp", "xiaohongshu", "douyin", "bilibili"]


def health_check() -> Dict[str, Any]:
    """健康检查，返回包的状态信息"""
    return {
        "package": "hotlist_crawler",
        "version": __version__,
        "import_success": _import_success,
        "import_error": _import_error,
        "supported_platforms": get_supported_platforms(),
        "python_version": sys.version,
        "platform": sys.platform,
    }


# 包初始化时的提示信息
if not _import_success:
    logger.warning(f"⚠️ hotlist_crawler包导入时遇到问题: {_import_error}")
    logger.info("💡 请确保所有依赖已正确安装，或查看文档获取帮助")
