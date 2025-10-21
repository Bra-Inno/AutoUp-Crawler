from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any

import shutil
from pathlib import Path
from loguru import logger


def _ensure_env_file() -> None:
    """
    确保 .env 文件存在
    如果不存在，则从 .env.example 自动创建
    """
    # 获取本根目录（app目录的上一级）
    current_dir = Path(__file__).parent
    project_root = current_dir.parent

    env_file = project_root / ".env"
    env_example = project_root / ".env.example"

    # 如果 .env 已存在，直接返回
    if env_file.exists():
        return

    # 如果 .env.example 存在，复制为 .env
    if env_example.exists():
        try:
            shutil.copy2(env_example, env_file)
            logger.info(f"✅ 已自动从 .env.example 创建 .env 文件: {env_file}")
            logger.info(f"💡 提示: 请根据需要修改 .env 文件中的配置")
        except Exception as e:
            logger.warning(f"⚠️ 无法创建 .env 文件: {e}")
            logger.info(f"💡 请手动复制 .env.example 为 .env")
    else:
        logger.warning(f"⚠️ 未找到 .env.example 文件")
        logger.info(f"💡 请确保项目根目录下存在 .env.example 文件")


# 在导入时自动检查并创建 .env 文件
_ensure_env_file()

# 获取 .env 文件的绝对路径
_current_dir = Path(__file__).parent
_project_root = _current_dir.parent
_env_file_path = _project_root / ".env"


class Settings(BaseSettings):
    """
    应用配置模型
    所有配置从 .env 文件加载
    """

    # 从 .env 文件加载配置（使用绝对路径）
    model_config = SettingsConfigDict(env_file=str(_env_file_path), env_file_encoding="utf-8", extra="allow")

    # Redis 配置
    REDIS_URL: str
    CACHE_EXPIRE_SECONDS: int

    # 下载配置
    DOWNLOAD_DIR: str
    MAX_IMAGE_SIZE: int

    # 浏览器数据目录配置
    USER_DATA_DIR: str
    LOGIN_DATA_DIR: str

    # Playwright 配置
    PLAYWRIGHT_HEADLESS: bool
    PLAYWRIGHT_TIMEOUT: int
    USER_AGENT: str

    # 平台识别与解析规则
    PLATFORMS: Dict[str, Dict[str, Any]] = {
        "zhihu": {
            "domains": ["www.zhihu.com", "zhuanlan.zhihu.com"],
            "rules": {
                "title_selector": ".Post-Main .Post-Header .Post-Title",
                "content_selector": ".Post-Main .Post-RichText",
            },
        },
        "weixin": {  # 改为weixin以匹配PlatformType
            "domains": ["mp.weixin.qq.com"],
            "rules": {
                "title_selector": "#activity-name",
                "content_selector": "#js_content",
            },
        },
        "weibo": {
            "domains": ["s.weibo.com", "weibo.com"],
            "rules": {
                "title_selector": ".card-wrap .info .name",
                "content_selector": ".card-wrap .txt",
            },
        },
        "xiaohongshu": {
            "domains": ["www.xiaohongshu.com", "xhslink.com"],
            "rules": {
                "title_selector": ".note-item .title",
                "content_selector": ".note-item .content",
            },
        },
        "douyin": {
            "domains": ["www.douyin.com", "v.douyin.com"],
            "rules": {
                "title_selector": ".video-info .title",
                "content_selector": ".video-info .desc",
            },
        },
        "bilibili": {
            "domains": ["www.bilibili.com", "b23.tv"],
            "rules": {
                "title_selector": ".video-title",
                "content_selector": ".video-desc",
            },
        },
    }


# 创建配置实例，供应用全局使用
settings = Settings()
