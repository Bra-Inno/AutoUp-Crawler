import asyncio
import httpx
import re
import os
import json
from pathlib import Path
from urllib.parse import urlencode
from typing import Dict, Any, Optional
from datetime import datetime
from loguru import logger


class DouyinVideoDownloader:
    """抖音视频下载器"""

    USER_POST_ENDPOINT = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    AWEME_DETAIL_ENDPOINT = "https://www.douyin.com/aweme/v1/web/aweme/detail/"

    def __init__(self, cookie: str = "", user_agent: str = ""):
        """初始化下载器，接收配置参数。"""
        self.cookie = cookie
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        self.headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": self.user_agent,
            "Referer": "https://www.douyin.com/",
            "Cookie": self.cookie,
        }
        self.client = httpx.AsyncClient(headers=self.headers, timeout=30.0, follow_redirects=True, http2=True)

    async def parse_share_url(self, share_url: str) -> Dict[str, Optional[str]]:
        """解析分享链接，获取作品ID和用户ID。"""
        logger.debug(f"🔍 正在解析链接...")

        try:
            if "v.douyin.com" in share_url or "iesdouyin.com" in share_url:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                    response = await client.get(share_url)
                    share_url = str(response.url)

            aweme_id = None
            sec_user_id = None

            video_match = re.search(r"/video/(\d+)", share_url)
            if video_match:
                aweme_id = video_match.group(1)

            user_match = re.search(r"/user/([^/\?]+)", share_url)
            if user_match:
                sec_user_id = user_match.group(1)

            if not aweme_id:
                modal_match = re.search(r"modal_id=(\d+)", share_url)
                if modal_match:
                    aweme_id = modal_match.group(1)

            if aweme_id and not sec_user_id:
                logger.debug(f"⚠️  链接缺少用户ID，尝试自动获取...")
                sec_user_id = await self._fetch_user_id_from_video(aweme_id)

            if aweme_id:
                logger.info(f"✅ 解析成功! 作品ID: {aweme_id}")

            return {"aweme_id": aweme_id, "sec_user_id": sec_user_id, "url": share_url}

        except Exception as e:
            logger.error(f"❌ 解析链接失败: {e}")
            return {}

    async def _fetch_user_id_from_video(self, aweme_id: str) -> Optional[str]:
        """从视频ID获取用户ID。"""
        try:
            video_url = f"https://www.douyin.com/video/{aweme_id}"
            response = await self.client.get(video_url, follow_redirects=True)

            user_match = re.search(r"/user/([^/\?]+)", str(response.url))
            if user_match:
                return user_match.group(1)

            html = response.text
            sec_id_match = re.search(r'"authorSecId"\s*:\s*"([^"]+)"', html)
            if sec_id_match:
                return sec_id_match.group(1)

        except Exception as e:
            logger.debug(f"获取用户ID失败: {e}")

        return None

    async def fetch_aweme_detail(self, aweme_id: str) -> Optional[Dict[str, Any]]:
        """获取作品详情。"""
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "aweme_id": aweme_id,
            "pc_client_type": 1,
            "version_code": "290100",
            "version_name": "29.1.0",
            "cookie_enabled": "true",
            "screen_width": 1920,
            "screen_height": 1080,
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "130.0.0.0",
        }

        url = f"{self.AWEME_DETAIL_ENDPOINT}?{urlencode(params)}"

        try:
            response = await self.client.get(url)
            data = response.json()

            if data.get("status_code") == 0:
                aweme_detail = data.get("aweme_detail")
                if aweme_detail:
                    return aweme_detail

        except Exception as e:
            logger.debug(f"获取作品详情失败: {e}")

        return None

    def extract_video_info(self, aweme: Dict[str, Any]) -> Dict[str, Any]:
        """从作品数据中提取视频信息。"""
        video = aweme.get("video", {})
        author = aweme.get("author", {})
        statistics = aweme.get("statistics", {})

        play_addr = video.get("play_addr", {}).get("url_list", [])
        download_addr = video.get("download_addr", {}).get("url_list", [])

        return {
            "aweme_id": aweme.get("aweme_id"),
            "desc": aweme.get("desc", ""),
            "create_time": aweme.get("create_time", 0),
            "author": {
                "nickname": author.get("nickname", ""),
                "unique_id": author.get("unique_id", ""),
                "sec_uid": author.get("sec_uid", ""),
            },
            "video": {
                "duration": video.get("duration", 0) / 1000,
                "width": video.get("width", 0),
                "height": video.get("height", 0),
                "cover_url": video.get("cover", {}).get("url_list", [""])[0],
                "play_url": play_addr[0] if play_addr else "",
                "download_url": download_addr[0] if download_addr else "",
            },
            "statistics": {
                "digg_count": statistics.get("digg_count", 0),
                "comment_count": statistics.get("comment_count", 0),
                "share_count": statistics.get("share_count", 0),
                "collect_count": statistics.get("collect_count", 0),
            },
        }

    def print_video_info(self, info: Dict[str, Any]):
        """打印视频信息。"""
        logger.info("📹 视频信息")
        logger.info(f"   作品ID: {info['aweme_id']}")
        logger.info(f"   描述: {info['desc'][:60]}")

        if info["create_time"]:
            dt = datetime.fromtimestamp(info["create_time"])
            logger.info(f"   发布时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

        author = info["author"]
        logger.info(f"👤 作者: {author['nickname']}")

        video = info["video"]
        logger.info(f"🎬 视频: {video['duration']:.1f}秒, {video['width']}x{video['height']}")

        stats = info["statistics"]
        logger.info(f"📊 点赞: {stats['digg_count']}, 评论: {stats['comment_count']}")

    async def download_video(self, video_url: str, save_path: str) -> bool:
        """下载视频到指定路径。"""
        try:
            logger.info(f"⬇️  开始下载视频...")

            Path(save_path).parent.mkdir(parents=True, exist_ok=True)

            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "GET",
                    video_url,
                    headers={
                        "User-Agent": self.user_agent,
                        "Referer": "https://www.douyin.com/",
                    },
                ) as response:
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    downloaded = 0

                    with open(save_path, "wb") as f:
                        async for chunk in response.aiter_bytes(chunk_size=1024 * 1024):
                            f.write(chunk)
                            downloaded += len(chunk)

                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"进度: {progress:.1f}%")

            logger.info(f"✅ 下载完成! 保存路径: {save_path}")
            return True

        except Exception as e:
            logger.error(f"❌ 下载失败: {e}")
            return False

    async def download_from_url(self, share_url: str, save_dir: str = "downloads") -> str:
        """从分享链接下载视频，返回保存路径。"""
        parse_result = await self.parse_share_url(share_url)
        aweme_id = parse_result.get("aweme_id")

        if not aweme_id:
            logger.error("❌ 无法从链接中提取作品ID")
            return ""

        aweme = await self.fetch_aweme_detail(aweme_id)
        if not aweme:
            logger.error("❌ 无法获取视频信息")
            return ""

        video_info = self.extract_video_info(aweme)
        self.print_video_info(video_info)

        video_data = video_info["video"]
        download_url = video_data.get("download_url") or video_data.get("play_url")

        if not download_url:
            logger.error("❌ 未找到视频下载地址")
            return ""

        author_name = video_info["author"]["nickname"]
        desc = video_info["desc"][:30]
        safe_author = re.sub(r'[<>:"/\\|?*]', "_", author_name)
        safe_desc = re.sub(r'[<>:"/\\|?*]', "_", desc)

        filename = f"{safe_author}_{aweme_id}_{safe_desc}.mp4"
        save_path = str(Path(save_dir) / filename)

        success = await self.download_video(download_url, save_path)
        return save_path if success else ""

    async def find_video_in_posts(self, sec_user_id: str, aweme_id: str, max_pages: int = 20) -> Optional[dict]:
        """
        从用户作品列表中查找指定视频

        Args:
            sec_user_id: 用户ID
            aweme_id: 作品ID
            max_pages: 最多查找页数

        Returns:
            dict: 作品信息,未找到返回None
        """
        logger.info(f"\n🔎 正在搜索作品...")

        max_cursor = 0

        for page in range(max_pages):
            res = await self.fetch_user_posts(sec_user_id, max_cursor, 20)

            if res.get("status_code") != 0:
                logger.error(f"   获取失败: {res.get('status_msg', '未知错误')}")
                return None

            aweme_list = res.get("aweme_list", [])

            # 在当前页查找目标作品
            for aweme in aweme_list:
                if aweme.get("aweme_id") == aweme_id:
                    logger.info(f"✅ 找到作品! (第{page+1}页)")
                    return aweme

            # 检查是否还有更多
            if not res.get("has_more", False):
                logger.info(f"   已搜索完所有 {page+1} 页")
                break

            max_cursor = res.get("max_cursor", 0)

            if (page + 1) % 5 == 0:
                logger.info(f"   已搜索 {page+1} 页...")

            await asyncio.sleep(0.3)  # 避免请求过快

        logger.error(f"❌ 未找到作品 (搜索了{max_pages}页)")
        return None

    async def fetch_user_posts(self, sec_user_id: str, max_cursor: int = 0, count: int = 20) -> Dict[str, Any]:
        """获取用户作品列表"""
        params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "sec_user_id": sec_user_id,
            "max_cursor": max_cursor,
            "count": count,
            "pc_client_type": 1,
            "version_code": "290100",
            "version_name": "29.1.0",
            "cookie_enabled": "true",
            "screen_width": 1920,
            "screen_height": 1080,
            "browser_language": "zh-CN",
            "browser_platform": "Win32",
            "browser_name": "Chrome",
            "browser_version": "130.0.0.0",
        }

        url = f"{self.USER_POST_ENDPOINT}?{urlencode(params)}"

        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"请求失败: {e}")
            return {"status_code": -1}

    async def close(self):
        """关闭客户端。"""
        await self.client.aclose()
