import os
import asyncio
from loguru import logger
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse

from .config import CrawlerConfig
from .storage import StorageManager

from .providers.zhihu import ZhihuArticleProvider
from .providers.weibo import WeiboProvider
from .providers.weixin import WeixinMpProvider
from .providers.bilibili import BilibiliVideoProvider, BilibiliVideoQuality
from .providers.xhs import XiaohongshuProvider
from .providers.douyin import DouyinVideoProvider


class Crawler:
    def __init__(self, config: Optional[CrawlerConfig] = None):
        self.config = config or CrawlerConfig()
        self.storage = StorageManager(self.config)
        self._ensure_directories()

    def _ensure_directories(self):
        os.makedirs(self.config.download_dir, exist_ok=True)

    def _identify_platform(self, url: str) -> Optional[str]:
        if url.startswith("xhs_keyword:"):
            return "xiaohongshu"

        domain = urlparse(url).netloc

        for platform, config in self.config.platforms.items():
            if any(d in domain for d in config["domains"]):
                return platform
        return None

    def fetch(
        self,
        url: str,
        destination: Optional[str] = None,
        cookies: Optional[List[Dict]] = None,
        save_images: bool = True,
        output_format: str = "markdown",
    ) -> bool:
        """根据 URL 识别平台并抓取内容。"""
        try:
            platform = self._identify_platform(url)
            if not platform:
                logger.error(f"❌ 无法识别平台: {url}")
                return False

            logger.info(f"🎯 识别平台: {platform}")

            dest_dir = destination or self.config.download_dir
            dest_dir = os.path.abspath(dest_dir)
            os.makedirs(dest_dir, exist_ok=True)
            logger.info(f"📁 目标目录: {dest_dir}")

            original_base_dir = self.storage.base_dir
            self.storage.base_dir = dest_dir

            provider = None
            result = None

            try:
                if platform == "zhihu":
                    provider = ZhihuArticleProvider(
                        url=url,
                        config=self.config,
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                    )
                elif platform == "weibo":
                    provider = WeiboProvider(
                        url=url,
                        config=self.config,
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                    )
                elif platform == "weixin":
                    provider = WeixinMpProvider(
                        url=url,
                        config=self.config,
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                    )
                elif platform == "bilibili":
                    provider = BilibiliVideoProvider(
                        url=url,
                        config=self.config,
                        save_images=save_images,
                        output_format=output_format,
                        force_save=True,
                        cookies=cookies,
                        auto_download_video=True,
                        video_quality=BilibiliVideoQuality.QUALITY_1080P,
                    )
                elif platform == "douyin":
                    provider = DouyinVideoProvider(
                        url=url,
                        config=self.config,
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                        auto_download_video=True,
                    )
                elif platform == "xiaohongshu":
                    if url.startswith("xhs_keyword:"):
                        keyword = url.replace("xhs_keyword:", "").strip()
                        if not keyword:
                            logger.error(f"❌ 小红书关键词不能为空")
                            return False

                        logger.debug(f"🔍 小红书关键词搜索: {keyword}")
                        if cookies is None:
                            logger.error(f"❌ 小红书搜索需要有效的cookies，请提供cookies参数")
                            return False

                        provider = XiaohongshuProvider(cookies=cookies, save_dir=dest_dir)

                        async def _run_xhs_search():
                            search_result = await provider.search_and_save(
                                query=keyword,
                                require_num=2,
                                save_format="both",
                                custom_save_dir=dest_dir,
                            )
                            await provider.close()
                            return search_result

                        result = asyncio.run(_run_xhs_search())

                        if result.get("success"):
                            logger.info(f"✅ 小红书搜索成功！")
                            logger.debug(f"📊 找到 {result['total_found']} 个笔记")
                            logger.info(f"💾 成功保存 {result['saved']} 个笔记")
                            logger.info(f"📂 保存位置: {result['save_directory']}")
                            return True
                        else:
                            error_msg = result.get("error") or result.get("statistics", {}).get("error", "未知错误")
                            logger.error(f"❌ 小红书搜索失败: {error_msg}")
                            return False
                    else:
                        provider = XiaohongshuProvider(cookies=cookies, save_dir=dest_dir)

                        async def _run_xhs_detail():
                            detail_result = await provider.get_note_detail_and_save(
                                url=url,
                                save_format="both",
                                custom_save_dir=dest_dir,
                            )
                            await provider.close()
                            return detail_result

                        result = asyncio.run(_run_xhs_detail())

                        if result.get("success"):
                            logger.info(f"✅ 小红书笔记获取成功！")
                            return True
                        else:
                            logger.error(f"❌ 小红书笔记获取失败: {result.get('error', '未知错误')}")
                            return False
                else:
                    logger.error(f"❌ 不支持的平台: {platform}")
                    return False

                if provider and not result:

                    async def _run_fetch():
                        return await provider.fetch_and_parse()

                    result = asyncio.run(_run_fetch())

                    if result:
                        logger.info(f"✅ 内容获取成功！")
                        return True
                    else:
                        logger.error(f"❌ 内容获取失败")
                        return False

                return result is not None

            finally:
                self.storage.base_dir = original_base_dir

        except Exception as e:
            logger.error(f"❌ fetch 执行失败: {e}")
            import traceback

            logger.debug(traceback.format_exc())
            return False

    def clear_cache(self, platform: Optional[str] = None):
        """清除指定平台或所有平台的缓存。"""
        if platform:
            platform_dir = Path(self.config.download_dir) / platform
            if platform_dir.exists():
                import shutil

                shutil.rmtree(platform_dir)
                logger.info(f"✅ 已清除 {platform} 缓存")
        else:
            download_dir = Path(self.config.download_dir)
            if download_dir.exists():
                import shutil

                shutil.rmtree(download_dir)
            download_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"✅ 已清除所有缓存")
