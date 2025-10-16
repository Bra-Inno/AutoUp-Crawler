from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any

class Settings(BaseSettings):
    """
    应用配置模型
    """
    # 从 .env 文件加载配置
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_EXPIRE_SECONDS: int = 60 * 60  # 缓存1小时
    
    # 下载配置
    DOWNLOAD_DIR: str = "./downloads"  # 默认下载目录
    MAX_IMAGE_SIZE: int = 10 * 1024 * 1024  # 最大图片大小 10MB
    
    # 浏览器数据目录配置
    USER_DATA_DIR: str = "./chrome_user_data"  # Chrome浏览器用户数据目录
    LOGIN_DATA_DIR: str = "USER_DATA_DIR/login_data"  # 登录数据存储目录
    
    # Playwright 配置
    PLAYWRIGHT_HEADLESS: bool = True  # 生产环境建议为True
    PLAYWRIGHT_TIMEOUT: int = 90000  # 页面加载超时时间（毫秒）
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"  # 默认User-Agent

    # 平台识别与解析规则
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "zhihu": {
            "domains": ["www.zhihu.com", "zhuanlan.zhihu.com"],
            "rules": {
                "title_selector": ".Post-Main .Post-Header .Post-Title",
                "content_selector": ".Post-Main .Post-RichText",
            }
        },
        "weixin": {  # 改为weixin以匹配PlatformType
            "domains": ["mp.weixin.qq.com"],
            "rules": {
                "title_selector": "#activity-name",
                "content_selector": "#js_content",
            }
        },
        "weibo": {
            "domains": ["s.weibo.com", "weibo.com"],
            "rules": {
                "title_selector": ".card-wrap .info .name",
                "content_selector": ".card-wrap .txt",
            }
        },
        "xiaohongshu": {
            "domains": ["www.xiaohongshu.com", "xhslink.com"],
            "rules": {
                "title_selector": ".note-item .title",
                "content_selector": ".note-item .content",
            }
        },
        "douyin": {
            "domains": ["www.douyin.com", "v.douyin.com"],
            "rules": {
                "title_selector": ".video-info .title",
                "content_selector": ".video-info .desc",
            }
        },
        "bilibili": {
            "domains": ["www.bilibili.com", "b23.tv"],
            "rules": {
                "title_selector": ".video-title",
                "content_selector": ".video-desc",
            }
        }
    }

# 创建配置实例，供应用全局使用
settings = Settings()