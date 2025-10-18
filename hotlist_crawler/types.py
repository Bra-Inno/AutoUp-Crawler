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
    PlatformType.BILIBILI: "https://passport.bilibili.com/login",
}

# 平台登录状态检测URL映射
PLATFORM_CHECK_URLS = {
    PlatformType.ZHIHU: "https://www.zhihu.com/settings/profile",
    PlatformType.WEIBO: "https://weibo.com/set/index",
    PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com/explore/683fe17f0000000023017c6a?xsec_token=ABiqWIzMrzlIqlcQ8I5Ywig4rtiMtgvr2LQ5Jp02z1EDw=",
    PlatformType.BILIBILI: "https://account.bilibili.com/account/home",
    # 微信和抖音暂不实现
    # PlatformType.WEIXIN: None,
    # PlatformType.DOUYIN: None,
}
