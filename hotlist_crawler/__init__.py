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
    from .auth import login, is_online, get_all_online_status
    from .fetch import fetch
    from .types import PlatformType
    from .models import ScrapedDataItem

    # 成功导入标志
    _import_success = True
    _import_error = None

except ImportError as e:
    # 如果相对导入失败，尝试绝对导入
    try:
        import hotlist_crawler.auth as auth_module
        import hotlist_crawler.fetch as fetch_module
        import hotlist_crawler.models as models
        import hotlist_crawler.types as types_module

        login = auth_module.login
        is_online = auth_module.is_online
        get_all_online_status = auth_module.get_all_online_status

        fetch = fetch_module.fetch

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
        login = _import_error_func
        is_online = _import_error_func
        get_all_online_status = _import_error_func
        fetch = _import_error_func
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
    # Fetch功能 - 符合API设计
    "fetch",  # 核心fetch函数 -> bool
    # 登录功能 - 符合API设计
    "login",  # 登录函数 -> bool
    "is_online",  # 检查在线状态 -> bool
    "get_all_online_status",  # 获取所有平台状态
    # 类型和常量
    "PlatformType",  # 平台类型枚举
    # 数据模型
    "ScrapedDataItem",  # 数据项模型
    # 版本信息
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
