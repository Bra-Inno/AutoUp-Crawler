import os
import time
import json
import asyncio
from loguru import logger
from pathlib import Path
from typing import Optional, List, Dict
from urllib.parse import urlparse

from .config import CrawlerConfig
from .storage import StorageManager
from .types import PlatformType, PLATFORM_LOGIN_URLS, PLATFORM_CHECK_URLS
from .utils.browser_utils import launch_browser, add_stealth_scripts
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
        os.makedirs(self.config.chrome_user_data_dir, exist_ok=True)
        os.makedirs(self.config.download_dir, exist_ok=True)

    def login(self, platform: PlatformType, headless: Optional[bool] = None) -> bool:
        """在指定平台上进行用户登录操作。"""
        if not isinstance(platform, PlatformType):
            logger.error(f"❌ 无效的平台类型: {platform}")
            return False

        login_url = PLATFORM_LOGIN_URLS.get(platform)
        if not login_url:
            logger.error(f"❌ 不支持的平台: {platform}")
            return False

        use_headless = headless if headless is not None else self.config.playwright_headless

        logger.info(f"🚀 开始登录 {platform.upper()} 平台...")
        logger.info(f"📍 登录页面: {login_url}")

        try:
            import sys

            if sys.platform == "win32":
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                except:
                    pass

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self._login_async(platform, login_url, use_headless))

        except Exception as e:
            logger.error(f"❌ 登录过程中出现错误: {e}")
            return False

    async def _login_async(self, platform: PlatformType, login_url: str, headless: bool) -> bool:
        try:
            browser = await launch_browser(
                user_data_dir=self.config.chrome_user_data_dir,
                headless=headless,
                user_agent=self.config.user_agent,
            )

            try:
                page = await browser.new_page()
                page.set_default_timeout(300000)

                await add_stealth_scripts(browser)

                logger.debug("🌐 正在打开登录页面...")
                await page.goto(login_url, wait_until="networkidle")

                logger.info("\n" + "=" * 50)
                logger.info("👤 请在浏览器中完成登录操作")
                logger.info("💡 登录状态将在45秒后自动保存")
                logger.debug("⏳ 请在45秒内完成登录操作")
                logger.info("=" * 50)

                await asyncio.sleep(45)

                cookies = await page.context.cookies()
                login_data = {"cookies": cookies, "timestamp": time.time()}

                login_data_dir = Path(self.config.chrome_user_data_dir) / "login_data"
                login_data_dir.mkdir(parents=True, exist_ok=True)

                login_file = login_data_dir / f"{platform.value}_login.json"
                with open(login_file, "w", encoding="utf-8") as f:
                    json.dump(login_data, f, ensure_ascii=False, indent=2)

                logger.info("✅ 登录数据已保存")
                await browser.close()
                return True

            except Exception as e:
                logger.error(f"❌ 登录过程中发生错误: {e}")
                await browser.close()
                return False

        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            return False

    def is_online(self, platform: PlatformType) -> bool:
        """检查指定平台的登录状态是否有效。"""
        if not isinstance(platform, PlatformType):
            logger.error(f"❌ 无效的平台类型: {platform}")
            return False

        check_url = PLATFORM_CHECK_URLS.get(platform)
        if not check_url:
            logger.warning(f"⚠️ 平台 {platform} 暂不支持在线状态检测")
            return False

        try:
            import sys

            if sys.platform == "win32":
                try:
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                except:
                    pass

            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(self._is_online_async(platform, check_url))

        except Exception as e:
            logger.error(f"❌ 检测在线状态时出错: {e}")
            return False

    async def _is_online_async(self, platform: PlatformType, check_url: str) -> bool:
        try:
            browser = await launch_browser(
                user_data_dir=self.config.chrome_user_data_dir,
                headless=True,
            )

            try:
                page = await browser.new_page()
                page.set_default_timeout(10000)

                await page.goto(check_url, wait_until="networkidle")
                await asyncio.sleep(2)

                current_url = page.url
                is_logged_in = "login" not in current_url.lower() and "signin" not in current_url.lower()

                await browser.close()

                if is_logged_in:
                    logger.info(f"✅ {platform.upper()} 已登录")
                else:
                    logger.warning(f"⚠️ {platform.upper()} 未登录")

                return is_logged_in

            except Exception as e:
                logger.error(f"❌ 检测登录状态时出错: {e}")
                await browser.close()
                return False

        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            return False

    def get_all_online_status(self) -> Dict[str, bool]:
        """获取所有支持平台的登录状态。"""
        status = {}
        for platform in PlatformType:
            status[str(platform)] = self.is_online(platform)
        return status

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
        max_answers: int = 3,
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
                        rules=self.config.platforms[platform]["rules"],
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                        max_answers=max_answers,
                    )
                elif platform == "weibo":
                    provider = WeiboProvider(
                        url=url,
                        rules=self.config.platforms[platform]["rules"],
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                    )
                elif platform == "weixin":
                    provider = WeixinMpProvider(
                        url=url,
                        rules=self.config.platforms[platform]["rules"],
                        save_images=save_images,
                        output_format=output_format,
                        cookies=cookies,
                        force_save=True,
                    )
                elif platform == "bilibili":
                    provider = BilibiliVideoProvider(
                        url=url,
                        rules={},
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
                        rules={},
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

    def load_cookies(self, platform: PlatformType) -> Optional[List[Dict]]:
        """从本地文件读取指定平台的 cookies。"""
        login_data_dir = Path(self.config.chrome_user_data_dir) / "login_data"
        login_file = login_data_dir / f"{platform.value}_login.json"

        if not login_file.exists():
            logger.warning(f"⚠️ 未找到 {platform.upper()} 的登录数据")
            return None

        try:
            with open(login_file, "r", encoding="utf-8") as f:
                login_data = json.load(f)
                return login_data.get("cookies")
        except Exception as e:
            logger.error(f"❌ 读取登录数据失败: {e}")
            return None

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
