from bs4 import BeautifulSoup
from app.providers.base import BaseProvider
from app.models import ScrapedDataItem
from app.storage import storage_manager
from typing import Any

class ZhihuArticleProvider(BaseProvider):
    """
    知乎文章页面的爬虫实现
    """
    def __init__(self, url: str, rules: dict, save_images: bool = True, output_format: str = "markdown", 
                 force_save: bool = True):
        super().__init__(url, rules, save_images, output_format, force_save, "zhihu")
    
    async def fetch_and_parse(self) -> Any:
        html = await self._get_html()
        soup = BeautifulSoup(html, 'lxml')

        try:
            title_element = soup.select_one(self.rules["title_selector"])
            if not title_element:
                return None
            title = title_element.text.strip()
            
            content_element = soup.select_one(self.rules["content_selector"])
            if content_element:
                # 清理内容中的非文本元素，例如 "收起" 按钮
                for element in content_element.find_all("button"):
                    element.decompose()
                content = content_element.text.strip()
            else:
                content = ""

            # 创建存储结构
            storage_info = None
            if self.force_save:
                storage_info = storage_manager.create_article_storage(
                    platform=self.platform_name,
                    title=title,
                    url=self.url
                )
                
                # 保存内容
                storage_manager.save_text_content(storage_info, content)
                
                # 如果是markdown格式，也保存markdown
                if self.output_format == "markdown":
                    storage_manager.save_markdown_content(storage_info, content, title)
                
                # 保存文章索引
                storage_manager.save_article_index(storage_info, content[:200])

            return ScrapedDataItem(
                title=title, 
                content=content,
                author=None,
                markdown_content=content if self.output_format == "markdown" else None,
                save_directory=storage_info["article_dir"] if storage_info else None
            )
        
        except AttributeError:
            # 如果选择器找不到元素，会触发 AttributeError，说明解析失败
            return None