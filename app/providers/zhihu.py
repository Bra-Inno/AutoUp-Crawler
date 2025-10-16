import os
import re
import json
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
from loguru import logger
from app.providers.base import BaseProvider
from app.models import ScrapedDataItem
from app.storage import storage_manager
from app.file_utils import get_file_extension
from app.config import settings
from typing import Any, List, Dict


class ZhihuArticleProvider(BaseProvider):
    """
    知乎文章和问题页面的爬虫实现
    支持：
    1. 知乎专栏文章 (zhuanlan.zhihu.com)
    2. 知乎问题页面 (www.zhihu.com/question)
    """
    def __init__(self, url: str, rules: dict, save_images: bool = True, output_format: str = "markdown", 
                 force_save: bool = True, max_answers: int = 3):
        super().__init__(url, rules, save_images, output_format, force_save, "zhihu")
        self.max_answers = max_answers
    
    def _load_saved_cookies(self):
        """加载已保存的登录cookies"""
        try:
            cookies_file = os.path.join(settings.LOGIN_DATA_DIR, "zhihu_cookies.json")
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                logger.info(f"📂 加载已保存的知乎登录状态，共 {len(cookies)} 个cookies")
                return cookies
        except Exception as e:
            logger.warning(f"⚠️ 加载知乎登录状态失败: {e}")
        return None
    
    def _is_question_page(self) -> bool:
        """判断是否为知乎问题页面"""
        return "www.zhihu.com/question" in self.url
    
    def _is_article_page(self) -> bool:
        """判断是否为知乎专栏文章页面"""
        return "zhuanlan.zhihu.com" in self.url
    
    async def fetch_and_parse(self) -> Any:
        """根据URL类型选择不同的解析方法"""
        if self._is_question_page():
            return await self._parse_question_page()
        elif self._is_article_page():
            return await self._parse_article_page()
        else:
            # 尝试使用通用方法解析
            return await self._parse_article_page()
    
    async def _parse_article_page(self) -> Any:
        """解析知乎专栏文章页面（原逻辑）"""
        html = await self._get_html()
        soup = BeautifulSoup(html, 'lxml')

        try:
            title_element = soup.select_one(self.rules.get("title_selector", "h1"))
            if not title_element:
                return None
            title = title_element.text.strip()
            
            content_element = soup.select_one(self.rules.get("content_selector", ".Post-Main"))
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
    
    async def _parse_question_page(self) -> Any:
        """使用Playwright解析知乎问题页面（整合test.py逻辑）"""

        def _sync_playwright_parse():
            """同步Playwright解析函数"""
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as playwright:
                # 创建持久化上下文，保持登录状态
                context = playwright.chromium.launch_persistent_context(
                    settings.USER_DATA_DIR,
                    headless=True,  # 抓取时使用无头模式
                    slow_mo=100,
                    user_agent=settings.USER_AGENT,
                    ignore_default_args=['--enable-automation'],
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = context.new_page()
                
                # 加载已保存的登录cookies
                saved_cookies = self._load_saved_cookies()
                if saved_cookies:
                    context.add_cookies(saved_cookies)
                    logger.info("✅ 知乎登录状态已加载")
                
                try:
                    logger.debug(f"🌐 正在访问知乎问题页面: {self.url}")
                    
                    # 访问页面
                    page.goto(self.url, timeout=90000, wait_until='networkidle')
                    page.wait_for_selector('h1.QuestionHeader-title', timeout=60000)
                    logger.info("✅ 页面已稳定！")
                    
                    # 检查是否需要登录
                    if page.is_visible('button.Button--primary.Button--blue:has-text("登录")'):
                        logger.debug("\n🔐 需要登录知乎账号，请在浏览器中手动登录...")
                        try:
                            page.wait_for_selector('div.AppHeader-profile', timeout=120000)
                            logger.info("✅ 登录成功！")
                        except:
                            logger.warning("⚠️ 登录超时，尝试继续...")
                    
                    # 点击"显示全部"按钮以展开问题描述
                    logger.debug("\n📖 正在检查问题描述是否需要展开...")
                    show_all_button_selector = 'button.QuestionRichText-more'
                    if page.is_visible(show_all_button_selector):
                        try:
                            page.click(show_all_button_selector, timeout=5000)
                            logger.debug("  - 成功点击 '显示全部' 按钮，等待内容加载...")
                            page.wait_for_timeout(2000)
                        except Exception as e:
                            logger.warning(f"  - 点击 \'显示全部\' 按钮失败: {e}")
                    else:
                        logger.debug("  - 无需展开，问题描述已是全文。")
                    
                    # 等待页面稳定
                    logger.debug(f"📝 仅处理页面前 {self.max_answers} 个回答。")
                    page.wait_for_timeout(1000)
                    
                    # 获取页面内容
                    final_html = page.content()
                    soup = BeautifulSoup(final_html, 'html.parser')
                    
                    # 提取问题信息
                    question_title_element = soup.find('h1', class_='QuestionHeader-title')
                    question_title = question_title_element.get_text(strip=True) if question_title_element else "未知问题标题"
                    
                    question_detail_element = soup.find('div', class_='QuestionRichText')
                    question_detail = question_detail_element.get_text('\n', strip=True) if question_detail_element else ""
                    
                    logger.info(f"📋 问题标题: {question_title}")
                    
                    # 创建存储结构
                    storage_info = None
                    question_images = []
                    if self.force_save:
                        storage_info = storage_manager.create_article_storage(
                            platform=self.platform_name,
                            title=question_title,
                            url=self.url
                        )
                        
                        # 下载问题描述中的图片
                        if question_detail_element and self.save_images:
                            question_images = self._sync_download_question_images(
                                question_detail_element, storage_info
                            )
                    
                    # 解析回答
                    answers_list = []
                    downloaded_images = []
                    answer_items = soup.find_all('div', class_='AnswerItem')
                    
                    logger.debug(f"📊 页面共加载了 {len(answer_items)} 个回答，将处理前 {self.max_answers} 个。")
                    
                    for index, item in enumerate(answer_items[:self.max_answers]):
                        # 使用字符串操作来提取信息，避免类型问题
                        item_html = str(item)
                        
                        # 获取作者信息
                        author_match = re.search(r'<meta[^>]*itemprop="name"[^>]*content="([^"]*)"', item_html)
                        if author_match:
                            author = author_match.group(1)
                        else:
                            # 尝试从用户链接获取
                            author_match = re.search(r'class="UserLink-link"[^>]*>([^<]+)<', item_html)
                            author = author_match.group(1).strip() if author_match else "匿名用户"
                        
                        # 获取点赞数
                        vote_match = re.search(r'<meta[^>]*itemprop="upvoteCount"[^>]*content="([^"]*)"', item_html)
                        if vote_match:
                            try:
                                upvotes = int(vote_match.group(1))
                            except (ValueError, TypeError):
                                upvotes = 0
                        else:
                            upvotes = 0
                        
                        # 获取回答内容（使用BeautifulSoup，但加类型忽略）
                        content_element = item.find('div', {'class': 'RichContent-inner'})  # type: ignore
                        if content_element:
                            content_text = content_element.get_text(separator='\n', strip=True)  # type: ignore
                        else:
                            content_text = ""
                        
                        # 处理图片
                        answer_images = []
                        if content_element and self.save_images and storage_info:
                            answer_images = self._sync_download_answer_images(
                                content_element, storage_info, index, author
                            )
                            downloaded_images.extend(answer_images)
                        
                        answers_list.append({
                            'author': author,
                            'upvotes': upvotes,
                            'content': content_text,
                            'images': answer_images
                        })
                        
                        logger.debug(f"  ✅ 处理完成第 {index + 1} 个回答 (作者: {author}, 👍 {upvotes})")
                    
                    # 组装完整内容
                    full_content = f"# {question_title}\n\n"
                    if question_detail:
                        full_content += f"## 问题描述\n\n{question_detail}\n\n"
                    
                    full_content += f"## 回答 ({len(answers_list)}个)\n\n"
                    for i, answer in enumerate(answers_list, 1):
                        full_content += f"### 回答 {i} - {answer['author']} (👍 {answer['upvotes']})\n\n"
                        full_content += f"{answer['content']}\n\n"
                    
                    # 保存内容
                    if storage_info:
                        storage_manager.save_text_content(storage_info, full_content)
                        
                        if self.output_format == "markdown":
                            markdown_content = self._convert_to_markdown(question_title, question_detail, answers_list)
                            storage_manager.save_markdown_content(storage_info, markdown_content, question_title)
                        
                        # 保存完整的JSON数据
                        json_data = {
                            'question_url': self.url,
                            'question_title': question_title,
                            'question_detail': question_detail,
                            'question_images': question_images,
                            'answers_count': len(answers_list),
                            'answers': answers_list
                        }
                        
                        json_path = os.path.join(storage_info["article_dir"], "data.json")
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)
                        
                        storage_manager.save_article_index(storage_info, full_content[:200])
                        
                        logger.info(f"💾 数据已保存到: {storage_info['article_dir']}")
                    
                    # 转换图片路径为ImageInfo对象
                    from app.models import ImageInfo

                    all_image_infos = []
                    for img_path in question_images + downloaded_images:
                        all_image_infos.append(ImageInfo(
                            original_url="local_file",
                            local_path=img_path,
                            alt_text=os.path.basename(img_path)
                        ))
                    
                    return ScrapedDataItem(
                        title=question_title,
                        content=full_content,
                        author="知乎用户",
                        images=all_image_infos,
                        markdown_content=self._convert_to_markdown(question_title, question_detail, answers_list) if self.output_format == "markdown" else None,
                        save_directory=storage_info["article_dir"] if storage_info else None
                    )
                
                except Exception as e:
                    logger.error(f"❌ 知乎问题页面解析失败: {e}")
                    return None
                finally:
                    context.close()
        
        # 在线程池中执行同步代码
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _sync_playwright_parse)
    
    def _sync_download_question_images(self, question_element, storage_info: dict) -> List[str]:
        """下载问题描述中的图片"""
        downloaded_images = []
        question_image_dir = os.path.join(storage_info["images_dir"], "question_images")
        os.makedirs(question_image_dir, exist_ok=True)
        
        images = question_element.find_all('img')
        logger.debug(f"🖼️ 正在处理... 发现 {len(images)} 张")
        
        for img_index, img_tag in enumerate(images):
            img_url = img_tag.get('data-original') or img_tag.get('data-actualsrc') or img_tag.get('src')
            
            if not img_url or not img_url.startswith('http'):
                continue
            
            try:
                response = httpx.get(img_url, timeout=15)
                response.raise_for_status()
                
                # 智能检测图片格式
                content_type = response.headers.get('Content-Type')
                content = response.content
                ext = get_file_extension(content_type, img_url, content)
                
                img_filename = f"question_image_{img_index + 1}.{ext}"
                local_img_path = os.path.join(question_image_dir, img_filename)
                
                with open(local_img_path, 'wb') as f:
                    f.write(content)
                
                downloaded_images.append(local_img_path)
                logger.debug(f" {local_img_path}")
                
            except Exception as e:
                logger.error(f"  - ❌ 下载问题图片失败: {img_url}, 错误: {e}")
        
        return downloaded_images
    
    def _sync_download_answer_images(self, content_element, storage_info: dict, answer_index: int, author: str) -> List[str]:
        """下载回答中的图片"""
        downloaded_images = []
        
        # 创建回答专用图片目录
        safe_author = re.sub(r'[\\/:*?"<>|]', '_', author)
        answer_image_dir = os.path.join(storage_info["images_dir"], f"answer_{answer_index + 1}_{safe_author}")
        os.makedirs(answer_image_dir, exist_ok=True)
        
        images = content_element.find_all('img')
        logger.debug(f"  🖼️ 正在处理第 {answer_index + 1} 个回答中的图片，发现 {len(images)} 张")
        
        for img_index, img_tag in enumerate(images):
            img_url = img_tag.get('data-original') or img_tag.get('data-actualsrc') or img_tag.get('src')
            
            if not img_url or not img_url.startswith('http'):
                continue
            
            try:
                response = httpx.get(img_url, timeout=10)
                response.raise_for_status()
                
                # 获取正确的文件扩展名
                content_type = response.headers.get('Content-Type')
                content = response.content
                ext = get_file_extension(content_type, img_url, content)
                
                img_filename = f"{img_index + 1}.{ext}"
                local_img_path = os.path.join(answer_image_dir, img_filename)
                
                with open(local_img_path, 'wb') as f:
                    f.write(content)
                
                downloaded_images.append(local_img_path)
                logger.debug(f" {local_img_path}")
                
            except Exception as e:
                logger.error(f"    - ❌ 下载图片失败: {img_url}, 错误: {e}")
        
        return downloaded_images
    
    def _convert_to_markdown(self, question_title: str, question_detail: str, answers_list: List[Dict]) -> str:
        """将知乎问题和回答转换为Markdown格式"""
        markdown = f"# {question_title}\n\n"
        
        if question_detail:
            markdown += f"## 问题描述\n\n{question_detail}\n\n"
        
        markdown += f"## 回答 ({len(answers_list)}个)\n\n"
        
        for i, answer in enumerate(answers_list, 1):
            markdown += f"### 回答 {i} - {answer['author']} (👍 {answer['upvotes']})\n\n"
            markdown += f"{answer['content']}\n\n"
            
            if answer['images']:
                markdown += "**相关图片:**\n\n"
                for img_path in answer['images']:
                    img_name = os.path.basename(img_path)
                    # 使用相对路径在Markdown中引用图片
                    relative_path = f"images/{img_name}"
                    markdown += f"![{img_name}]({relative_path})\n\n"
        
        return markdown
