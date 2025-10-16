"""
实用工具函数
"""
import os
import re
import filetype
from typing import Optional


def clean_filename(filename: str, max_length: int = 80) -> str:
    """
    清理文件名，替换掉Windows和Linux下不支持的非法字符
    
    Args:
        filename: 原始文件名
        max_length: 最大长度（默认80，避免路径过长）
        
    Returns:
        清理后的安全文件名
    """
    if not filename:
        return "untitled"
    
    # 替换非法字符为下划线
    cleaned = re.sub(r'[\\/:*?"<>|]', '_', filename)
    
    # 移除emoji和其他特殊Unicode字符
    cleaned = re.sub(r'[^\w\s\-_.()（）\u4e00-\u9fff]', '', cleaned)
    
    # 移除多余的空格和下划线
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # 移除前后空格、点号、下划线
    cleaned = cleaned.strip(' ._')
    
    # 限制长度（考虑中文字符）
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length]
        # 确保不在中文字符中间截断
        cleaned = cleaned.rstrip()
    
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


def get_file_extension(content_type: Optional[str] = None, url: Optional[str] = None, 
                      content: Optional[bytes] = None) -> str:
    """
    根据多种来源智能判断图片格式
    
    优先级策略:
    1. 如果有文件内容，使用 filetype 库检测（最准确）
    2. 如果检测失败，使用 Content-Type
    3. 如果 Content-Type 也没有，使用 URL 扩展名
    4. 都没有则默认返回 jpg
    
    Args:
        content_type: HTTP响应的Content-Type头
        url: 图片URL
        content: 图片二进制内容（用于文件类型检测，最准确）
        
    Returns:
        文件扩展名（不含点号）
    """
    if content:
        try:
            kind = filetype.guess(content)
            if kind is not None:
                # filetype 返回的扩展名已经是标准格式
                ext = kind.extension
                # 标准化：jpeg -> jpg
                return 'jpg' if ext == 'jpeg' else ext
        except Exception:
            pass
    
    # 默认返回 jpg
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