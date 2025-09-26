# app/models.py
from pydantic import BaseModel, Field
from typing import List

class HotListItem(BaseModel):
    rank: int = Field(..., description="排名")
    title: str = Field(..., description="标题")
    url: str = Field(..., description="链接")
    hotness: str | None = Field(None, description="热度值")

class HotListResponse(BaseModel):
    platform: str = Field(..., description="平台名称")
    data: List[HotListItem] = Field(..., description="热榜数据列表")
    update_time: str = Field(..., description="更新时间")