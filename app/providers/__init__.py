from app.providers.zhihu import ZhihuArticleProvider
from app.providers.weixin import WeixinMpProvider
from app.providers.weibo import WeiboProvider
from app.providers.bilibili import BilibiliVideoProvider

# 抖音Provider - 使用包装器版本（基于原始下载器）
try:
    from app.providers.douyin import DouyinVideoProvider
except ImportError:
    # 如果包装器导入失败，尝试使用原始实现
    from app.providers.douyin import DouyinVideoProvider

# 小红书Provider - 标准实现
from app.providers.xhs import XiaohongshuProvider

__all__ = [
    'ZhihuArticleProvider',
    'WeixinMpProvider', 
    'WeiboProvider',
    'BilibiliVideoProvider',
    'DouyinVideoProvider',
    'XiaohongshuProvider'
]
