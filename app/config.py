from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any


class Settings(BaseSettings):
    """
    应用配置模型
    所有配置从 .env 文件加载
    """

    # 从 .env 文件加载配置
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="allow"
    )  # 允许额外的字段

    # Redis 配置
    REDIS_URL: str
    CACHE_EXPIRE_SECONDS: int

    # 下载配置
    DOWNLOAD_DIR: str
    MAX_IMAGE_SIZE: int

    # 浏览器数据目录配置
    USER_DATA_DIR: str
    LOGIN_DATA_DIR: str

    # Playwright 配置
    PLAYWRIGHT_HEADLESS: bool
    PLAYWRIGHT_TIMEOUT: int
    USER_AGENT: str

    # 平台识别与解析规则
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "zhihu": {
            "domains": ["www.zhihu.com", "zhuanlan.zhihu.com"],
            "rules": {
                "title_selector": ".Post-Main .Post-Header .Post-Title",
                "content_selector": ".Post-Main .Post-RichText",
            },
        },
        "weixin": {  # 改为weixin以匹配PlatformType
            "domains": ["mp.weixin.qq.com"],
            "rules": {
                "title_selector": "#activity-name",
                "content_selector": "#js_content",
            },
        },
        "weibo": {
            "domains": ["s.weibo.com", "weibo.com"],
            "rules": {
                "title_selector": ".card-wrap .info .name",
                "content_selector": ".card-wrap .txt",
            },
        },
        "xiaohongshu": {
            "domains": ["www.xiaohongshu.com", "xhslink.com"],
            "rules": {
                "title_selector": ".note-item .title",
                "content_selector": ".note-item .content",
            },
        },
        "douyin": {
            "domains": ["www.douyin.com", "v.douyin.com"],
            "rules": {
                "title_selector": ".video-info .title",
                "content_selector": ".video-info .desc",
            },
        },
        "bilibili": {
            "domains": ["www.bilibili.com", "b23.tv"],
            "rules": {
                "title_selector": ".video-title",
                "content_selector": ".video-desc",
            },
        },
    }


# 创建配置实例，供应用全局使用
settings = Settings()
