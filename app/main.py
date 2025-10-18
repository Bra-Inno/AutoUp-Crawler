import sys
import asyncio
from loguru import logger
from fastapi import FastAPI, HTTPException
from urllib.parse import urlparse
from datetime import datetime, timezone, timedelta

from app.models import ScrapeRequest, ScrapeResponse
from app.config import settings
from app.cache import cache_manager
from app.storage import storage_manager
from app.providers.zhihu import ZhihuArticleProvider
from app.providers.weixin import WeixinMpProvider
from app.providers.weibo import WeiboProvider
from app.providers.bilibili import BilibiliVideoProvider
from app.providers.douyin import DouyinVideoProvider


# Windows 系统上修复异步问题
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

app = FastAPI(
    title="Universal Scraper API",
    description="一个可以根据 URL 动态抓取指定平台内容的 API",
    version="2.0.0",
)

# 调度器：将平台标识符映射到对应的 Provider 类
PROVIDER_MAP = {
    "zhihu": ZhihuArticleProvider,
    "weixin_mp": WeixinMpProvider,
    "weibo": WeiboProvider,
    "bilibili": BilibiliVideoProvider,
    "douyin": DouyinVideoProvider,
}


def identify_platform(url: str) -> str | None:
    """根据 URL 的域名识别平台"""
    domain = urlparse(url).netloc
    for platform, config in settings.PLATFORMS.items():
        if any(d in domain for d in config["domains"]):
            return platform
    return None


@app.post("/scrape", response_model=ScrapeResponse, summary="根据URL抓取内容")
async def scrape_url(request: ScrapeRequest):
    """
    接收一个 URL，自动识别平台并抓取其主要内容。
    - **url**: 需要抓取的文章链接
    - **save_images**: 是否下载图片到本地
    - **output_format**: 输出格式（text 或 markdown）
    """
    url_str = str(request.url)

    platform = identify_platform(url_str)
    if not platform:
        raise HTTPException(status_code=400, detail="无法识别或暂不支持该链接的平台")

    # 包含请求参数的缓存键
    cache_key = f"scraped:{url_str}:{request.save_images}:{request.output_format}"
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return ScrapeResponse(**cached_data)

    provider_class = PROVIDER_MAP.get(platform)
    if not provider_class:
        raise HTTPException(
            status_code=501, detail=f"平台 '{platform}' 的抓取逻辑未实现"
        )

    provider = provider_class(
        url=url_str,
        rules=settings.PLATFORMS[platform]["rules"],
        save_images=request.save_images,
        output_format=request.output_format,
        force_save=request.force_save,
    )

    try:
        scraped_data = await provider.fetch_and_parse()
        if scraped_data is None:
            raise HTTPException(
                status_code=422,
                detail="解析页面内容失败，可能是页面结构已更改或链接不正确",
            )
    except Exception as e:
        # 在生产环境中，这里应该使用日志库记录错误
        logger.error(f"抓取失败: {url_str} - 错误: {e}")
        raise HTTPException(status_code=500, detail="抓取过程中发生内部错误")

    beijing_tz = timezone(timedelta(hours=8))
    response_data = ScrapeResponse(
        platform=platform,
        source_url=request.url,  # 使用原始的HttpUrl对象
        data=scraped_data,
        scrape_time=datetime.now(beijing_tz),
    )

    await cache_manager.set(
        cache_key,
        response_data.model_dump(mode="json"),
        expire=settings.CACHE_EXPIRE_SECONDS,
    )

    return response_data


@app.get("/", summary="健康检查")
def read_root():
    return {"status": "ok"}


@app.get("/storage/platforms", summary="获取所有平台的存储摘要")
async def get_storage_platforms():
    """获取所有已保存内容的平台列表和摘要"""
    platforms = storage_manager.list_all_platforms()
    platform_summaries = []

    for platform in platforms:
        summary = storage_manager.get_platform_summary(platform)
        platform_summaries.append(summary)

    return {"total_platforms": len(platforms), "platforms": platform_summaries}


@app.get("/storage/platform/{platform}", summary="获取特定平台的详细信息")
async def get_platform_details(platform: str):
    """获取特定平台的详细存储信息"""
    summary = storage_manager.get_platform_summary(platform)
    if summary["total_articles"] == 0:
        raise HTTPException(
            status_code=404, detail=f"平台 '{platform}' 没有找到任何文章"
        )

    return summary
