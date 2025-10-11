"""
平台类型定义和常量
"""
from enum import StrEnum
import os

class PlatformType(StrEnum):
    """支持的平台类型枚举"""
    ZHIHU = "zhihu"
    WEIBO = "weibo"
    XIAOHONGSHU = "xiaohongshu"
    WEIXIN = "weixin"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"

# 用户数据目录常量 - 固定保存到工作目录
USER_DATA_DIR: str = os.path.join(os.getcwd(), "chrome_user_data")

# 平台登录页面映射
PLATFORM_LOGIN_URLS = {
    PlatformType.ZHIHU: "https://www.zhihu.com/signin",
    PlatformType.WEIBO: "https://passport.weibo.cn/signin/login", 
    PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com/explore",
    PlatformType.WEIXIN: "https://mp.weixin.qq.com/",
    PlatformType.DOUYIN: "https://www.douyin.com/",
    PlatformType.BILIBILI: "https://passport.bilibili.com/login"
}