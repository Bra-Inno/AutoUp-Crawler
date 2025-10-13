# hotlist_crawler package
"""
通用热榜内容爬虫包
支持知乎、微博、微信公众号等平台的内容抓取
"""

import sys
import os
import asyncio
from typing import Optional, List, Dict, Any

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
    from .core import scrape, scrape_zhihu, scrape_weibo, scrape_weixin, identify_platform
    from .auth import login, is_online, login_sync, get_all_online_status
    from .fetch import fetch, batch_fetch, validate_destination, list_supported_platforms, get_platform_info
    from .types import PlatformType, USER_DATA_DIR
    from .models import ScrapedDataItem
    
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
        identify_platform = core.identify_platform
        
        login = auth_module.login
        is_online = auth_module.is_online
        login_sync = auth_module.login_sync
        get_all_online_status = auth_module.get_all_online_status
        
        fetch = fetch_module.fetch
        batch_fetch = fetch_module.batch_fetch
        validate_destination = fetch_module.validate_destination
        list_supported_platforms = fetch_module.list_supported_platforms
        get_platform_info = fetch_module.get_platform_info
        
        PlatformType = types_module.PlatformType
        USER_DATA_DIR = types_module.USER_DATA_DIR
        
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
        identify_platform = _import_error_func
        login = _import_error_func
        is_online = _import_error_func
        login_sync = _import_error_func
        get_all_online_status = _import_error_func
        fetch = _import_error_func
        batch_fetch = _import_error_func
        validate_destination = _import_error_func
        list_supported_platforms = _import_error_func
        get_platform_info = _import_error_func
        PlatformType = None
        USER_DATA_DIR = os.path.join(os.getcwd(), "chrome_user_data")  # 固定保存到工作目录
        ScrapedDataItem = None

# 导出的公共接口
__all__ = [
    # 核心爬虫功能
    'scrape',           # 通用爬取函数
    'scrape_zhihu',     # 知乎专用爬取
    'scrape_weibo',     # 微博专用爬取
    'scrape_weixin',    # 微信专用爬取
    'identify_platform', # 平台识别
    
    # Fetch功能 - 符合API设计
    'fetch',            # 核心fetch函数 -> bool
    'batch_fetch',      # 批量抓取
    'validate_destination', # 验证目标目录
    'list_supported_platforms', # 获取支持的平台
    'get_platform_info', # 获取平台信息
    
    # 登录功能 - 符合API设计
    'login',            # 登录函数 -> bool
    'is_online',        # 检查在线状态 -> bool
    'login_sync',       # 同步版登录
    'get_all_online_status', # 获取所有平台状态
    
    # 类型和常量
    'PlatformType',     # 平台类型枚举
    'USER_DATA_DIR',    # 用户数据目录
    
    # 数据模型
    'ScrapedDataItem',  # 数据项模型
    
    # 便捷别名
    'zhihu',           # scrape_zhihu 的别名
    'weibo',           # scrape_weibo 的别名
    'weixin',          # scrape_weixin 的别名
    
    # 版本信息
    '__version__',
]

# 创建便捷别名
def _create_aliases():
    """创建便捷别名"""
    global zhihu, weibo, weixin
    if _import_success:
        zhihu = scrape_zhihu
        weibo = scrape_weibo
        weixin = scrape_weixin
    else:
        def _error_func(*args, **kwargs):
            raise ImportError(f"hotlist_crawler模块导入失败: {_import_error}")
        zhihu = _error_func
        weibo = _error_func
        weixin = _error_func

# 执行别名创建
_create_aliases()


def get_version() -> str:
    """获取包版本号"""
    return __version__


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
        "platform": sys.platform
    }


# 包初始化时的提示信息
if _import_success:
    # 成功导入时的静默模式，避免过多输出
    pass
else:
    print(f"⚠️ hotlist_crawler包导入时遇到问题: {_import_error}")
    print("💡 请确保所有依赖已正确安装，或查看文档获取帮助")


# 便捷的使用示例（在文档字符串中）
"""
使用示例:

# 基本爬取功能
import hotlist_crawler

# 自动识别平台并爬取
result = hotlist_crawler.scrape("https://www.zhihu.com/question/12345")

# 平台专用爬取
zhihu_data = hotlist_crawler.scrape_zhihu("https://www.zhihu.com/question/12345", max_answers=5)
weibo_data = hotlist_crawler.scrape_weibo("https://s.weibo.com/weibo?q=Python")

# 使用别名
result = hotlist_crawler.zhihu("https://www.zhihu.com/question/12345")

# 登录功能
import asyncio
login_result = asyncio.run(hotlist_crawler.login("zhihu"))

# 获取登录状态
cookies = hotlist_crawler.get_cookies("zhihu")
status = hotlist_crawler.get_login_status("zhihu")

# 健康检查
health = hotlist_crawler.health_check()
print(health)
"""