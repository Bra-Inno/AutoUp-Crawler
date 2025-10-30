from abc import ABC, abstractmethod
from typing import Any

from ..storage import StorageManager


class BaseProvider(ABC):
    """
    所有爬虫 Provider 的抽象基类
    """

    def __init__(
        self,
        url: str,
        config: Any,
        save_images: bool = True,
        output_format: str = "markdown",
        force_save: bool = True,
        platform_name: str = "unknown",
    ):
        self.url = url
        self.config = config
        self.save_images = save_images
        self.output_format = output_format
        self.force_save = force_save
        self.platform_name = platform_name
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
        }

        # 实例化 StorageManager（如果 config 存在）
        self.storage = StorageManager(config) if config else None

    @abstractmethod
    async def fetch_and_parse(self) -> Any:
        """
        异步获取和解析指定 URL 的内容。
        每个子类必须实现此方法。
        """
        raise NotImplementedError()
