"""
fetch 函数实现
符合API设计: fetch(url: str, destination: str) -> bool
"""

import os
import sys
import asyncio
from loguru import logger
from typing import List, Optional

# 添加app目录到路径，以便导入现有模块
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_app_dir = os.path.join(_project_root, "app")

if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    from app.providers.zhihu import ZhihuArticleProvider
    from app.providers.weibo import WeiboProvider
    from app.providers.weixin import WeixinMpProvider
    from app.providers.bilibili import BilibiliVideoProvider
    from app.providers.xhs import XiaohongshuProvider
    from app.providers.douyin import DouyinVideoProvider
    from app.config import settings
    from app.storage import storage_manager
except ImportError as e:
    raise ImportError(f"无法导入核心模块: {e}")


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


async def _fetch_async(
    url: str,
    destination: str,
    save_images: bool = True,
    output_format: str = "markdown",
    max_answers: int = 3,
) -> bool:
    """异步版本的fetch实现"""
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

        try:
            # 4. 根据平台创建对应的提供者
            if platform == "zhihu":
                provider = ZhihuArticleProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                    max_answers=max_answers,
                )
            elif platform == "weibo":
                provider = WeiboProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                )
            elif platform == "weixin":
                provider = WeixinMpProvider(
                    url=url,
                    rules=settings.PLATFORMS[platform]["rules"],
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                )
            elif platform == "bilibili":
                provider = BilibiliVideoProvider(
                    url=url,
                    rules={},  # B站不需要rules
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                    auto_download_video=True,
                    video_quality=80,  # 默认1080P
                )
            elif platform == "xiaohongshu":
                # 小红书关键词搜索
                if url.startswith("xhs_keyword:"):
                    keyword = url.replace("xhs_keyword:", "").strip()
                    if not keyword:
                        logger.error(f"❌ 小红书关键词不能为空")
                        return False

                    logger.debug(f"🔍 小红书关键词搜索: {keyword}")

                    # 创建小红书Provider
                    provider = XiaohongshuProvider(save_dir=destination)

                    # 使用search_and_save方法
                    result = await provider.search_and_save(
                        query=keyword,
                        require_num=20,  # 默认搜索20个笔记
                        save_format="both",  # 同时保存markdown和json
                        custom_save_dir=destination,
                    )

                    # 关闭provider
                    await provider.close()

                    if result.get("success"):
                        logger.info(f"✅ 小红书搜索成功！")
                        logger.debug(f"📊 找到 {result['total_found']} 个笔记")
                        logger.info(f"💾 成功保存 {result['saved']} 个笔记")
                        logger.info(f"📂 保存位置: {result['save_directory']}")
                        return True
                    else:
                        logger.error(
                            f"❌ 小红书搜索失败: {result.get('error', '未知错误')}"
                        )
                        return False
                else:
                    # 普通小红书笔记URL（暂未实现）
                    logger.warning(f"⚠️ 小红书笔记URL抓取暂未实现")
                    logger.info(f"💡 请使用格式: xhs_keyword:关键词")
                    return False
            elif platform == "douyin":
                # 抖音视频Provider
                provider = DouyinVideoProvider(
                    url=url,
                    rules={},  # 抖音不需要rules
                    save_images=save_images,
                    output_format=output_format,
                    force_save=True,
                    cookies=None,  # 会自动从浏览器数据加载
                    auto_download_video=True,  # 默认自动下载视频
                )
            else:
                logger.error(f"❌ 平台 '{platform}' 的抓取逻辑未实现")
                return False

            # 5. 执行抓取
            logger.info(f"🚀 开始抓取: {url}")
            result = await provider.fetch_and_parse()

            if result is None:
                logger.error(f"❌ 抓取失败，没有获取到内容")
                return False

            # 6. 验证文件是否保存成功
            platform_dir = os.path.join(destination, platform)
            if os.path.exists(platform_dir) and os.listdir(platform_dir):
                logger.info(f"✅ 抓取成功！获取到内容项")
                logger.info(f"📂 文件已保存到: {platform_dir}")

                # 显示保存的文件信息
                if hasattr(result, "title") and result.title:
                    logger.debug(f"   📄 {result.title}")

                return True
            else:
                logger.warning(f"⚠️ 抓取完成但文件保存验证失败")
                return False

        finally:
            # 恢复原始基础目录
            storage_manager.base_dir = original_base_dir

    except Exception as e:
        logger.error(f"❌ 抓取过程中发生错误: {e}")
        return False


def fetch(
    url: str,
    destination: str,
    save_images: bool = True,
    output_format: str = "markdown",
    max_answers: int = 3,
) -> bool:
    """
    根据URL自动识别平台并抓取内容到指定目录

    Args:
        url: 要抓取的URL
        destination: 目标存储目录
        save_images: 是否下载图片（默认True）
        output_format: 输出格式，"text"或"markdown"（默认"markdown"）
        max_answers: 知乎问题最大回答数（默认3）

    Returns:
        bool: 抓取是否成功
        - True: 抓取成功并保存到指定目录
        - False: 抓取失败

    Example:
        # 抓取知乎问题到指定目录
        success = fetch(
            "https://www.zhihu.com/question/12345",
            "./my_downloads"
        )
        if success:
            logger.info("抓取成功！")
        else:
            logger.error("抓取失败！")
    """

    # 输入验证
    if not url or not isinstance(url, str):
        logger.error("❌ URL参数无效")
        return False

    if not destination or not isinstance(destination, str):
        logger.error("❌ destination参数无效")
        return False

    # Windows系统异步支持
    if sys.platform == "win32":
        try:
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        except:
            pass

    # 运行异步函数
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(
        _fetch_async(url, destination, save_images, output_format, max_answers)
    )


def batch_fetch(
    urls: List[str],
    destination: str,
    save_images: bool = True,
    output_format: str = "markdown",
    max_answers: int = 3,
) -> dict:
    """
    批量抓取多个URL

    Args:
        urls: URL列表
        destination: 目标存储目录
        save_images: 是否下载图片
        output_format: 输出格式
        max_answers: 知乎问题最大回答数

    Returns:
        dict: 详细的批量抓取结果统计
        {
            "total": 总数,
            "success": 成功数,
            "failed": 失败数,
            "success_rate": "成功率",
            "details": [
                {"url": "...", "success": True/False, "error": "..."},
                ...
            ]
        }
    """

    if not urls or not isinstance(urls, list):
        return {
            "total": 0,
            "success": 0,
            "failed": 0,
            "success_rate": "0%",
            "details": [],
            "error": "URLs参数无效",
        }

    logger.info(f"🚀 开始批量抓取 {len(urls)} 个URL")
    logger.info(f"📁 目标目录: {os.path.abspath(destination)}")

    details = []
    success_count = 0

    for i, url in enumerate(urls, 1):
        logger.debug(f"\n进度: {i}/{len(urls)} - {url}")

        try:
            success = fetch(url, destination, save_images, output_format, max_answers)

            detail = {"url": url, "success": success}

            if success:
                success_count += 1
                logger.info(f"✅ 成功")
            else:
                logger.error(f"❌ 失败")
                detail["error"] = "抓取失败"

            details.append(detail)

        except Exception as e:
            logger.error(f"❌ 异常: {e}")
            details.append({"url": url, "success": False, "error": str(e)})

        # 添加延时避免请求过快
        if i < len(urls):
            import time

            time.sleep(1)

    # 构建返回结果
    result = {
        "total": len(urls),
        "success": success_count,
        "failed": len(urls) - success_count,
        "success_rate": f"{success_count/len(urls)*100:.1f}%",
        "details": details,
    }

    logger.info(f"\n📊 批量抓取完成:")
    logger.info(f"   总计: {result['total']}")
    logger.info(f"   成功: {result['success']}")
    logger.error(f"   失败: {result['failed']}")
    logger.info(f"   成功率: {result['success_rate']}")

    return result


def validate_destination(destination: str) -> bool:
    """
    验证目标目录是否有效

    Args:
        destination: 目标目录路径

    Returns:
        bool: 目录是否有效可用
    """

    try:
        # 检查空路径
        if not destination or not destination.strip():
            logger.error(f"❌ 目标路径不能为空")
            return False

        # 转换为绝对路径
        abs_path = os.path.abspath(destination)

        # 检查父目录是否存在且可写
        parent_dir = os.path.dirname(abs_path)
        if not os.path.exists(parent_dir):
            logger.error(f"❌ 父目录不存在: {parent_dir}")
            return False

        if not os.access(parent_dir, os.W_OK):
            logger.error(f"❌ 父目录无写入权限: {parent_dir}")
            return False

        # 尝试创建目标目录
        os.makedirs(abs_path, exist_ok=True)

        # 检查目录是否可写
        if not os.access(abs_path, os.W_OK):
            logger.error(f"❌ 目标目录无写入权限: {abs_path}")
            return False

        logger.info(f"✅ 目标目录有效: {abs_path}")
        return True

    except Exception as e:
        logger.error(f"❌ 目录验证失败: {e}")
        return False


def list_supported_platforms() -> List[str]:
    """
    获取支持的平台列表

    Returns:
        List[str]: 支持的平台名称列表
    """
    return list(settings.PLATFORMS.keys())


def get_platform_info(url: str) -> dict:
    """
    获取URL的平台信息

    Args:
        url: 要分析的URL

    Returns:
        dict: 平台信息
        {
            "url": 原始URL,
            "platform": 平台名称或None,
            "supported": 是否支持,
            "domains": 平台支持的域名列表
        }
    """

    platform = identify_platform_from_url(url)

    info = {"url": url, "platform": platform, "supported": platform is not None}

    if platform and platform in settings.PLATFORMS:
        info["domains"] = settings.PLATFORMS[platform]["domains"]
        info["rules"] = settings.PLATFORMS[platform].get("rules", {})
    else:
        info["domains"] = []
        info["rules"] = {}

    return info
