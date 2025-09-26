# app/main.py
from fastapi import FastAPI, HTTPException, Path
from datetime import datetime, timezone, timedelta
from app.models import HotListResponse
from app.config import settings
from app.cache import cache_manager
from app.providers.zhihu import ZhihuProvider
# ... 导入其他 Provider

app = FastAPI(
    title="HotList API",
    description="一个聚合各大平台热榜的 API 服务",
    version="1.0.0"
)

# 使用一个字典来映射平台名称和 Provider 类
PROVIDER_MAP = {
    "zhihu": ZhihuProvider,
    # "weibo": WeiboProvider, # 在 weibo.py 中实现后添加进来
}

@app.get(
    "/{platform}", 
    response_model=HotListResponse,
    summary="获取指定平台的热榜信息"
)
async def get_hot_list(
    platform: str = Path(..., description="平台标识符 (例如: zhihu, weibo)")
):
    """
    根据平台标识符，获取对应的热榜信息。
    - **zhihu**: 知乎热榜
    """
    if platform not in settings.PLATFORMS:
        raise HTTPException(status_code=404, detail="平台未找到或暂不支持")

    # 1. 检查缓存
    cache_key = f"hotlist:{platform}"
    cached_data = await cache_manager.get(cache_key)
    if cached_data:
        return cached_data

    # 2. 缓存未命中，执行爬取
    provider_class = PROVIDER_MAP.get(platform)
    if not provider_class:
        raise HTTPException(status_code=501, detail="该平台的爬取逻辑未实现")

    platform_config = settings.PLATFORMS[platform]
    provider = provider_class(platform, platform_config)
    
    try:
        hot_list_data = await provider.fetch_and_parse()
    except Exception as e:
        # 记录日志
        print(f"爬取 {platform} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"爬取 {platform} 数据时发生内部错误")

    # 构造响应
    beijing_tz = timezone(timedelta(hours=8))
    response_data = HotListResponse(
        platform=platform,
        data=hot_list_data,
        update_time=datetime.now(beijing_tz).isoformat()
    )

    # 3. 存入缓存
    await cache_manager.set(cache_key, response_data.model_dump(), expire=settings.CACHE_EXPIRE_SECONDS)

    return response_data