"""
实用工具函数
"""

import os
import re
import filetype
from fake_useragent import UserAgent
from typing import Optional
from loguru import logger


def clean_filename(filename: str, max_length: int = 80) -> str:
    """
    清理文件名，替换掉Windows和Linux下不支持的非法字符
    """
    if not filename:
        return "untitled"

    # 替换非法字符为下划线
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", filename)

    # 移除emoji和其他特殊Unicode字符
    cleaned = re.sub(r"[^\w\s\-_.()（）\u4e00-\u9fff]", "", cleaned)

    # 移除多余的空格和下划线
    cleaned = re.sub(r"\s+", " ", cleaned)
    cleaned = re.sub(r"_+", "_", cleaned)

    # 移除前后空格、点号、下划线
    cleaned = cleaned.strip(" ._")

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


def get_file_extension(
    content: Optional[bytes] = None,
) -> str:
    if content:
        try:
            kind = filetype.guess(content)
            if kind is not None:
                # filetype 返回的扩展名已经是标准格式
                ext = kind.extension
                # 标准化：jpeg -> jpg
                return "jpg" if ext == "jpeg" else ext
        except Exception:
            pass

    # 默认返回 jpg
    return "jpg"


def format_cookies_to_string(cookies):
    """
    将 cookies 列表（字典格式）转换为标准的字符串格式，或者直接返回已是字符串的 cookies。
    """

    # 1. 检查输入是否已经是字符串
    if isinstance(cookies, str):
        logger.info("输入已经是字符串，直接返回。")
        return cookies

    # 2. 检查输入是否是列表
    if isinstance(cookies, list):
        cookie_pairs = []
        for cookie in cookies:
            # 确保列表中的元素是字典并且包含 'name' 和 'value' 键
            if isinstance(cookie, dict) and "name" in cookie and "value" in cookie:
                # 忽略 name 为空的 cookie
                if cookie["name"]:
                    cookie_pairs.append(f"{cookie['name']}={cookie['value']}")
            else:
                logger.warning(f"警告：跳过格式不正确的 cookie 项：{cookie}")

        # 3. 用分号和空格连接
        return "; ".join(cookie_pairs)

    # 4. 处理其他意外的输入类型
    else:
        logger.error(f"错误：不支持的输入类型 {type(cookies)}。请输入列表或字符串。")
        return ""


def get_random_user_agent(browser_type="chrome") -> str:
    """
    生成一个随机的、真实的 **桌面** User-Agent。

    参数:
    browser_type (str, optional): 浏览器类型。
        接受: 'chrome', 'firefox', 'safari', 'edge'。
        如果为 None 或 'random' (或任何其他值)，则返回一个完全随机的桌面UA。
        默认为 "chrome"。

    返回:
    str: 一个 User-Agent 字符串。
    """
    ua_fallback = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

    try:
        # 关键修改：添加 device_type="desktop" 来过滤
        ua_generator = UserAgent(platforms=["pc"], min_version=100.0, fallback=ua_fallback)  # <-- 确保只选择桌面UA

        if browser_type:
            browser_type = browser_type.lower()

            if browser_type == "chrome":
                return ua_generator.chrome
            elif browser_type == "firefox":
                return ua_generator.firefox
            elif browser_type == "safari":
                return ua_generator.safari
            elif browser_type == "edge":
                return ua_generator.edge
            else:
                # 如果传入了不支持的类型，也返回一个随机的桌面UA
                return ua_generator.random
        else:
            # 默认返回随机的桌面UA
            return ua_generator.random

    except Exception as e:
        logger.error(f"生成 User-Agent 时出错: {e}. 返回备用UA。")
        return ua_fallback
