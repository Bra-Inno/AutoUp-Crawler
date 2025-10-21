import sys
import os
from pathlib import Path
from loguru import logger

# 添加app目录到路径
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
_app_dir = os.path.join(_project_root, "app")

if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)

try:
    from app.config import settings
except ImportError as e:
    raise ImportError(f"无法导入配置模块: {e}")


def _save_to_env(key: str, value) -> None:
    """
    保存配置到 .env 文件

    Args:
        key: 配置项名称
        value: 配置项值
    """
    env_file = Path(_project_root) / ".env"

    if not env_file.exists():
        raise FileNotFoundError(f".env 文件不存在: {env_file}")

    # 读取现有内容
    with open(env_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 查找并更新配置项
    updated = False
    new_lines = []

    for line in lines:
        stripped = line.strip()
        # 跳过注释和空行
        if stripped.startswith("#") or not stripped:
            new_lines.append(line)
            continue

        # 检查是否是目标配置项
        if "=" in stripped:
            current_key = stripped.split("=")[0].strip()
            if current_key == key:
                # 格式化值
                if isinstance(value, bool):
                    formatted_value = str(value)
                elif isinstance(value, (int, float)):
                    formatted_value = str(value)
                else:
                    formatted_value = f'"{value}"'

                new_lines.append(f"{key}={formatted_value}\n")
                updated = True
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # 如果没找到,添加到文件末尾
    if not updated:
        if isinstance(value, bool):
            formatted_value = str(value)
        elif isinstance(value, (int, float)):
            formatted_value = str(value)
        else:
            formatted_value = f'"{value}"'
        new_lines.append(f"{key}={formatted_value}\n")

    # 写回文件
    with open(env_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)


def set_user_data_dir(path: str, save_to_file: bool = True) -> None:
    """
    设置浏览器用户数据目录

    Args:
        path: 浏览器用户数据目录路径
        save_to_file: 是否保存到 .env 文件(默认 True)

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.set_user_data_dir("./my_chrome_data")
    """
    if not isinstance(path, str):
        raise TypeError("path 必须是字符串类型")

    settings.USER_DATA_DIR = path
    settings.LOGIN_DATA_DIR = f"{path}/login_data"

    if save_to_file:
        _save_to_env("USER_DATA_DIR", path)
        logger.debug(f"✅ 已设置并保存 USER_DATA_DIR = {path}")
        logger.info(f"✅ LOGIN_DATA_DIR 将自动更新为 {settings.LOGIN_DATA_DIR}")
    else:
        logger.debug(f"✅ 已设置 USER_DATA_DIR = {path} (仅内存)")
        logger.debug(f"✅ 已设置 LOGIN_DATA_DIR = {settings.LOGIN_DATA_DIR} (仅内存)")


def set_user_agent(user_agent: str, save_to_file: bool = True) -> None:
    """
    设置浏览器 User-Agent

    Args:
        user_agent: User-Agent 字符串
        save_to_file: 是否保存到 .env 文件(默认 True)

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.set_user_agent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...")
    """
    if not isinstance(user_agent, str):
        raise TypeError("user_agent 必须是字符串类型")

    if not user_agent.strip():
        raise ValueError("user_agent 不能为空")

    settings.USER_AGENT = user_agent

    if save_to_file:
        _save_to_env("USER_AGENT", user_agent)
        logger.debug(f"✅ 已设置并保存 USER_AGENT = {user_agent[:50]}...")
    else:
        logger.debug(f"✅ 已设置 USER_AGENT = {user_agent[:50]}... (仅内存)")


def set_playwright_headless(headless: bool, save_to_file: bool = True) -> None:
    """
    设置 Playwright 是否使用无头模式

    Args:
        headless: True 为无头模式，False 为有头模式
        save_to_file: 是否保存到 .env 文件(默认 True)

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.set_playwright_headless(False)  # 显示浏览器窗口
    """
    if not isinstance(headless, bool):
        raise TypeError("headless 必须是布尔类型")

    settings.PLAYWRIGHT_HEADLESS = headless

    if save_to_file:
        _save_to_env("PLAYWRIGHT_HEADLESS", headless)
        logger.debug(f"✅ 已设置并保存 PLAYWRIGHT_HEADLESS = {headless}")
    else:
        logger.debug(f"✅ 已设置 PLAYWRIGHT_HEADLESS = {headless} (仅内存)")


def set_download_dir(path: str, save_to_file: bool = True) -> None:
    """
    设置下载目录

    Args:
        path: 下载目录路径
        save_to_file: 是否保存到 .env 文件(默认 True)

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.set_download_dir("./my_downloads")
    """
    if not isinstance(path, str):
        raise TypeError("path 必须是字符串类型")

    settings.DOWNLOAD_DIR = path

    if save_to_file:
        _save_to_env("DOWNLOAD_DIR", path)
        logger.debug(f"✅ 已设置并保存 DOWNLOAD_DIR = {path}")
    else:
        logger.debug(f"✅ 已设置 DOWNLOAD_DIR = {path} (仅内存)")


def set_redis_url(url: str, save_to_file: bool = True) -> None:
    """
    设置 Redis 连接 URL

    Args:
        url: Redis 连接 URL
        save_to_file: 是否保存到 .env 文件(默认 True)

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.set_redis_url("redis://192.168.1.100:6379")
    """
    if not isinstance(url, str):
        raise TypeError("url 必须是字符串类型")

    settings.REDIS_URL = url

    if save_to_file:
        _save_to_env("REDIS_URL", url)
        logger.debug(f"✅ 已设置并保存 REDIS_URL = {url}")
    else:
        logger.debug(f"✅ 已设置 REDIS_URL = {url} (仅内存)")


def get_user_data_dir() -> str:
    """
    获取当前的浏览器用户数据目录

    Returns:
        当前的 USER_DATA_DIR 值

    Example:
        >>> import hotlist_crawler
        >>> print(hotlist_crawler.get_user_data_dir())
    """
    return settings.USER_DATA_DIR


def get_user_agent() -> str:
    """
    获取当前的 User-Agent

    Returns:
        当前的 USER_AGENT 值

    Example:
        >>> import hotlist_crawler
        >>> print(hotlist_crawler.get_user_agent())
    """
    return settings.USER_AGENT


def get_login_data_dir() -> str:
    """
    获取当前的登录数据目录

    Returns:
        当前的 LOGIN_DATA_DIR 值

    Example:
        >>> import hotlist_crawler
        >>> print(hotlist_crawler.get_login_data_dir())
    """
    return settings.LOGIN_DATA_DIR


def get_all_config() -> dict:
    """
    获取所有配置信息

    Returns:
        包含所有配置的字典

    Example:
        >>> import hotlist_crawler
        >>> config = hotlist_crawler.get_all_config()
        >>> print(config)
    """
    return {
        "USER_DATA_DIR": settings.USER_DATA_DIR,
        "LOGIN_DATA_DIR": settings.LOGIN_DATA_DIR,
        "USER_AGENT": settings.USER_AGENT,
        "PLAYWRIGHT_HEADLESS": settings.PLAYWRIGHT_HEADLESS,
        "PLAYWRIGHT_TIMEOUT": settings.PLAYWRIGHT_TIMEOUT,
        "DOWNLOAD_DIR": settings.DOWNLOAD_DIR,
        "MAX_IMAGE_SIZE": settings.MAX_IMAGE_SIZE,
        "REDIS_URL": settings.REDIS_URL,
        "CACHE_EXPIRE_SECONDS": settings.CACHE_EXPIRE_SECONDS,
    }


def print_config() -> None:
    """
    打印当前所有配置信息

    Example:
        >>> import hotlist_crawler
        >>> hotlist_crawler.print_config()
    """
    config = get_all_config()
    logger.info("\n" + "=" * 60)
    logger.info("📋 当前配置信息")
    logger.info("=" * 60)

    logger.debug("\n🌐 浏览器配置:")
    logger.info(f"  USER_DATA_DIR      : {config['USER_DATA_DIR']}")
    logger.info(f"  LOGIN_DATA_DIR     : {config['LOGIN_DATA_DIR']}")
    logger.info(f"  USER_AGENT         : {config['USER_AGENT'][:50]}...")
    logger.info(f"  PLAYWRIGHT_HEADLESS: {config['PLAYWRIGHT_HEADLESS']}")
    logger.info(f"  PLAYWRIGHT_TIMEOUT : {config['PLAYWRIGHT_TIMEOUT']}ms")

    logger.info("\n📁 存储配置:")
    logger.info(f"  DOWNLOAD_DIR       : {config['DOWNLOAD_DIR']}")
    logger.info(f"  MAX_IMAGE_SIZE     : {config['MAX_IMAGE_SIZE'] / (1024*1024):.1f}MB")

    logger.info("\n💾 缓存配置:")
    logger.info(f"  REDIS_URL          : {config['REDIS_URL']}")
    logger.info(f"  CACHE_EXPIRE       : {config['CACHE_EXPIRE_SECONDS']}s")

    logger.info("=" * 60 + "\n")


# 导出所有函数
__all__ = [
    "set_user_data_dir",
    "set_user_agent",
    "set_playwright_headless",
    "set_download_dir",
    "set_redis_url",
    "get_user_data_dir",
    "get_user_agent",
    "get_login_data_dir",
    "get_all_config",
    "print_config",
]
