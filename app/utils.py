"""
实用工具函数
"""
import os
import re
from typing import Optional


def clean_filename(filename: str) -> str:
    """
    清理文件名，替换掉Windows和Linux下不支持的非法字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        清理后的安全文件名
    """
    if not filename:
        return "untitled"
    
    # 替换非法字符为下划线
    cleaned = re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    # 移除前后空格和点号
    cleaned = cleaned.strip(' .')
    
    # 限制长度
    if len(cleaned) > 200:
        cleaned = cleaned[:200]
    
    return cleaned or "untitled"


def ensure_directory(directory: str) -> str:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        directory: 目录路径
        
    Returns:
        目录的绝对路径
    """
    abs_path = os.path.abspath(directory)
    os.makedirs(abs_path, exist_ok=True)
    return abs_path


def get_file_extension(content_type: Optional[str]) -> str:
    """
    根据Content-Type获取文件扩展名
    
    Args:
        content_type: HTTP响应的Content-Type头
        
    Returns:
        文件扩展名（不含点号）
    """
    if not content_type:
        return 'jpg'
    
    if 'image' in content_type:
        ext = content_type.split('/')[-1]
        if ext == "jpeg":
            return "jpg"
        return ext
    
    return 'jpg'


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小显示
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        格式化的大小字符串
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"