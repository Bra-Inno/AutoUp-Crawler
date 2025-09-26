# app/providers/base.py
from abc import ABC, abstractmethod
from typing import List
from app.models import HotListItem
import httpx

class BaseProvider(ABC):
    def __init__(self, platform_name: str, config: dict):
        self.platform_name = platform_name
        self.url = config.get("url")
        self.rules = config.get("rules")
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    @abstractmethod
    async def fetch_and_parse(self) -> List[HotListItem]:
        """
        异步获取和解析网页内容，返回热榜数据列表
        """
        pass

    async def _get_html(self) -> str:
        async with httpx.AsyncClient() as client:
            response = await client.get(self.url, headers=self.headers)
            response.raise_for_status() # 如果请求失败则抛出异常
            return response.text

# app/providers/zhihu.py
from bs4 import BeautifulSoup
from .base import BaseProvider
from app.models import HotListItem
from typing import List

class ZhihuProvider(BaseProvider):
    async def fetch_and_parse(self) -> List[HotListItem]:
        html = await self._get_html()
        soup = BeautifulSoup(html, 'html.parser')
        
        items = []
        hot_list = soup.select(self.rules["list_selector"])
        
        for item_soup in hot_list:
            try:
                rank = int(item_soup.select_one(self.rules["rank_selector"]).text.strip())
                title = item_soup.select_one(self.rules["title_selector"]).text.strip()
                url = item_soup.select_one(self.rules["url_selector"])['href']
                hotness = item_soup.select_one(self.rules["hotness_selector"]).text.strip()
                
                items.append(HotListItem(rank=rank, title=title, url=url, hotness=hotness))
            except (AttributeError, ValueError, TypeError) as e:
                # 某些项可能不规范，或者广告，跳过
                print(f"解析 {self.platform_name} 的一项时出错: {e}")
                continue
        
        return items