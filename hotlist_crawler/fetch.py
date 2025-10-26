import os
import asyncio
from loguru import logger
from typing import Optional

from hotlist_crawler.providers.zhihu import ZhihuArticleProvider
from hotlist_crawler.providers.weibo import WeiboProvider
from hotlist_crawler.providers.weixin import WeixinMpProvider
from hotlist_crawler.providers.bilibili import BilibiliVideoProvider, BilibiliVideoQuality
from hotlist_crawler.providers.xhs import XiaohongshuProvider
from hotlist_crawler.providers.douyin import DouyinVideoProvider
from hotlist_crawler.config import settings
from hotlist_crawler.storage import storage_manager


def identify_platform_from_url(url: str) -> Optional[str]:
    """根据URL自动识别平台类型"""
    from urllib.parse import urlparse

    # 检查是否是小红书关键词搜索格式
    if url.startswith("xhs_keyword:"):
        return "xiaohongshu"

    domain = urlparse(url).netloc

    for platform, config in settings.PLATFORMS.items():
        if any(d in domain for d in config["domains"]):
            return platform
    return None


def fetch(
    url: str,
    destination: str,
    cookies: list | str | None = None,
    save_images: bool = True,
    output_format: str = "markdown",
    max_answers: int = 3,
) -> bool:
    """同步版本的fetch实现"""
    try:
        # 1. 识别平台
        platform = identify_platform_from_url(url)
        if not platform:
            logger.error(f"❌ 无法识别平台: {url}")
            return False

        logger.info(f"🎯 识别平台: {platform}")

        # 2. 确保目标目录存在
        destination = os.path.abspath(destination)
        os.makedirs(destination, exist_ok=True)
        logger.info(f"📁 目标目录: {destination}")

        # 3. 临时修改存储管理器的基础目录
        original_base_dir = storage_manager.base_dir
        storage_manager.base_dir = destination

        provider = None
        result = None

        try:
            # 4. 根据平台创建对应的提供者
            if platform == "zhihu":
                provider = ZhihuArticleProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    cookies=cookies,
                    force_save=True,
                    max_answers=max_answers,
                )
            elif platform == "weibo":
                provider = WeiboProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    cookies=cookies,
                    force_save=True,
                )
            elif platform == "weixin":
                provider = WeixinMpProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    cookies=cookies,
                    force_save=True,
                )
            elif platform == "bilibili":
                provider = BilibiliVideoProvider(
                    url=url,
                    rules={},  # B站不需要rules
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                    cookies=cookies,
                    auto_download_video=True,
                    video_quality=BilibiliVideoQuality.QUALITY_1080P,  # 默认1080P
                )
            elif platform == "douyin":
                provider = DouyinVideoProvider(
                    url=url,
                    rules={},  # 抖音不需要rules
                    save_images=save_images,
                    output_format=output_format,
                    cookies=cookies,
                    force_save=True,
                    auto_download_video=True,  # 默认自动下载视频
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
                        logger.info(f"💡 提示: 使用 cookies 参数提供小红书登录cookies")
                        return False
                    provider = XiaohongshuProvider(cookies=cookies, save_dir=destination)

                    # --- 异步辅助函数 (小红书) ---
                    async def _run_xhs_search():
                        search_result = await provider.search_and_save(
                            query=keyword,
                            require_num=2,
                            save_format="both",
                            custom_save_dir=destination,
                        )
                        await provider.close()
                        return search_result

                    # 使用 asyncio.run() 同步执行
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
                    logger.warning(f"⚠️ 小红书笔记URL抓取暂未实现")
                    logger.info(f"💡 请使用格式: xhs_keyword:关键词")
                    return False
            else:
                logger.error(f"❌ 平台 '{platform}' 的抓取逻辑未实现")
                return False

            # 5. 执行抓取 (适用于除小红书关键词搜索外的所有平台)
            logger.info(f"🚀 开始抓取: {url}")

            # --- 异步辅助函数 (其他平台) ---
            async def _run_fetch():
                return await provider.fetch_and_parse()

            # 使用 asyncio.run() 同步执行
            result = asyncio.run(_run_fetch())

            if result is None:
                logger.error(f"❌ 抓取失败，没有获取到内容")
                return False

            # 6. 验证文件是否保存成功 (同步)
            platform_dir = os.path.join(destination, platform)
            if os.path.exists(platform_dir) and os.listdir(platform_dir):
                logger.info(f"✅ 抓取成功！获取到内容项")
                logger.info(f"📂 文件已保存到: {platform_dir}")

                if hasattr(result, "title") and result.title:
                    logger.debug(f"   📄 {result.title}")
                return True
            else:
                logger.warning(f"⚠️ 抓取完成但文件保存验证失败")
                return False

        finally:
            # 恢复原始基础目录 (同步)
            storage_manager.base_dir = original_base_dir

    except Exception as e:
        logger.error(f"❌ 抓取过程中发生错误: {e}")
        return False
