"""
hotlist_crawler providers 模块
各平台爬虫提供者
"""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环导入
    from app.providers.zhihu import ZhihuArticleProvider
    from app.providers.weibo import WeiboProvider
    from app.providers.weixin import WeixinMpProvider

__all__ = ['ZhihuArticleProvider', 'WeiboProvider', 'WeixinMpProvider']