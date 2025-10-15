import os
import re
import json
import time
import asyncio
import httpx
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse, parse_qs, unquote
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from app.providers.base import BaseProvider
from app.models import ScrapedDataItem, ImageInfo
from app.storage import storage_manager
from typing import Any, List


class WeiboProvider(BaseProvider):
    """
    微博搜索结果页面的爬虫实现
    支持：
    1. 微博搜索结果页面 (s.weibo.com/weibo)
    2. 自动提取第一条帖子内容
    3. 图片和视频下载
    4. 登录状态保持
    """
    def __init__(self, url: str, rules: dict, save_images: bool = True, output_format: str = "markdown", 
                 force_save: bool = True):
        super().__init__(url, rules, save_images, output_format, force_save, "weibo")
        self.user_data_dir = "./chrome_user_data"
    
    def _load_saved_cookies(self):
        """加载已保存的登录cookies"""
        try:
            cookies_file = os.path.join(self.user_data_dir, "login_data", "weibo_cookies.json")
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    print(f"📂 加载已保存的登录状态，共 {len(cookies)} 个cookies")
                    return cookies
        except Exception as e:
            print(f"⚠️ 加载登录状态失败: {e}")
        return None
    
    def _is_weibo_search_page(self) -> bool:
        """判断是否为微博搜索页面"""
        return "s.weibo.com/weibo" in self.url
    
    def _extract_search_query(self) -> tuple[str, str]:
        """从URL中提取搜索关键词"""
        search_query = "default"
        try:
            parsed_url = urlparse(self.url)
            query_params = parse_qs(parsed_url.query)
            if 'q' in query_params:
                search_query = unquote(query_params['q'][0])
        except Exception as e:
            print(f"  - 警告: 解析URL关键词失败: {e}")
        
        # 清洗关键词，使其可用于文件名
        safe_search_query = re.sub(r'[\\/:*?"<>|]', '_', search_query)[:30]
        return search_query, safe_search_query
    
    def _parse_count(self, text: str) -> str:
        """从 '评论 123' 或 '123' 这样的字符串中提取数字，找不到则返回 '0'"""
        match = re.search(r'\\d+', text)
        if match:
            return match.group(0)
        return '0'
    
    async def fetch_and_parse(self) -> Any:
        """主要的抓取和解析方法"""
        if not self._is_weibo_search_page():
            print("⚠️ 当前URL不是微博搜索页面，尝试通用解析...")
            return await self._parse_generic_weibo()
        
        return await self._parse_weibo_search_page()
    
    async def _parse_weibo_search_page(self) -> Any:
        """使用Playwright解析微博搜索页面（整合test.py逻辑）"""
        def _sync_playwright_parse():
            """同步Playwright解析函数"""
            from playwright.sync_api import sync_playwright
            
            print("=" * 50)
            print("🚀 开始执行微博第一条帖子抓取任务...")
            print(f"目标URL: {self.url}")
            print("=" * 50)
            
            # 提取搜索关键词
            search_query, safe_search_query = self._extract_search_query()
            print(f"已解析搜索关键词为: {search_query}")
            
            with sync_playwright() as playwright:
                # 创建持久化上下文，保持登录状态
                context = playwright.chromium.launch_persistent_context(
                    self.user_data_dir,
                    headless=True,  # 抓取时使用无头模式  
                    slow_mo=50,
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                    ignore_default_args=['--enable-automation'],
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                page = context.new_page()
                
                # 加载已保存的登录cookies
                saved_cookies = self._load_saved_cookies()
                if saved_cookies:
                    context.add_cookies(saved_cookies)
                    print("✅ 登录状态已加载")
                
                try:
                    print("🌐 导航至目标页面...")
                    page.goto(self.url, timeout=90000, wait_until='load')
                    print("✅ 页面初步加载完成。")
                    
                    print("⏳ 正在等待搜索结果加载...")
                    robust_post_xpath = "(//*[@id='pl_feedlist_index']//div[@class='card-wrap' and .//div[@class='info']])[1]"
                    page.wait_for_selector(f"xpath={robust_post_xpath}", timeout=60000)
                    print("✅ 目标帖子元素已加载。")
                    
                    first_post = page.locator(robust_post_xpath)
                    
                    # 提取帖子信息
                    try:
                        author_name = first_post.locator('a.name').first.inner_text(timeout=5000) or "未知作者"
                    except:
                        author_name = "未知作者"
                    
                    # 提取帖子内容
                    post_content = ""
                    try:
                        full_content_locator = first_post.locator('p.txt[node-type="feed_list_content_full"]')
                        standard_content_locator = first_post.locator('p.txt[node-type="feed_list_content"]')
                        if full_content_locator.count() > 0:
                            post_content = full_content_locator.inner_text(timeout=5000)
                        elif standard_content_locator.count() > 0:
                            post_content = standard_content_locator.first.inner_text(timeout=5000)
                    except PlaywrightTimeoutError:
                        post_content = "内容提取失败"
                    
                    # 提取互动数据
                    try:
                        action_buttons = first_post.locator('div.card-act > ul > li')
                        reposts_count = self._parse_count(action_buttons.nth(0).inner_text(timeout=5000))
                        comments_count = self._parse_count(action_buttons.nth(1).inner_text(timeout=5000))
                        likes_count = self._parse_count(action_buttons.nth(2).inner_text(timeout=5000))
                    except:
                        reposts_count = comments_count = likes_count = "0"
                    
                    print(f"\\n--- 帖子信息 ---")
                    print(f"作者: {author_name}")
                    print(f"内容: {post_content[:100]}...")
                    print(f"转发: {reposts_count}, 评论: {comments_count}, 赞: {likes_count}")
                    print("------------------")
                    
                    # 创建存储结构
                    storage_info = None
                    downloaded_images = []
                    downloaded_videos = []
                    title = f"{search_query} - {author_name}帖子"
                    
                    if self.force_save:
                        # 创建标题（结合搜索词和作者）
                        storage_info = storage_manager.create_article_storage(
                            platform=self.platform_name,
                            title=title,
                            url=self.url
                        )
                        
                        # 下载图片
                        if self.save_images:
                            downloaded_images = self._sync_download_images(
                                first_post, page, storage_info
                            )
                            
                            # 下载视频
                            downloaded_videos = self._sync_download_videos(
                                first_post, page, storage_info
                            )
                    
                    # 组装完整内容
                    full_content = f"# {search_query} - 微博搜索结果\\n\\n"
                    full_content += f"**作者**: {author_name}\\n\\n"
                    full_content += f"**内容**: {post_content}\\n\\n"
                    full_content += f"**互动数据**:\\n"
                    full_content += f"- 转发: {reposts_count}\\n"
                    full_content += f"- 评论: {comments_count}\\n"
                    full_content += f"- 点赞: {likes_count}\\n\\n"
                    
                    if downloaded_images:
                        full_content += f"**图片 ({len(downloaded_images)}张)**:\\n"
                        for img_path in downloaded_images:
                            img_name = os.path.basename(img_path)
                            full_content += f"![{img_name}]({img_path})\\n"
                        full_content += "\\n"
                    
                    if downloaded_videos:
                        full_content += f"**视频 ({len(downloaded_videos)}个)**:\\n"
                        for video_path in downloaded_videos:
                            video_name = os.path.basename(video_path)
                            full_content += f"- [{video_name}]({video_path})\\n"
                        full_content += "\\n"
                    
                    # 保存内容
                    if storage_info:
                        storage_manager.save_text_content(storage_info, full_content)
                        
                        if self.output_format == "markdown":
                            storage_manager.save_markdown_content(storage_info, full_content, title)
                        
                        # 保存完整的JSON数据
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        json_data = {
                            'search_query': search_query,
                            'source_url': self.url,
                            'author': author_name,
                            'content': post_content,
                            'counts': {
                                'reposts': reposts_count,
                                'comments': comments_count,
                                'likes': likes_count
                            },
                            'local_images': downloaded_images,
                            'local_videos': downloaded_videos,
                            'scraped_timestamp': timestamp
                        }
                        
                        json_path = os.path.join(storage_info["article_dir"], "post_data.json")
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(json_data, f, ensure_ascii=False, indent=4)
                        
                        storage_manager.save_article_index(storage_info, post_content[:200])
                        
                        print(f"💾 数据已保存到: {storage_info['article_dir']}")
                    
                    # 转换图片和视频路径为ImageInfo对象
                    all_media_infos = []
                    for img_path in downloaded_images:
                        all_media_infos.append(ImageInfo(
                            original_url="weibo_image",
                            local_path=img_path,
                            alt_text=os.path.basename(img_path)
                        ))
                    
                    # 视频也作为"图片"信息处理（因为模型限制）
                    for video_path in downloaded_videos:
                        all_media_infos.append(ImageInfo(
                            original_url="weibo_video", 
                            local_path=video_path,
                            alt_text=f"视频: {os.path.basename(video_path)}"
                        ))
                    
                    return ScrapedDataItem(
                        title=f"{search_query} - {author_name}",
                        content=full_content,
                        author=author_name,
                        images=all_media_infos,
                        markdown_content=full_content if self.output_format == "markdown" else None,
                        save_directory=storage_info["article_dir"] if storage_info else None
                    )
                
                except Exception as e:
                    print(f"❌ 微博页面解析失败: {e}")
                    return None
                finally:
                    print("🔒 关闭浏览器...")
                    context.close()
        
        # 在线程池中执行同步代码
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            return await loop.run_in_executor(executor, _sync_playwright_parse)
    
    def _sync_download_images(self, first_post, page, storage_info: dict) -> List[str]:
        """同步下载图片"""
        downloaded_images = []
        
        try:
            image_elements = first_post.locator('div.media-piclist img')
            image_count = image_elements.count()
            
            if image_count > 0:
                print(f"🖼️ 发现 {image_count} 张图片，开始下载...")
                
                for i in range(image_count):
                    try:
                        img_tag = image_elements.nth(i)
                        img_url = img_tag.get_attribute('src')
                        
                        if not img_url or not img_url.startswith('http'):
                            continue
                        
                        # 获取高质量图片URL
                        large_img_url = img_url.replace('/orj360/', '/large/').replace('/thumbnail/', '/large/')
                        
                        img_filename = f"image_{i + 1}.jpg"
                        local_img_path = os.path.join(storage_info["images_dir"], img_filename)
                        
                        response = httpx.get(large_img_url, stream=True, timeout=20)
                        response.raise_for_status()
                        
                        with open(local_img_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        downloaded_images.append(local_img_path)
                        print(f"  ✅ 图片已下载: {local_img_path}")
                        
                    except Exception as e:
                        print(f"  ❌ 下载图片失败: {e}")
            else:
                print("📷 未发现图片内容")
                
        except Exception as e:
            print(f"❌ 图片下载过程出错: {e}")
        
        return downloaded_images
    
    def _sync_download_videos(self, first_post, page, storage_info: dict) -> List[str]:
        """同步下载视频"""
        downloaded_videos = []
        
        try:
            video_element = first_post.locator('video')
            
            if video_element.count() > 0:
                print("🎥 发现视频，正在解析链接...")
                
                try:
                    video_url = video_element.first.get_attribute('src', timeout=5000)
                    
                    if video_url:
                        if video_url.startswith('//'):
                            video_url = 'https:' + video_url
                        
                        print(f"✅ 视频链接解析成功: {video_url}")
                        print("⬇️ 开始下载视频...")
                        
                        video_file_path = os.path.join(storage_info["attachments_dir"], "video.mp4")
                        
                        response = httpx.get(video_url, stream=True, timeout=300)
                        response.raise_for_status()
                        
                        with open(video_file_path, 'wb') as f:
                            for chunk in response.iter_content(chunk_size=1024*1024):
                                f.write(chunk)
                        
                        downloaded_videos.append(video_file_path)
                        print(f"✅ 视频下载成功: {video_file_path}")
                        
                except Exception as e:
                    print(f"  ❌ 下载视频过程中发生错误: {e}")
            else:
                print("🎬 未发现视频内容")
                
        except Exception as e:
            print(f"❌ 视频下载过程出错: {e}")
        
        return downloaded_videos
    
    async def _parse_generic_weibo(self) -> Any:
        """通用微博页面解析（备用方法）"""
        try:
            html = await self._get_html()
            soup = BeautifulSoup(html, 'lxml')
            
            # 尝试提取基本信息
            title = "微博内容"
            content = soup.get_text()[:500] + "..."
            storage_info = None
            
            if self.force_save:
                storage_info = storage_manager.create_article_storage(
                    platform=self.platform_name,
                    title=title,
                    url=self.url
                )
                
                storage_manager.save_text_content(storage_info, content)
                
                if self.output_format == "markdown":
                    storage_manager.save_markdown_content(storage_info, content, title)
                
                storage_manager.save_article_index(storage_info, content[:200])
            
            return ScrapedDataItem(
                title=title,
                content=content,
                author="微博用户",
                markdown_content=content if self.output_format == "markdown" else None,
                save_directory=storage_info["article_dir"] if storage_info else None
            )
            
        except Exception as e:
            print(f"❌ 通用微博解析失败: {e}")
            return None
