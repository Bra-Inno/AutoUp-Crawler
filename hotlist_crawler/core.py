"""
hotlist_crawler 核心功能模块
提供统一的爬虫接口
"""
import sys
import os
import asyncio
from typing import Optional, List, Dict, Any
from urllib.parse import urlparse

# 添加app目录到路径，以便导入现有模块
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_app_dir = os.path.join(_project_root, 'app')

if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

# Windows 系统异步支持
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

try:
    from app.providers.zhihu import ZhihuArticleProvider
    from app.providers.weibo import WeiboProvider
    from app.providers.weixin import WeixinMpProvider
    from app.config import settings
    from app.models import ScrapedDataItem
except ImportError as e:
    raise ImportError(f"无法导入核心模块: {e}")


def identify_platform(url: str) -> Optional[str]:
    """根据URL自动识别平台类型"""
    domain = urlparse(url).netloc
    for platform, config in settings.PLATFORMS.items():
        if any(d in domain for d in config["domains"]):
            return platform
    return None


def _run_async(coro):
    """运行异步函数的辅助函数"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def scrape(url: str, 
          save_images: bool = True, 
          output_format: str = "markdown",
          max_answers: int = 3,
          force_save: bool = True) -> List[ScrapedDataItem]:
    """
    通用爬取函数，自动识别平台并抓取内容
    
    Args:
        url: 要抓取的URL
        save_images: 是否下载图片到本地
        output_format: 输出格式 ("text" 或 "markdown")
        max_answers: 知乎问题最大回答数
        force_save: 是否强制保存到本地
    
    Returns:
        抓取到的内容项列表
    
    Raises:
        ValueError: 不支持的平台
        Exception: 抓取失败
    """
    platform = identify_platform(url)
    if not platform:
        raise ValueError(f"不支持的平台，URL: {url}")
    
    async def _scrape():
        if platform == "zhihu":
            provider = ZhihuArticleProvider(
                url=url,
                rules=settings.PLATFORMS[platform]["rules"],
                save_images=save_images,
                output_format=output_format,
                force_save=force_save,
                max_answers=max_answers
            )
        elif platform == "weibo":
            provider = WeiboProvider(
                url=url,
                rules=settings.PLATFORMS[platform]["rules"],
                save_images=save_images,
                output_format=output_format,
                force_save=force_save
            )
        elif platform == "weixin":
            provider = WeixinMpProvider(
                url=url,
                rules=settings.PLATFORMS[platform]["rules"],
                save_images=save_images,
                output_format=output_format,
                force_save=force_save
            )
        else:
            raise ValueError(f"平台 '{platform}' 的抓取逻辑未实现")
        
        return await provider.fetch_and_parse()
    
    try:
        result = _run_async(_scrape())
        if result is None:
            raise Exception("抓取失败，可能是页面结构已更改或链接不正确")
        return result
    except Exception as e:
        raise Exception(f"抓取过程中发生错误: {str(e)}")


def scrape_zhihu(url: str,
                save_images: bool = True,
                output_format: str = "markdown", 
                max_answers: int = 3,
                force_save: bool = True) -> List[ScrapedDataItem]:
    """
    专门的知乎内容爬取函数
    支持知乎问题页面和专栏文章
    
    Args:
        url: 知乎URL (问题页面或专栏文章)
        save_images: 是否下载图片
        output_format: 输出格式
        max_answers: 问题页面最大回答数
        force_save: 是否强制保存
    
    Returns:
        抓取到的内容项列表
    """
    if not any(domain in url for domain in ["zhihu.com", "zhuanlan.zhihu.com"]):
        raise ValueError("不是有效的知乎URL")
    
    async def _scrape_zhihu():
        provider = ZhihuArticleProvider(
            url=url,
            rules=settings.PLATFORMS["zhihu"]["rules"],
            save_images=save_images,
            output_format=output_format,
            force_save=force_save,
            max_answers=max_answers
        )
        return await provider.fetch_and_parse()
    
    try:
        result = _run_async(_scrape_zhihu())
        if result is None:
            raise Exception("知乎内容抓取失败")
        return result
    except Exception as e:
        raise Exception(f"知乎抓取错误: {str(e)}")


def scrape_weibo(url: str,
                save_images: bool = True,
                output_format: str = "text",
                force_save: bool = True) -> List[ScrapedDataItem]:
    """
    专门的微博内容爬取函数
    支持微博搜索页面
    
    Args:
        url: 微博搜索URL
        save_images: 是否下载图片和视频
        output_format: 输出格式
        force_save: 是否强制保存
    
    Returns:
        抓取到的内容项列表
    """
    if not any(domain in url for domain in ["weibo.com", "s.weibo.com"]):
        raise ValueError("不是有效的微博URL")
    
    async def _scrape_weibo():
        provider = WeiboProvider(
            url=url,
            rules=settings.PLATFORMS["weibo"]["rules"],
            save_images=save_images,
            output_format=output_format,
            force_save=force_save
        )
        return await provider.fetch_and_parse()
    
    try:
        result = _run_async(_scrape_weibo())
        if result is None:
            raise Exception("微博内容抓取失败")
        return result
    except Exception as e:
        raise Exception(f"微博抓取错误: {str(e)}")


def scrape_weixin(url: str,
                 save_images: bool = True,
                 output_format: str = "markdown",
                 force_save: bool = True) -> List[ScrapedDataItem]:
    """
    专门的微信公众号文章爬取函数
    
    Args:
        url: 微信公众号文章URL
        save_images: 是否下载图片
        output_format: 输出格式
        force_save: 是否强制保存
    
    Returns:
        抓取到的内容项列表
    """
    if "mp.weixin.qq.com" not in url:
        raise ValueError("不是有效的微信公众号文章URL")
    
    async def _scrape_weixin():
        provider = WeixinMpProvider(
            url=url,
            rules=settings.PLATFORMS["weixin"]["rules"],
            save_images=save_images,
            output_format=output_format,
            force_save=force_save
        )
        return await provider.fetch_and_parse()
    
    try:
        result = _run_async(_scrape_weixin())
        if result is None:
            raise Exception("微信公众号文章抓取失败")
        return result
    except Exception as e:
        raise Exception(f"微信抓取错误: {str(e)}")