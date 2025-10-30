"""
平台类型定义和常量
"""

from enum import StrEnum


class PlatformType(StrEnum):
    """支持的平台类型枚举"""

    ZHIHU = "zhihu"
    WEIBO = "weibo"
    XIAOHONGSHU = "xiaohongshu"
    WEIXIN = "weixin"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"
