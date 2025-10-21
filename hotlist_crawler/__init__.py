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
    # 导入核心功能
    from .core import (
        scrape,
        scrape_zhihu,
        scrape_weibo,
        scrape_weixin,
        scrape_bilibili,
        scrape_douyin,
        identify_platform,
    )
    from .auth import login, is_online, get_all_online_status
    from .fetch import (
        fetch,
        batch_fetch,
        validate_destination,
        list_supported_platforms,
        get_platform_info,
    )
    from .types import PlatformType
    from .models import ScrapedDataItem

    # 导入配置管理功能
    from .config import (
        set_user_data_dir,
        set_user_agent,
        get_user_data_dir,
        get_user_agent,
        get_login_data_dir,
        set_playwright_headless,
        set_download_dir,
        get_all_config,
        print_config,
    )

    # 成功导入标志
    _import_success = True
    _import_error = None

except ImportError as e:
    # 如果相对导入失败，尝试绝对导入
    try:
        import hotlist_crawler.core as core
        import hotlist_crawler.auth as auth_module
        import hotlist_crawler.fetch as fetch_module
        import hotlist_crawler.models as models
        import hotlist_crawler.types as types_module

        # 导入函数
        scrape = core.scrape
        scrape_zhihu = core.scrape_zhihu
        scrape_weibo = core.scrape_weibo
        scrape_weixin = core.scrape_weixin
        scrape_bilibili = core.scrape_bilibili
        scrape_douyin = core.scrape_douyin
        identify_platform = core.identify_platform

        login = auth_module.login
        is_online = auth_module.is_online
        get_all_online_status = auth_module.get_all_online_status

        fetch = fetch_module.fetch
        batch_fetch = fetch_module.batch_fetch
        validate_destination = fetch_module.validate_destination
        list_supported_platforms = fetch_module.list_supported_platforms
        get_platform_info = fetch_module.get_platform_info

        PlatformType = types_module.PlatformType

        ScrapedDataItem = models.ScrapedDataItem

        _import_success = True
        _import_error = None

    except ImportError as e2:
        # 导入失败，记录错误但不崩溃
        _import_success = False
        _import_error = str(e2)

        # 提供错误提示函数
        def _import_error_func(*args, **kwargs):
            raise ImportError(f"hotlist_crawler模块导入失败: {_import_error}")

        # 用错误函数替代主要功能
        scrape = _import_error_func
        scrape_zhihu = _import_error_func
        scrape_weibo = _import_error_func
        scrape_weixin = _import_error_func
        scrape_bilibili = _import_error_func
        scrape_douyin = _import_error_func
        identify_platform = _import_error_func
        login = _import_error_func
        is_online = _import_error_func
        get_all_online_status = _import_error_func
        fetch = _import_error_func
        batch_fetch = _import_error_func
        validate_destination = _import_error_func
        list_supported_platforms = _import_error_func
        get_platform_info = _import_error_func

        # 配置管理函数
        set_user_data_dir = _import_error_func
        set_user_agent = _import_error_func
        set_login_data_dir = _import_error_func
        get_user_data_dir = _import_error_func
        get_user_agent = _import_error_func
        get_login_data_dir = _import_error_func
        set_playwright_headless = _import_error_func
        set_download_dir = _import_error_func
        get_all_config = _import_error_func
        print_config = _import_error_func

        PlatformType = None
        ScrapedDataItem = None

# 导出的公共接口
__all__ = [
    # 核心爬虫功能
    "scrape",  # 通用爬取函数
    "scrape_zhihu",  # 知乎专用爬取
    "scrape_weibo",  # 微博专用爬取
    "scrape_weixin",  # 微信专用爬取
    "scrape_bilibili",  # B站专用爬取
    "scrape_douyin",  # 抖音专用爬取
    "identify_platform",  # 平台识别
    # Fetch功能 - 符合API设计
    "fetch",  # 核心fetch函数 -> bool
    "batch_fetch",  # 批量抓取
    "validate_destination",  # 验证目标目录
    "list_supported_platforms",  # 获取支持的平台
    "get_platform_info",  # 获取平台信息
    # 登录功能 - 符合API设计
    "login",  # 登录函数 -> bool
    "is_online",  # 检查在线状态 -> bool
    "get_all_online_status",  # 获取所有平台状态
    # 配置管理功能
    "set_user_data_dir",  # 设置浏览器数据目录
    "set_user_agent",  # 设置User-Agent
    "set_login_data_dir",  # 设置登录数据目录
    "get_user_data_dir",  # 获取浏览器数据目录
    "get_user_agent",  # 获取User-Agent
    "get_login_data_dir",  # 获取登录数据目录
    "set_playwright_headless",  # 设置无头模式
    "set_download_dir",  # 设置下载目录
    "get_all_config",  # 获取所有配置
    "print_config",  # 打印配置信息
    # 类型和常量
    "PlatformType",  # 平台类型枚举
    # 数据模型
    "ScrapedDataItem",  # 数据项模型
    # 便捷别名
    "zhihu",
    "weibo",
    "weixin",
    "bilibili",
    "douyin",
    # 版本信息
    "__version__",
]


if _import_success:
    zhihu = scrape_zhihu
    weibo = scrape_weibo
    weixin = scrape_weixin
    bilibili = scrape_bilibili
    douyin = scrape_douyin
else:

    def _error_func(*args, **kwargs):
        raise ImportError(f"hotlist_crawler模块导入失败: {_import_error}")

    zhihu = _error_func
    weibo = _error_func
    weixin = _error_func
    bilibili = _error_func
    douyin = _error_func


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
