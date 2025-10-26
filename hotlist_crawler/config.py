from typing import Dict, Any
from pathlib import Path


class CrawlerConfig:
    def __init__(
        self,
        download_dir: str = "./temp",
        chrome_user_data_dir: str = "./chrome_user_data",
        max_image_size: int = 10485760,
        playwright_headless: bool = False,
        playwright_timeout: int = 30000,
        user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ):
        self.download_dir = download_dir
        self.chrome_user_data_dir = chrome_user_data_dir
        self.login_data_dir = str(Path(chrome_user_data_dir) / "login_data")
        self.max_image_size = max_image_size
        self.playwright_headless = playwright_headless
        self.playwright_timeout = playwright_timeout
        self.user_agent = user_agent

        self.platforms: Dict[str, Dict[str, Any]] = {
            "zhihu": {
                "domains": ["www.zhihu.com", "zhuanlan.zhihu.com"],
                "rules": {
                    "title_selector": ".Post-Main .Post-Header .Post-Title",
                    "content_selector": ".Post-Main .Post-RichText",
                },
            },
            "weixin": {
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
