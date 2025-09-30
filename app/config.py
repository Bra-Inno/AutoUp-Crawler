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
    
    # Playwright 配置
    PLAYWRIGHT_HEADLESS: bool = True  # 生产环境建议为True
    PLAYWRIGHT_TIMEOUT: int = 90000  # 页面加载超时时间（毫秒）

    # 平台识别与解析规则
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "zhihu": {
            "domains": ["www.zhihu.com", "zhuanlan.zhihu.com"],
            "rules": {
                "title_selector": ".Post-Main .Post-Header .Post-Title",
                "content_selector": ".Post-Main .Post-RichText",
            }
        },
        "weixin_mp": {
            "domains": ["mp.weixin.qq.com"],
            "rules": {
                "title_selector": "#activity-name",
                "content_selector": "#js_content",
            }
        }
    }

# 创建配置实例，供应用全局使用
settings = Settings()