"""
hotlist_crawler 数据模型
"""
import sys
import os

# 添加app目录到路径，以便导入现有模型
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_app_dir = os.path.join(_project_root, 'app')

if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    from app.models import ScrapedDataItem, ImageInfo, ScrapeResponse, ScrapeRequest
    
    # 重新导出所有模型
    __all__ = ['ScrapedDataItem', 'ImageInfo', 'ScrapeResponse', 'ScrapeRequest']
    
except ImportError as e:
    # 如果导入失败，提供简化的模型定义
    from typing import List, Optional, Dict, Any
    from datetime import datetime
    
    class ImageInfo:
        """图片信息简化版本"""
        def __init__(self, url: str = "", local_path: str = "", alt_text: str = ""):
            self.url = url
            self.local_path = local_path
            self.alt_text = alt_text
    
    class ScrapedDataItem:
        """抓取数据项简化版本"""
        def __init__(self, title: str = "", content: str = "", author: str = "", 
                     publish_time: str = "", url: str = "", images: List[ImageInfo] = None):
            self.title = title
            self.content = content
            self.author = author
            self.publish_time = publish_time
            self.url = url
            self.images = images or []
    
    class ScrapeResponse:
        """抓取响应简化版本"""
        def __init__(self, platform: str = "", data: List[ScrapedDataItem] = None, 
                     status: str = "success"):
            self.platform = platform
            self.data = data or []
            self.status = status
    
    class ScrapeRequest:
        """抓取请求简化版本"""
        def __init__(self, url: str, save_images: bool = True, output_format: str = "markdown"):
            self.url = url
            self.save_images = save_images
            self.output_format = output_format
    
    __all__ = ['ScrapedDataItem', 'ImageInfo', 'ScrapeResponse', 'ScrapeRequest']