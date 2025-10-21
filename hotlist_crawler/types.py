"""
平台类型定义和常量
"""

import os
from enum import StrEnum


class PlatformType(StrEnum):
    """支持的平台类型枚举"""

    ZHIHU = "zhihu"
    WEIBO = "weibo"
    XIAOHONGSHU = "xiaohongshu"
    WEIXIN = "weixin"
    DOUYIN = "douyin"
    BILIBILI = "bilibili"


USER_DATA_DIR: str = os.path.join(os.getcwd(), "chrome_user_data")
"""浏览器用户数据目录（默认是工作目录下的 chrome_user_data 文件夹）"""

PLATFORM_LOGIN_URLS = {
    PlatformType.ZHIHU: "https://www.zhihu.com/signin",
    PlatformType.WEIBO: "https://passport.weibo.cn/signin/login",
    PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com/explore",
    PlatformType.WEIXIN: "https://mp.weixin.qq.com/",
    PlatformType.DOUYIN: "https://www.douyin.com/",
    PlatformType.BILIBILI: "https://passport.bilibili.com/login",
}
"""各平台的登录页 URL"""

PLATFORM_CHECK_URLS = {
    PlatformType.ZHIHU: "https://www.zhihu.com/settings/profile",
    PlatformType.WEIBO: "https://weibo.com/set/index",
    PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com/explore/683fe17f0000000023017c6a?xsec_token=ABiqWIzMrzlIqlcQ8I5Ywig4rtiMtgvr2LQ5Jp02z1EDw=",
    PlatformType.BILIBILI: "https://account.bilibili.com/account/home",
    # 微信和抖音使用其他方法，详情见README.md
    # PlatformType.WEIXIN: None,
    # PlatformType.DOUYIN: None,
}
"""各平台的状态检测 URL"""
