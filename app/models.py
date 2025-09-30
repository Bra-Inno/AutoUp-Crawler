from pydantic import BaseModel, Field, HttpUrl
from typing import Any, List, Optional
from datetime import datetime

class ScrapeRequest(BaseModel):
    """接收抓取请求的模型"""
    url: HttpUrl = Field(..., description="需要抓取的文章链接")
    save_images: bool = Field(True, description="是否下载图片到本地（默认开启）")
    output_format: str = Field("markdown", description="输出格式: text, markdown（默认markdown）")
    force_save: bool = Field(True, description="是否强制保存所有内容到本地（默认开启）")

class ImageInfo(BaseModel):
    """图片信息模型"""
    original_url: str = Field(..., description="原始图片URL")
    local_path: Optional[str] = Field(None, description="本地保存路径")
    alt_text: str = Field("", description="图片替代文本")

class ScrapedDataItem(BaseModel):
    """抓取到的单项数据模型 (可根据需要灵活定义)"""
    title: str = Field(..., description="抓取到的标题")
    author: Optional[str] = Field(None, description="作者")
    content: str | None = Field(None, description="抓取到的主要内容文本")
    markdown_content: Optional[str] = Field(None, description="Markdown格式的内容")
    images: List[ImageInfo] = Field(default_factory=list, description="文章中的图片信息")
    save_directory: Optional[str] = Field(None, description="内容保存目录")

class ScrapeResponse(BaseModel):
    """成功抓取后的响应模型"""
    platform: str = Field(..., description="识别出的平台")
    source_url: HttpUrl = Field(..., description="原始链接")
    data: Any = Field(..., description="抓取到的数据")
    scrape_time: datetime = Field(..., description="抓取时间")