import os
import asyncio
import httpx
import concurrent.futures
from loguru import logger
from typing import Any, Optional
from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from playwright.sync_api import sync_playwright

from ..providers.base import BaseProvider
from ..models import ScrapedDataItem, ImageInfo
from ..utils.file_utils import get_file_extension, get_random_user_agent


class WeixinMpProvider(BaseProvider):
    """
    微信公众号文章页面的爬虫实现
    使用 Playwright 处理 JavaScript 渲染和反爬虫机制
    支持图片下载和 Markdown 转换
    """

    MAX_IMAGE_SIZE = 10485760  # 10MB
    HTTP_TIMEOUT = 30  # s
    PLAYWRIGHT_TIMEOUT = 60000  # ms

    def __init__(
        self,
        url: str,
        config: Any,
        output_format: str = "markdown",
        cookies: list | None = None,
        force_save: bool = True,
    ):
        super().__init__(url, config, output_format, force_save, "weixin")
        self.storage_info = None
        self.img_counter = 0
        self.cookies = cookies

    def _download_image_content(self, img_url: str) -> Optional[bytes]:
        """
        下载图片内容（统一的下载逻辑）

        Args:
            img_url: 图片URL

        Returns:
            图片二进制内容，或None（如果下载失败/文件过大）
        """
        if not img_url or not img_url.startswith("http"):
            return None

        try:
            response = httpx.get(img_url, timeout=self.HTTP_TIMEOUT)
            response.raise_for_status()

            content_length = response.headers.get("Content-Length")
            if content_length and int(content_length) > self.MAX_IMAGE_SIZE:
                logger.warning(f"  - 图片过大，跳过: {img_url}")
                return None

            return response.content

        except Exception as e:
            logger.error(f"  - 下载图片失败: {img_url}, 错误: {e}")
            return None

    def download_image(self, img_url: str, save_dir: str) -> Optional[str]:
        """
        下载图片并保存到指定目录

        Args:
            img_url: 图片URL
            save_dir: 保存目录

        Returns:
            保存的文件名（含扩展名），或None
        """
        content = self._download_image_content(img_url)
        if content is None:
            return None

        try:
            self.img_counter += 1
            img_filename = f"image_{self.img_counter}"
            ext = get_file_extension(content=content)

            img_save_path = os.path.join(save_dir, f"{img_filename}.{ext}")
            with open(img_save_path, "wb") as f:
                f.write(content)

            logger.debug(f"  - 图片已下载: {img_filename}.{ext}")
            return f"{img_filename}.{ext}"

        except Exception as e:
            logger.error(f"  - 保存图片失败: {img_url}, 错误: {e}")
            return None

    def download_image_with_storage(self, img_url: str, storage_info: dict, alt_text: str = "") -> Optional[str]:
        """
        下载图片并通过存储管理器保存

        Args:
            img_url: 图片URL
            storage_info: 存储信息字典
            alt_text: 图片的alt文本

        Returns:
            本地路径，或None
        """
        content = self._download_image_content(img_url)
        if content is None:
            return None

        try:
            image_info = self.storage.save_image(storage_info, content, img_url, alt_text, self.img_counter + 1)

            self.img_counter += 1
            return image_info["local_path"]

        except Exception as e:
            logger.error(f"  - 通过存储管理器保存图片失败: {img_url}, 错误: {e}")
            return None

    def convert_tag_to_markdown(self, tag, save_dir: str) -> str:
        """递归地将 BeautifulSoup 的 tag 转换成 Markdown 字符串"""
        markdown_str = ""

        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag.name[1])
            markdown_str = f"{'#' * level} {tag.get_text(strip=True)}\n\n"

        elif tag.name in ["p", "section"]:
            for child in tag.children:
                if isinstance(child, NavigableString):
                    markdown_str += str(child)
                elif child.name == "img":
                    img_src = child.get("data-src") or child.get("src")
                    alt_text = child.get("alt", "image")
                    if save_dir:
                        img_local_path = self.download_image(img_src, save_dir)
                        if img_local_path:
                            markdown_str += f"![{alt_text}]({img_local_path})\n"
                    else:
                        markdown_str += f"![{alt_text}]({img_src})\n"
                elif child.name == "br":
                    markdown_str += "\n"
                else:
                    markdown_str += self.convert_tag_to_markdown(child, save_dir)
            markdown_str += "\n\n"

        elif tag.name == "blockquote":
            content = tag.get_text(separator="\n", strip=True)
            markdown_str = "".join([f"> {line}\n" for line in content.split("\n")]) + "\n"

        elif tag.name == "pre" or (tag.name == "section" and "code-snippet__js" in tag.get("class", [])):
            code_content = tag.get_text()
            markdown_str = f"```\n{code_content.strip()}\n```\n\n"

        elif tag.name == "a":
            link_text = tag.get_text(strip=True)
            href = tag.get("href", "")
            markdown_str = f"[{link_text}]({href})"

        elif tag.name == "strong":
            markdown_str = f"**{tag.get_text(strip=True)}**"

        else:
            markdown_str = tag.get_text()

        return markdown_str

    async def fetch_and_parse(self) -> Any:
        """使用 Playwright 获取和解析微信公众号文章，失败时降级到基础抓取"""
        try:
            return await self._playwright_parse()
        except Exception as e:
            logger.warning(f"⚠️  Playwright 抓取失败: {e}")
            # TODO 实现降级方案
            raise NotImplementedError("Playwright 抓取失败，且降级方案未实现")

    def _sync_playwright_parse(self) -> dict:
        """同步版本的 Playwright 抓取实现"""
        with sync_playwright() as playwright:
            # 使用持久化上下文，减少反爬虫检测
            try:
                # 1. 启动一个 "干净" 的浏览器实例
                #    (注意：launch 不接受 user_agent 参数)
                browser = playwright.chromium.launch(
                    headless=True,
                    ignore_default_args=["--enable-automation"],
                    args=["--disable-blink-features=AutomationControlled"],
                )

                # 2. 从浏览器实例创建 "上下文" (Context)
                #    (user_agent 在这里设置)
                context = browser.new_context(
                    user_agent=get_random_user_agent("chrome"),
                    # 你可以在这里添加其他设置，例如视口大小：
                    # viewport={'width': 1920, 'height': 1080}
                )

                # 3. (可选) 如果你需要加载 cookies，在这里添加
                cookies = self.cookies  # 假设你有这个函数
                if cookies:
                    context.add_cookies(cookies)

            except Exception as e:
                raise Exception(f"Playwright 浏览器启动失败: {e}")

            page = context.new_page()

            try:
                logger.debug(f"🌐 正在访问页面: {self.url}")
                page.goto(self.url, timeout=60000)

                # 等待关键内容加载
                page.wait_for_selector("#js_content", timeout=60000)
                logger.debug("✅ 页面内容已加载！")

                html_content = page.content()
                soup = BeautifulSoup(html_content, "lxml")

                # 提取标题
                title_element = soup.find(id="activity-name")
                if not title_element:
                    raise ValueError("无法在页面中找到标题元素")
                title = title_element.get_text(strip=True)

                # 提取作者
                author_element = soup.find(id="js_name")
                author = author_element.get_text(strip=True) if author_element else "未知作者"

                # 提取正文内容
                content_element = soup.find(id="js_content")
                if not content_element:
                    raise ValueError("无法在页面中找到正文容器")

                # 纯文本内容
                content = content_element.get_text(strip=True)

                # 创建存储结构（如果启用强制保存或需要保存图片/Markdown）
                storage_info = None
                if self.force_save or self.output_format == "markdown":
                    storage_info = self.storage.create_article_storage(
                        platform=self.platform_name,
                        title=title,
                        url=self.url,
                        author=author,
                    )

                # 保存纯文本内容
                if storage_info:
                    self.storage.save_text_content(storage_info, content)

                # 处理 Markdown 格式
                markdown_content = None
                if isinstance(content_element, Tag):
                    markdown_parts = []

                    for tag in content_element.find_all(recursive=False):
                        md_part = self._sync_convert_tag_to_markdown(tag, storage_info)
                        markdown_parts.append(md_part)

                    markdown_content = "".join(markdown_parts)

                    # 保存 Markdown 文件
                    if storage_info:
                        self.storage.save_markdown_content(storage_info, markdown_content, title, author)

                # 收集图片信息
                images = []
                if isinstance(content_element, Tag):
                    for img in content_element.find_all("img"):
                        if isinstance(img, Tag):
                            img_src_raw = img.get("data-src") or img.get("src")
                            alt_text_raw = img.get("alt", "")

                            # 确保类型安全
                            img_src = str(img_src_raw) if img_src_raw else ""
                            alt_text = str(alt_text_raw) if alt_text_raw else ""

                            if img_src:
                                local_path = None
                                if storage_info:
                                    local_path = self.download_image_with_storage(img_src, storage_info, alt_text)

                                images.append({"original_url": img_src, "local_path": local_path, "alt_text": alt_text})

                # 保存文章索引
                if storage_info:
                    self.storage.save_article_index(storage_info, content[:200])

                return {
                    "title": title,
                    "author": author,
                    "content": content,
                    "markdown_content": markdown_content,
                    "images": images,
                    "save_directory": (storage_info["article_dir"] if storage_info else None),
                    "storage_info": storage_info,
                }

            except Exception as e:
                raise Exception(f"Playwright 页面处理失败: {e}")

            finally:
                context.close()

    def _sync_convert_tag_to_markdown(self, tag, storage_info=None) -> str:
        """同步版本的 Markdown 转换"""
        markdown_str = ""

        if tag.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
            level = int(tag.name[1])
            markdown_str = f"{'#' * level} {tag.get_text(strip=True)}\n\n"

        elif tag.name in ["p", "section"]:
            for child in tag.children:
                if isinstance(child, NavigableString):
                    markdown_str += str(child)
                elif child.name == "img":
                    img_src = child.get("data-src") or child.get("src")
                    alt_text = child.get("alt", "image")
                    if storage_info:
                        img_local_path = self.download_image_with_storage(str(img_src), storage_info, str(alt_text))
                        if img_local_path:
                            # 使用相对路径在Markdown中引用图片
                            relative_path = f"images/{os.path.basename(img_local_path)}"
                            markdown_str += f"![{alt_text}]({relative_path})\n"
                        else:
                            markdown_str += f"![{alt_text}]({img_src})\n"
                    else:
                        markdown_str += f"![{alt_text}]({img_src})\n"
                elif child.name == "br":
                    markdown_str += "\n"
                else:
                    markdown_str += self._sync_convert_tag_to_markdown(child, storage_info)
            markdown_str += "\n\n"

        elif tag.name == "blockquote":
            content = tag.get_text(separator="\n", strip=True)
            markdown_str = "".join([f"> {line}\n" for line in content.split("\n")]) + "\n"

        elif tag.name == "pre" or (tag.name == "section" and "code-snippet__js" in tag.get("class", [])):
            code_content = tag.get_text()
            markdown_str = f"```\n{code_content.strip()}\n```\n\n"

        elif tag.name == "a":
            link_text = tag.get_text(strip=True)
            href = tag.get("href", "")
            markdown_str = f"[{link_text}]({href})"

        elif tag.name == "strong":
            markdown_str = f"**{tag.get_text(strip=True)}**"

        else:
            markdown_str = tag.get_text()

        return markdown_str

    async def _playwright_parse(self) -> Any:
        """异步包装器，在执行器中运行同步 Playwright"""
        loop = asyncio.get_event_loop()

        # 使用 ThreadPoolExecutor 来运行同步代码
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            try:
                result_dict = await loop.run_in_executor(executor, self._sync_playwright_parse)

                # 转换回 ScrapedDataItem 对象
                images = [ImageInfo(**img_data) for img_data in result_dict["images"]]

                return ScrapedDataItem(
                    title=result_dict["title"],
                    author=result_dict["author"],
                    content=result_dict["content"],
                    markdown_content=result_dict["markdown_content"],
                    images=images,
                    save_directory=result_dict["save_directory"],
                )

            except Exception as e:
                raise e
