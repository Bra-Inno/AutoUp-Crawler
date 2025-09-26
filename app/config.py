# app/config.py
from pydantic_settings import BaseSettings
from typing import Dict, Any

class Settings(BaseSettings):
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379"
    CACHE_EXPIRE_SECONDS: int = 60 * 10 # 缓存10分钟

    # 爬取目标配置
    # key 是平台的标识符，value 是包含URL和解析规则的字典
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "zhihu": {
            "url": "https://www.zhihu.com/hot",
            "rules": {
                "list_selector": "#TopstoryContent .HotList-list .HotItem",
                "rank_selector": ".HotItem-rank",
                "title_selector": ".HotItem-title",
                "url_selector": ".HotItem-content a",
                "hotness_selector": ".HotItem-metrics"
            }
        },
        "weibo": {
            "url": "https://s.weibo.com/top/summary/",
            # ... 其他规则
        }
    }

settings = Settings()