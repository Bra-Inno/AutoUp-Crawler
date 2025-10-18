import re
import os
import json
import asyncio
from loguru import logger
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from playwright.async_api import async_playwright

from .base import BaseProvider
from ..models import ScrapedDataItem
from ..storage import storage_manager
from ..utils.dy_downloader import DouyinVideoDownloader
from ..config import settings


class DouyinVideoProvider(BaseProvider):
    """
    抖音视频Provider

    功能特点：
    1. 支持不完整链接（只有视频ID）自动获取用户ID
    2. 使用Playwright浏览器自动化技术
    3. 自动下载视频到指定目录
    4. 提取完整的视频信息
    5. 自动从浏览器数据加载Cookie和User-Agent
    """

    def __init__(
        self,
        url: str,
        rules: dict | None = None,
        save_images: bool = False,
        output_format: str = "markdown",
        force_save: bool = True,
        cookies: Optional[str] = None,
        auto_download_video: bool = False,
    ):
        """
        初始化抖音视频Provider

        Args:
            url: 抖音视频URL（支持不完整链接）
            rules: 规则配置（保持接口一致）
            save_images: 是否保存图片
            output_format: 输出格式
            force_save: 是否强制保存
            cookies: Cookie字符串（可选，默认从浏览器数据加载）
            auto_download_video: 是否自动下载视频
        """
        if rules is None:
            rules = {}
        super().__init__(url, rules, save_images, output_format, force_save, "douyin")

        self.url = url
        self.auto_download_video = auto_download_video

        # 加载Cookie和User-Agent
        self.cookies = cookies or self._load_saved_cookies()
        self.user_agent = self._load_user_agent()

        # 初始化下载器（使用加载的Cookie和UA）
        self.downloader = DouyinVideoDownloader(
            cookie=self.cookies or "", user_agent=self.user_agent
        )

    def _load_saved_cookies(self) -> Optional[str]:
        """
        加载已保存的抖音登录cookies

        Returns:
            str: Cookie字符串，失败返回None
        """
        try:
            cookies_file = os.path.join(settings.LOGIN_DATA_DIR, "douyin_cookies.json")

            if os.path.exists(cookies_file):
                with open(cookies_file, "r", encoding="utf-8") as f:
                    cookies_list = json.load(f)
                    # 转换为cookie字符串
                    cookie_str = "; ".join(
                        [f"{c['name']}={c['value']}" for c in cookies_list]
                    )
                    logger.info(
                        f"📂 加载已保存的抖音登录状态，共 {len(cookies_list)} 个cookies"
                    )
                    return cookie_str
            else:
                logger.warning(f"⚠️ 未找到保存的抖音Cookie: {cookies_file}")
                logger.info(f"💡 提示: 可以运行浏览器登录脚本保存Cookie")
        except Exception as e:
            logger.warning(f"⚠️ 加载抖音登录状态失败: {e}")

        return None

    def _load_user_agent(self) -> str:
        """
        加载User-Agent,优先级:
        1. user_agent.txt 文件
        2. settings.USER_AGENT 配置

        Returns:
            str: User-Agent字符串
        """

        # 使用配置文件中的User-Agent
        logger.debug(f"📝 使用配置的User-Agent")
        return settings.USER_AGENT

    async def _get_user_id_from_browser(self, video_url: str) -> Optional[str]:
        """
        使用浏览器自动化获取用户ID

        Args:
            video_url: 视频URL

        Returns:
            str: 用户ID，失败返回None
        """
        logger.debug(f"   🌐 使用浏览器获取用户ID...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                )
                page = await context.new_page()

                try:
                    logger.debug("   ⏳ 正在加载页面...")
                    await page.goto(video_url, wait_until="networkidle", timeout=30000)
                    await asyncio.sleep(3)

                    html_content = await page.content()
                    pattern = r"https://www\.douyin\.com/user/([A-Za-z0-9_-]+)"
                    matches = re.findall(pattern, html_content)

                    if matches:
                        user_id = matches[0]
                        logger.debug(f"   ✅ 成功获取用户ID: {user_id[:30]}...")
                        return user_id
                    else:
                        logger.error("   ❌ 未在网页中找到用户ID")
                        return None
                except Exception as e:
                    logger.error(f"   ❌ 获取失败: {e}")
                    return None
                finally:
                    await browser.close()
        except Exception as e:
            logger.error(f"   ❌ 浏览器初始化失败: {e}")
            return None

    async def _build_complete_url(self, url: str) -> Optional[str]:
        """
        将不完整链接转换为完整链接

        Args:
            url: 原始URL（可能不完整）

        Returns:
            str: 完整的URL，失败返回None
        """
        # 如果已经是完整链接，直接返回
        if "/user/" in url:
            logger.debug("   ✅ 已经是完整链接")
            return url

        # 提取视频ID
        video_id_match = re.search(r"/video/(\d+)", url)
        if not video_id_match:
            logger.error("   ❌ 无法从链接中提取视频ID")
            return None

        video_id = video_id_match.group(1)
        logger.debug(f"   📹 视频ID: {video_id}")

        # 使用浏览器获取用户ID
        user_id = await self._get_user_id_from_browser(url)
        if not user_id:
            return None

        # 拼接完整链接
        complete_url = f"https://www.douyin.com/user/{user_id}/video/{video_id}"
        logger.debug(f"   ✅ 完整链接: {complete_url[:80]}...")
        return complete_url

    async def fetch_and_parse(self) -> ScrapedDataItem:
        """
        获取并解析抖音视频信息

        Returns:
            ScrapedDataItem: 包含视频信息的数据项
        """
        try:
            logger.debug(
                "\n" + "=" * 80 + "\n🎬 抖音视频Provider - 开始处理\n" + "=" * 80
            )
            logger.debug(f"\n📎 输入链接: {self.url}")

            # 1. 处理链接（如果需要补全）
            logger.debug("\n🔧 正在处理链接...")
            complete_url = await self._build_complete_url(self.url)

            if not complete_url:
                raise Exception("无法获取完整链接")

            # 2. 解析URL获取视频ID和用户ID
            logger.debug("\n🔍 正在解析抖音链接...")
            parse_result = await self.downloader.parse_share_url(complete_url)

            if not parse_result or "aweme_id" not in parse_result:
                raise Exception("无法解析视频链接")

            aweme_id = parse_result["aweme_id"]
            sec_user_id = parse_result.get("sec_user_id")

            logger.info(f"   ✅ 解析成功!")
            logger.info(f"   作品ID: {aweme_id}")
            if sec_user_id:
                logger.info(f"   用户ID: {sec_user_id[:20]}...")

            # 3. 从用户作品列表中查找视频（更可靠的方法）
            aweme = None
            if sec_user_id:
                logger.info("\n� 从用户作品列表中查找视频...")
                aweme = await self.downloader.find_video_in_posts(sec_user_id, aweme_id)

            # 如果find_video_in_posts失败，回退到直接获取详情
            if not aweme:
                logger.info("\n📥 使用备用方法获取视频详情...")
                aweme = await self.downloader.fetch_aweme_detail(aweme_id)

            if not aweme:
                raise Exception("无法获取视频信息")

            # 4. 提取视频信息
            video_info = self.downloader.extract_video_info(aweme)
            video_info["complete_url"] = complete_url

            # 打印视频信息
            self.downloader.print_video_info(video_info)

            # 5. 创建存储目录（如果需要保存）
            storage_info = None
            if self.force_save:
                storage_info = storage_manager.create_article_storage(
                    platform=self.platform_name,
                    title=video_info.get("desc", "抖音视频"),
                    url=self.url,
                )

            # 6. 自动下载视频（如果启用）
            if self.auto_download_video and storage_info:
                logger.info(f"\n📥 开始下载视频...")

                # 获取视频下载地址
                video_url = video_info["video"].get("download_url") or video_info[
                    "video"
                ].get("play_url")

                if not video_url:
                    logger.warning("   ⚠️ 未找到视频下载地址")
                else:
                    # 构造文件名
                    author_name = video_info["author"]["nickname"]
                    desc = video_info["desc"][:30]

                    # 清理文件名中的非法字符
                    safe_author = re.sub(r'[<>:"/\\|?*]', "_", author_name)
                    safe_desc = re.sub(r'[<>:"/\\|?*]', "_", desc)

                    filename = f"{safe_author}_{aweme_id}_{safe_desc}.mp4"
                    save_path = os.path.join(storage_info["article_dir"], filename)

                    # 下载视频
                    success = await self.downloader.download_video(video_url, save_path)

                    if success:
                        video_info["local_video_path"] = save_path
                        # 获取文件大小
                        file_size = Path(save_path).stat().st_size / (1024 * 1024)
                        logger.info(f"   文件大小: {file_size:.2f} MB")
                    else:
                        logger.error(f"   ⚠️ 视频下载失败")

            # 7. 创建ScrapedDataItem
            title = video_info.get("desc", "抖音视频")
            author_name = video_info.get("author", {}).get("nickname", "未知作者")

            # 格式化内容文本
            content_text = self._format_video_info_text(video_info)
            markdown_content = self._format_as_markdown_from_downloader_info(video_info)

            # 8. 保存到本地（如果启用）
            if self.force_save and storage_info:
                # 保存JSON格式的完整数据
                json_path = os.path.join(storage_info["article_dir"], "video_info.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=2)

                # 保存文本内容
                storage_manager.save_text_content(storage_info, content_text)

                # 保存markdown格式
                storage_manager.save_markdown_content(
                    storage_info, markdown_content, title
                )

                # 保存文章索引
                storage_manager.save_article_index(
                    storage_info, video_info.get("desc", "")[:200]
                )

            item = ScrapedDataItem(
                title=title,
                author=author_name,
                content=content_text,
                markdown_content=markdown_content,
                images=[],
                save_directory=(
                    storage_info.get("article_dir") if storage_info else None
                ),
            )

            logger.info("\n" + "=" * 80)
            logger.info("✅ 抖音视频信息获取成功!")
            logger.info("=" * 80)

            return item

        except Exception as e:
            logger.error(f"\n❌ 获取抖音视频信息失败: {str(e)}")
            raise

    def _extract_video_info(self, aweme_detail: Dict[str, Any]) -> Dict[str, Any]:
        """
        从aweme_detail中提取视频信息

        Args:
            aweme_detail: 视频详情数据

        Returns:
            dict: 提取后的视频信息
        """
        # 基本信息
        author = aweme_detail.get("author", {})
        statistics = aweme_detail.get("statistics", {})
        video = aweme_detail.get("video", {})
        music = aweme_detail.get("music", {})

        info = {
            "title": aweme_detail.get("desc", "无标题"),
            "create_time": aweme_detail.get("create_time"),
            # 作者信息
            "author": {
                "uid": author.get("uid"),
                "sec_uid": author.get("sec_uid"),
                "nickname": author.get("nickname"),
                "signature": author.get("signature"),
                "avatar": author.get("avatar_larger", {}).get("url_list", [None])[0],
            },
            # 统计信息
            "statistics": {
                "play_count": statistics.get("play_count", 0),
                "digg_count": statistics.get("digg_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "share_count": statistics.get("share_count", 0),
                "collect_count": statistics.get("collect_count", 0),
            },
            # 视频信息
            "video": {
                "duration": video.get("duration"),
                "ratio": video.get("ratio"),
                "cover": video.get("cover", {}).get("url_list", [None])[0],
                "dynamic_cover": video.get("dynamic_cover", {}).get("url_list", [None])[
                    0
                ],
                "play_addr": video.get("play_addr", {}).get("url_list", [None])[0],
                "download_addr": video.get("download_addr", {}).get("url_list", [None])[
                    0
                ],
            },
            # 音乐信息
            "music": {
                "id": music.get("id"),
                "title": music.get("title"),
                "author": music.get("author"),
                "cover": music.get("cover_large", {}).get("url_list", [None])[0],
                "play_url": music.get("play_url", {}).get("url_list", [None])[0],
            },
        }

        return info

    def _format_as_markdown(self, video_info: Dict[str, Any]) -> str:
        """
        将视频信息格式化为Markdown

        Args:
            video_info: 视频信息字典

        Returns:
            str: Markdown格式的内容
        """
        md_lines = []

        # 标题
        md_lines.append(f"# {video_info.get('title', '抖音视频')}\n")

        # 作者信息
        author = video_info.get("author", {})
        if author:
            md_lines.append(f"**作者**: {author.get('nickname', 'N/A')}")
            if author.get("signature"):
                md_lines.append(f"**签名**: {author.get('signature')}\n")
            else:
                md_lines.append("")

        # 统计信息
        stats = video_info.get("statistics", {})
        if stats:
            md_lines.append("## 数据统计\n")
            md_lines.append(f"- 播放量: {stats.get('play_count', 0):,}")
            md_lines.append(f"- 点赞数: {stats.get('digg_count', 0):,}")
            md_lines.append(f"- 评论数: {stats.get('comment_count', 0):,}")
            md_lines.append(f"- 分享数: {stats.get('share_count', 0):,}")
            md_lines.append(f"- 收藏数: {stats.get('collect_count', 0):,}\n")

        # 视频信息
        video = video_info.get("video", {})
        if video:
            md_lines.append("## 视频信息\n")
            if video.get("duration"):
                md_lines.append(f"- 时长: {video.get('duration')} 毫秒")
            if video.get("ratio"):
                md_lines.append(f"- 比例: {video.get('ratio')}")
            if video.get("cover"):
                md_lines.append(f"\n![封面]({video.get('cover')})\n")

        # 音乐信息
        music = video_info.get("music", {})
        if music and music.get("title"):
            md_lines.append("## 背景音乐\n")
            md_lines.append(f"- 标题: {music.get('title')}")
            if music.get("author"):
                md_lines.append(f"- 作者: {music.get('author')}\n")

        # 链接信息
        if video_info.get("complete_url"):
            md_lines.append(f"## 链接\n")
            md_lines.append(f"[查看原视频]({video_info.get('complete_url')})\n")

        # 本地保存路径
        if video_info.get("local_video_path"):
            md_lines.append(f"**本地视频**: `{video_info.get('local_video_path')}`\n")

        return "\n".join(md_lines)

    def _format_as_markdown_from_downloader_info(
        self, video_info: Dict[str, Any]
    ) -> str:
        """
        将下载器返回的视频信息格式化为Markdown

        Args:
            video_info: 下载器extract_video_info返回的视频信息字典

        Returns:
            str: Markdown格式的内容
        """
        md_lines = []

        # 标题
        title = video_info.get("desc", "抖音视频")
        md_lines.append(f"# {title}\n")

        # 作者信息
        author = video_info.get("author", {})
        if author:
            md_lines.append(f"**作者**: {author.get('nickname', 'N/A')}")
            if author.get("unique_id"):
                md_lines.append(f"**抖音号**: {author.get('unique_id')}")
            md_lines.append("")

        # 统计信息
        stats = video_info.get("statistics", {})
        if stats:
            md_lines.append("## 数据统计\n")
            md_lines.append(f"- 点赞数: {stats.get('digg_count', 0):,}")
            md_lines.append(f"- 评论数: {stats.get('comment_count', 0):,}")
            md_lines.append(f"- 分享数: {stats.get('share_count', 0):,}")
            md_lines.append(f"- 收藏数: {stats.get('collect_count', 0):,}\n")

        # 视频信息
        video = video_info.get("video", {})
        if video:
            md_lines.append("## 视频信息\n")
            duration = video.get("duration", 0)
            if duration:
                md_lines.append(f"- 时长: {duration:.1f} 秒")

            width = video.get("width", 0)
            height = video.get("height", 0)
            if width and height:
                md_lines.append(f"- 分辨率: {width}x{height}")

            if video.get("ratio"):
                md_lines.append(f"- 比例: {video.get('ratio')}")

            # 显示封面
            if video.get("cover_url"):
                md_lines.append(f"\n![封面]({video.get('cover_url')})\n")

        # 发布时间
        create_time = video_info.get("create_time")
        if create_time:
            from datetime import datetime

            dt = datetime.fromtimestamp(create_time)
            md_lines.append(f"**发布时间**: {dt.strftime('%Y-%m-%d %H:%M:%S')}\n")

        # 链接信息
        if video_info.get("complete_url"):
            md_lines.append(f"## 链接\n")
            md_lines.append(f"[查看原视频]({video_info.get('complete_url')})\n")

        # 本地保存路径
        if video_info.get("local_video_path"):
            md_lines.append(f"**本地视频**: `{video_info.get('local_video_path')}`\n")

        # 清晰度选项
        quality_urls = video.get("quality_urls", {})
        if quality_urls:
            md_lines.append("## 可用清晰度\n")
            for quality, url in quality_urls.items():
                md_lines.append(f"- {quality}")
            md_lines.append("")

        return "\n".join(md_lines)

    def _format_video_info_text(self, video_info: Dict[str, Any]) -> str:
        """
        将视频信息格式化为纯文本

        Args:
            video_info: 视频信息字典

        Returns:
            str: 纯文本格式的内容
        """
        lines = []

        # 基本信息
        lines.append(f"标题: {video_info.get('desc', '无标题')}")
        lines.append(f"作品ID: {video_info.get('aweme_id', 'N/A')}")

        # 作者信息
        author = video_info.get("author", {})
        if author:
            lines.append(f"作者: {author.get('nickname', 'N/A')}")
            if author.get("unique_id"):
                lines.append(f"抖音号: {author.get('unique_id')}")

        # 视频信息
        video = video_info.get("video", {})
        if video:
            duration = video.get("duration", 0)
            if duration:
                lines.append(f"时长: {duration:.1f}秒")

            width = video.get("width", 0)
            height = video.get("height", 0)
            if width and height:
                lines.append(f"分辨率: {width}x{height}")

        # 统计数据
        stats = video_info.get("statistics", {})
        if stats:
            lines.append(f"点赞: {stats.get('digg_count', 0):,}")
            lines.append(f"评论: {stats.get('comment_count', 0):,}")
            lines.append(f"分享: {stats.get('share_count', 0):,}")
            lines.append(f"收藏: {stats.get('collect_count', 0):,}")

        # 发布时间
        create_time = video_info.get("create_time")
        if create_time:
            dt = datetime.fromtimestamp(create_time)
            lines.append(f"发布时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        return "\n".join(lines)

    async def close(self):
        """关闭连接"""
        if hasattr(self.downloader, "client"):
            await self.downloader.client.aclose()
