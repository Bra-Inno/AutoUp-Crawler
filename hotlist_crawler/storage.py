"""
内容存储管理器
支持不同平台的分类存储，包括文本、图片和元数据
"""

import os
import re
import json
from datetime import datetime
from hashlib import md5
from typing import Dict, Optional, TYPE_CHECKING
from loguru import logger

from .utils.file_utils import clean_filename, ensure_directory, get_file_extension

if TYPE_CHECKING:
    from .config import CrawlerConfig


class StorageManager:
    def __init__(self, config: "CrawlerConfig"):
        self.config = config
        self.base_dir = config.download_dir
        self.platform_dirs = {}

    def _get_platform_dir(self, platform: str) -> str:
        """获取或创建平台专用目录"""
        if platform not in self.platform_dirs:
            platform_dir = ensure_directory(os.path.join(self.base_dir, platform))
            self.platform_dirs[platform] = platform_dir
        return self.platform_dirs[platform]

    def _generate_article_id(self, url: str, title: str) -> str:
        """根据URL和标题，生成文章的唯一标识符"""
        content = f"{url}_{title}"
        return md5(content.encode()).hexdigest()[:12]

    def _update_metadata(self, storage_info: Dict[str, str], updates: Dict, increment: bool = False):
        """更新元数据文件"""
        metadata_file = storage_info["metadata_file"]

        if os.path.exists(metadata_file):
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            metadata = {}

        # 更新统计信息
        if "statistics" not in metadata:
            metadata["statistics"] = {}

        for key, value in updates.items():
            if increment and key in metadata["statistics"]:
                metadata["statistics"][key] += value
            else:
                metadata["statistics"][key] = value

        metadata["updated_at"] = datetime.now().isoformat()

        # 保存更新后的元数据
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def create_article_storage(self, platform: str, title: str, url: str, author: str | None = None) -> Dict[str, str]:
        """
        为文章创建存储目录结构

        返回包含各种路径的字典
        """
        platform_dir = self._get_platform_dir(platform)
        article_id = self._generate_article_id(url, title)
        safe_title = clean_filename(title, max_length=50)

        # 创建文章专用目录
        article_dir_name = article_id
        article_dir = ensure_directory(os.path.join(platform_dir, article_dir_name))

        # 创建子目录
        images_dir = ensure_directory(os.path.join(article_dir, "images"))
        attachments_dir = ensure_directory(os.path.join(article_dir, "attachments"))

        # 准备文件路径
        text_file = os.path.join(article_dir, "content.txt")
        markdown_file = os.path.join(article_dir, "article.md")
        metadata_file = os.path.join(article_dir, "metadata.json")

        storage_info = {
            "article_id": article_id,
            "article_dir": article_dir,
            "images_dir": images_dir,
            "attachments_dir": attachments_dir,
            "text_file": text_file,
            "markdown_file": markdown_file,
            "metadata_file": metadata_file,
            "platform": platform,
            "title": title,
            "safe_title": safe_title,
        }

        # 创建初始元数据
        metadata = {
            "article_id": article_id,
            "title": title,
            "author": author,
            "url": url,
            "platform": platform,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "files": {
                "text_file": os.path.basename(text_file),
                "markdown_file": os.path.basename(markdown_file),
            },
            "statistics": {
                "images_count": 0,
                "attachments_count": 0,
                "content_length": 0,
            },
        }

        # 保存元数据
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        logger.info(f"📁 创建存储目录: {article_dir}")
        return storage_info

    def save_text_content(self, storage_info: Dict[str, str], content: str) -> str:
        """保存纯文本内容"""
        text_file = storage_info["text_file"]

        with open(text_file, "w", encoding="utf-8") as f:
            f.write(content)

        logger.debug(f"📄 保存文本文件: {os.path.basename(text_file)}")

        # 更新元数据
        self._update_metadata(storage_info, {"content_length": len(content)})

        return text_file

    def save_markdown_content(
        self,
        storage_info: Dict[str, str],
        content: str,
        title: str | None = None,
        author: str | None = None,
    ) -> str:
        """保存Markdown内容"""
        markdown_file = storage_info["markdown_file"]

        # 构建完整的Markdown内容
        markdown_parts = []

        if title:
            markdown_parts.append(f"# {title}\n")

        if author:
            markdown_parts.append(f"**作者:** {author}\n")

        markdown_parts.append("---\n\n")
        markdown_parts.append(content)

        final_content = "".join(markdown_parts)

        # 优化多余的连续空行和空格
        final_content = re.sub(r"\n{3,}", "\n\n", final_content)
        final_content = re.sub(r"\s{4,}", "   ", final_content)

        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(final_content)

        logger.debug(f"📄 保存Markdown文件: {os.path.basename(markdown_file)}")

        # 更新元数据
        self._update_metadata(storage_info, {"markdown_length": len(final_content)})

        return markdown_file

    def save_image(
        self,
        storage_info: Dict[str, str],
        image_data: bytes,
        original_url: str,
        alt_text: str = "",
        image_index: int = 1,
    ) -> Dict[str, str]:
        """
        保存图片文件（自动识别正确格式）

        返回包含图片信息的字典
        """
        images_dir = storage_info["images_dir"]

        # 使用增强的格式识别（Content-Type + URL + 文件签名）
        ext = get_file_extension(content=image_data)

        # 生成文件名
        image_filename = f"image_{image_index:03d}.{ext}"
        image_path = os.path.join(images_dir, image_filename)

        # 保存图片
        with open(image_path, "wb") as f:
            f.write(image_data)

        logger.debug(f"🖼️ 保存图片: {image_filename}")

        # 准备图片信息
        image_info = {
            "local_path": image_path,
            "relative_path": f"images/{image_filename}",
            "filename": image_filename,
            "original_url": original_url,
            "alt_text": alt_text,
            "size": len(image_data),
        }

        # 更新元数据中的图片计数
        self._update_metadata(storage_info, {"images_count": 1}, increment=True)

        return image_info

    def save_article_index(self, storage_info: Dict[str, str], content_preview: str = "") -> str:
        """保存文章索引文件，方便浏览"""
        platform_dir = self._get_platform_dir(storage_info["platform"])
        index_file = os.path.join(platform_dir, "articles_index.json")

        # 读取现有索引
        if os.path.exists(index_file):
            with open(index_file, "r", encoding="utf-8") as f:
                index_data = json.load(f)
        else:
            index_data = {"articles": [], "last_updated": None}

        # 添加新文章到索引
        article_entry = {
            "article_id": storage_info["article_id"],
            "title": storage_info["title"],
            "safe_title": storage_info["safe_title"],
            "article_dir": os.path.basename(storage_info["article_dir"]),
            "created_at": datetime.now().isoformat(),
            "preview": (content_preview[:200] + "..." if len(content_preview) > 200 else content_preview),
        }

        # 检查是否已存在，如果存在则更新
        existing_index = None
        for i, article in enumerate(index_data["articles"]):
            if article["article_id"] == storage_info["article_id"]:
                existing_index = i
                break

        if existing_index is not None:
            index_data["articles"][existing_index] = article_entry
            logger.debug(f"📋 更新文章索引: {storage_info['title']}")
        else:
            index_data["articles"].append(article_entry)
            logger.debug(f"📋 添加文章到索引: {storage_info['title']}")

        index_data["last_updated"] = datetime.now().isoformat()
        index_data["total_articles"] = len(index_data["articles"])

        # 保存索引
        with open(index_file, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)

        return index_file
