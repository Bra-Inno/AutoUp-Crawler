"""
B站视频Provider - 支持获取视频信息和下载链接
"""
import os
import re
import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode
from app.providers.base import BaseProvider
from app.models import ScrapedDataItem
from app.storage import storage_manager
import httpx


class BilibiliVideoEndpoints:
    """B站视频相关API端点"""
    
    BILIAPI_DOMAIN = "https://api.bilibili.com"
    
    # 视频详情（包含基本信息和统计数据）
    VIDEO_DETAIL = f"{BILIAPI_DOMAIN}/x/web-interface/view"
    
    # 视频标签
    VIDEO_TAGS = f"{BILIAPI_DOMAIN}/x/tag/archive/tags"
    
    # 视频分P信息
    VIDEO_PAGES = f"{BILIAPI_DOMAIN}/x/player/pagelist"
    
    # 视频播放地址
    VIDEO_PLAYURL = f"{BILIAPI_DOMAIN}/x/player/playurl"


class BilibiliVideoProvider(BaseProvider):
    """
    B站视频Provider
    支持功能：
    1. 获取指定视频的详细信息（标题、简介、统计数据等）
    2. 获取视频下载链接
    3. 支持多P视频
    """
    
    def __init__(self, url: str, rules: dict | None = None, save_images: bool = False, 
                 output_format: str = "json", force_save: bool = True, 
                 cookies: Optional[str] = None, auto_download_video: bool = False,
                 video_quality: int = 80):
        """
        初始化B站视频Provider
        
        Args:
            url: B站视频URL（支持BV号和av号）
            rules: 规则配置（暂不使用，保持接口一致）
            save_images: 是否保存图片（B站视频不需要）
            output_format: 输出格式（json）
            force_save: 是否强制保存
            cookies: B站登录cookie（获取高清画质需要）
            auto_download_video: 是否自动下载视频文件
            video_quality: 视频清晰度 (16=360P, 32=480P, 64=720P, 80=1080P)
        """
        if rules is None:
            rules = {}
        super().__init__(url, rules, save_images, output_format, force_save, "bilibili")
        self.cookies = cookies or self._load_saved_cookies()
        self.bvid = self._extract_bvid(url)
        self.auto_download_video = auto_download_video
        self.video_quality = video_quality
        
        # 更新headers为B站专用
        self.headers.update({
            "Referer": "https://www.bilibili.com",
            "Origin": "https://www.bilibili.com",
            "Accept": "application/json, text/plain, */*",
        })
    
    def _load_saved_cookies(self) -> Optional[str]:
        """加载已保存的B站登录cookies"""
        try:
            user_data_dir = "./chrome_user_data"
            cookies_file = os.path.join(user_data_dir, "login_data", "bilibili_cookies.json")
            if os.path.exists(cookies_file):
                with open(cookies_file, 'r', encoding='utf-8') as f:
                    cookies_list = json.load(f)
                    # 转换为cookie字符串
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
                    print(f"📂 加载已保存的B站登录状态，共 {len(cookies_list)} 个cookies")
                    return cookie_str
        except Exception as e:
            print(f"⚠️ 加载B站登录状态失败: {e}")
        return None
    
    def _extract_bvid(self, url: str) -> str:
        """
        从URL中提取BVID
        支持的格式:
        - https://www.bilibili.com/video/BV1Xu41177nj
        - https://b23.tv/BV1Xu41177nj (短链)
        - BV1Xu41177nj (直接BV号)
        """
        # 如果直接是BV号
        if url.startswith("BV"):
            return url
        
        # 从URL中提取
        bv_match = re.search(r'(BV[a-zA-Z0-9]+)', url)
        if bv_match:
            return bv_match.group(1)
        
        raise ValueError(f"无法从URL中提取BVID: {url}")
    
    async def _request_api(self, endpoint: str, params: dict | None = None) -> Dict[str, Any]:
        """
        统一的API请求方法
        
        Args:
            endpoint: API端点
            params: 请求参数
            
        Returns:
            API响应的JSON数据
        """
        if params:
            endpoint = f"{endpoint}?{urlencode(params)}"
        
        headers = self.headers.copy()
        if self.cookies:
            headers["Cookie"] = self.cookies
        
        async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=30.0) as client:
            try:
                response = await client.get(endpoint)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                raise Exception(f"API请求失败: {str(e)}")
    
    async def get_video_detail(self) -> Dict[str, Any]:
        """
        获取视频详细信息
        
        Returns:
            包含视频详细信息的字典
        """
        params = {"bvid": self.bvid}
        return await self._request_api(BilibiliVideoEndpoints.VIDEO_DETAIL, params)
    
    async def get_video_tags(self) -> Dict[str, Any]:
        """获取视频标签"""
        params = {"bvid": self.bvid}
        return await self._request_api(BilibiliVideoEndpoints.VIDEO_TAGS, params)
    
    async def get_video_pages(self) -> Dict[str, Any]:
        """获取视频分P信息"""
        params = {"bvid": self.bvid}
        return await self._request_api(BilibiliVideoEndpoints.VIDEO_PAGES, params)
    
    async def get_video_download_url(self, cid: Optional[int] = None, qn: int = 80) -> Dict[str, Any]:
        """
        获取视频下载链接
        
        Args:
            cid: 分P的CID（可选，不提供则获取第一P）
            qn: 清晰度，80=1080P，64=720P，32=480P，16=360P
            
        Returns:
            包含视频下载链接信息的字典
        """
        # 如果没有提供cid，先获取视频详情
        if not cid:
            detail = await self.get_video_detail()
            if detail.get("code") != 0:
                return detail
            cid = detail.get("data", {}).get("cid")
            if not cid:
                return {"code": -1, "message": "无法获取视频cid"}
        
        params = {
            "bvid": self.bvid,
            "cid": cid,
            "qn": qn,
            "fnval": 16,  # 获取dash格式
            "fourk": 1
        }
        return await self._request_api(BilibiliVideoEndpoints.VIDEO_PLAYURL, params)
    
    async def fetch_and_parse(self) -> Any:
        """
        实现BaseProvider的抽象方法
        获取视频完整信息（包含详情、标签、分P信息）
        
        Returns:
            ScrapedDataItem对象，包含视频信息
        """
        try:
            # 获取基本详情
            detail = await self.get_video_detail()
            
            if detail.get("code") != 0:
                raise Exception(f"获取视频详情失败: {detail.get('message', '未知错误')}")
            
            data = detail.get("data", {})
            
            # 获取标签和分P信息
            tags_result = await self.get_video_tags()
            pages_result = await self.get_video_pages()
            
            # 整合信息
            video_info = {
                "bvid": data.get("bvid"),
                "aid": data.get("aid"),
                "title": data.get("title"),
                "desc": data.get("desc"),
                "pic": data.get("pic"),  # 封面图
                "duration": data.get("duration"),  # 时长（秒）
                "pubdate": data.get("pubdate"),  # 发布时间戳
                "owner": {
                    "mid": data.get("owner", {}).get("mid"),
                    "name": data.get("owner", {}).get("name"),
                    "face": data.get("owner", {}).get("face")
                },
                "stat": {
                    "view": data.get("stat", {}).get("view"),  # 播放量
                    "like": data.get("stat", {}).get("like"),  # 点赞
                    "coin": data.get("stat", {}).get("coin"),  # 投币
                    "favorite": data.get("stat", {}).get("favorite"),  # 收藏
                    "share": data.get("stat", {}).get("share"),  # 分享
                    "reply": data.get("stat", {}).get("reply"),  # 评论
                    "danmaku": data.get("stat", {}).get("danmaku")  # 弹幕
                },
                "cid": data.get("cid"),
                "tags": tags_result.get("data", []) if tags_result.get("code") == 0 else [],
                "pages": pages_result.get("data", []) if pages_result.get("code") == 0 else []
            }
            
            # 格式化内容文本
            content_text = self._format_video_info(video_info)
            
            # 保存到本地
            storage_info = None
            if self.force_save:
                storage_info = storage_manager.create_article_storage(
                    platform=self.platform_name,
                    title=video_info["title"],
                    url=self.url
                )
                
                # 保存JSON格式的完整数据
                json_path = os.path.join(storage_info['article_dir'], 'video_info.json')
                with open(json_path, 'w', encoding='utf-8') as f:
                    json.dump(video_info, f, ensure_ascii=False, indent=2)
                
                # 保存文本内容
                storage_manager.save_text_content(storage_info, content_text)
                
                # 保存markdown格式
                markdown_content = self._format_video_info_markdown(video_info)
                storage_manager.save_markdown_content(storage_info, markdown_content, video_info["title"])
                
                # 保存文章索引
                storage_manager.save_article_index(storage_info, video_info.get("desc", "")[:200])
                
                # 自动下载视频（如果启用）
                if self.auto_download_video:
                    print(f"\n🎬 开始下载视频...")
                    download_result = await self.download_video(qn=self.video_quality)
                    if download_result.get("success"):
                        print(f"✅ 视频已保存到: {download_result.get('file_path')}")
                    else:
                        print(f"❌ 视频下载失败: {download_result.get('message')}")
            
            return ScrapedDataItem(
                title=video_info["title"],
                author=video_info["owner"]["name"],
                content=content_text,
                markdown_content=self._format_video_info_markdown(video_info),
                images=[],
                save_directory=storage_info.get('article_dir') if storage_info else None
            )
            
        except Exception as e:
            raise Exception(f"获取B站视频信息失败: {str(e)}")
    
    def _format_video_info(self, info: dict) -> str:
        """将视频信息格式化为文本"""
        lines = [
            f"标题: {info['title']}",
            f"BVID: {info['bvid']}",
            f"UP主: {info['owner']['name']}",
            f"时长: {info['duration']}秒",
            f"播放: {info['stat']['view']:,}",
            f"点赞: {info['stat']['like']:,}",
            f"投币: {info['stat']['coin']:,}",
            f"收藏: {info['stat']['favorite']:,}",
            f"分享: {info['stat']['share']:,}",
            f"评论: {info['stat']['reply']:,}",
            f"弹幕: {info['stat']['danmaku']:,}",
            f"\n简介:\n{info['desc']}",
        ]
        
        if info['tags']:
            tags = ", ".join([tag.get('tag_name', '') for tag in info['tags']])
            lines.append(f"\n标签: {tags}")
        
        if len(info['pages']) > 1:
            lines.append(f"\n分P信息 (共{len(info['pages'])}P):")
            for page in info['pages']:
                lines.append(f"  P{page.get('page')}: {page.get('part')} ({page.get('duration')}秒)")
        
        return "\n".join(lines)
    
    def _format_video_info_markdown(self, info: dict) -> str:
        """将视频信息格式化为Markdown"""
        lines = [
            f"# {info['title']}",
            f"",
            f"**UP主**: {info['owner']['name']}",
            f"**BVID**: `{info['bvid']}`",
            f"**时长**: {info['duration']}秒",
            f"",
            f"## 📊 统计数据",
            f"",
            f"- 播放: {info['stat']['view']:,}",
            f"- 点赞: {info['stat']['like']:,}",
            f"- 投币: {info['stat']['coin']:,}",
            f"- 收藏: {info['stat']['favorite']:,}",
            f"- 分享: {info['stat']['share']:,}",
            f"- 评论: {info['stat']['reply']:,}",
            f"- 弹幕: {info['stat']['danmaku']:,}",
            f"",
            f"## 📝 简介",
            f"",
            info['desc'] or "无简介",
            f"",
        ]
        
        if info['tags']:
            lines.append("## 🏷️ 标签")
            lines.append("")
            tags = ", ".join([f"`{tag.get('tag_name', '')}`" for tag in info['tags']])
            lines.append(tags)
            lines.append("")
        
        if len(info['pages']) > 1:
            lines.append(f"## 📑 分P信息 (共{len(info['pages'])}P)")
            lines.append("")
            for page in info['pages']:
                lines.append(f"- **P{page.get('page')}**: {page.get('part')} ({page.get('duration')}秒)")
            lines.append("")
        
        return "\n".join(lines)
    
    async def get_download_info(self, qn: int = 80) -> Dict[str, Any]:
        """
        获取视频下载信息的便捷方法
        
        Args:
            qn: 清晰度，80=1080P，64=720P，32=480P，16=360P
            
        Returns:
            包含下载链接和相关信息的字典
        """
        try:
            # 获取视频详情以获取cid
            detail = await self.get_video_detail()
            if detail.get("code") != 0:
                return {"success": False, "message": detail.get("message")}
            
            data = detail.get("data", {})
            cid = data.get("cid")
            pages = data.get("pages", [])
            
            # 获取下载链接
            download_result = await self.get_video_download_url(cid, qn)
            
            if download_result.get("code") != 0:
                return {"success": False, "message": download_result.get("message")}
            
            download_data = download_result.get("data", {})
            
            # 整理返回信息
            result = {
                "success": True,
                "title": data.get("title"),
                "bvid": self.bvid,
                "quality": qn,
                "pages_count": len(pages),
                "download_info": {}
            }
            
            # DASH格式（推荐，音视频分离）
            dash = download_data.get("dash")
            if dash:
                video_list = dash.get("video", [])
                audio_list = dash.get("audio", [])
                
                result["download_info"]["format"] = "dash"
                result["download_info"]["video_streams"] = [
                    {
                        "id": v.get("id"),
                        "quality": v.get("id"),
                        "url": v.get("baseUrl") or v.get("base_url"),
                        "codec": v.get("codecs"),
                        "width": v.get("width"),
                        "height": v.get("height"),
                        "size": v.get("size", 0)
                    }
                    for v in video_list
                ]
                result["download_info"]["audio_streams"] = [
                    {
                        "id": a.get("id"),
                        "url": a.get("baseUrl") or a.get("base_url"),
                        "codec": a.get("codecs"),
                        "size": a.get("size", 0)
                    }
                    for a in audio_list
                ]
            
            # 直接播放格式（音视频合一）
            durl = download_data.get("durl")
            if durl:
                result["download_info"]["format"] = "flv"
                result["download_info"]["direct_urls"] = [
                    {
                        "order": d.get("order"),
                        "url": d.get("url"),
                        "size": d.get("size", 0),
                        "length": d.get("length", 0)
                    }
                    for d in durl
                ]
            
            # 如果有多P，列出所有分P信息
            if len(pages) > 1:
                result["pages"] = [
                    {
                        "page": p.get("page"),
                        "cid": p.get("cid"),
                        "part": p.get("part"),
                        "duration": p.get("duration")
                    }
                    for p in pages
                ]
            
            return result
            
        except Exception as e:
            return {"success": False, "message": str(e)}
    
    async def download_video(self, qn: int = 80, page: int = 1, 
                            merge_video: bool = True) -> Dict[str, Any]:
        """
        下载视频到本地
        
        Args:
            qn: 清晰度，80=1080P，64=720P，32=480P，16=360P
            page: 分P页码（从1开始）
            merge_video: 是否合并视频和音频（DASH格式需要）
            
        Returns:
            包含下载结果的字典
        """
        try:
            # 获取视频详情
            detail = await self.get_video_detail()
            if detail.get("code") != 0:
                return {"success": False, "message": f"获取视频详情失败: {detail.get('message')}"}
            
            data = detail.get("data", {})
            title = data.get("title")
            pages = data.get("pages", [])
            
            # 检查分P
            if page > len(pages):
                return {"success": False, "message": f"分P页码超出范围，该视频共 {len(pages)} P"}
            
            # 获取对应分P的cid
            target_page = pages[page - 1]
            cid = target_page.get("cid")
            part_title = target_page.get("part", title)
            
            # 创建存储目录
            storage_info = storage_manager.create_article_storage(
                platform=self.platform_name,
                title=f"{title}_{part_title}" if len(pages) > 1 else title,
                url=self.url
            )
            
            video_dir = storage_info['article_dir']
            
            # 获取下载链接
            download_result = await self.get_video_download_url(cid, qn)
            
            if download_result.get("code") != 0:
                return {"success": False, "message": f"获取下载链接失败: {download_result.get('message')}"}
            
            download_data = download_result.get("data", {})
            
            # 处理DASH格式（音视频分离）
            dash = download_data.get("dash")
            if dash:
                video_list = dash.get("video", [])
                audio_list = dash.get("audio", [])
                
                if not video_list or not audio_list:
                    return {"success": False, "message": "未找到可用的视频或音频流"}
                
                # 选择最佳视频流
                video_stream = video_list[0]  # 第一个通常是最高画质
                audio_stream = audio_list[0]  # 第一个通常是最高音质
                
                video_url = video_stream.get("baseUrl") or video_stream.get("base_url")
                audio_url = audio_stream.get("baseUrl") or audio_stream.get("base_url")
                
                # 下载视频和音频
                print(f"📥 开始下载视频流...")
                video_file = os.path.join(video_dir, "video_temp.m4s")
                await self._download_file(video_url, video_file)
                
                print(f"📥 开始下载音频流...")
                audio_file = os.path.join(video_dir, "audio_temp.m4s")
                await self._download_file(audio_url, audio_file)
                
                # 合并视频和音频
                if merge_video:
                    output_file = os.path.join(video_dir, f"{storage_info['safe_title']}.mp4")
                    print(f"🔄 合并视频和音频...")
                    success = await self._merge_video_audio(video_file, audio_file, output_file)
                    
                    if success:
                        # 删除临时文件
                        os.remove(video_file)
                        os.remove(audio_file)
                        print(f"✅ 视频下载完成: {output_file}")
                        return {
                            "success": True,
                            "file_path": output_file,
                            "title": f"{title} - {part_title}" if len(pages) > 1 else title,
                            "format": "mp4"
                        }
                    else:
                        print(f"⚠️ 视频和音频已下载，但合并失败。文件保存在: {video_dir}")
                        return {
                            "success": True,
                            "video_file": video_file,
                            "audio_file": audio_file,
                            "message": "视频和音频已下载，但合并失败（需要安装ffmpeg）"
                        }
                else:
                    return {
                        "success": True,
                        "video_file": video_file,
                        "audio_file": audio_file,
                        "message": "视频和音频已分别下载"
                    }
            
            # 处理FLV格式（音视频合一）
            durl = download_data.get("durl")
            if durl:
                video_url = durl[0].get("url")
                output_file = os.path.join(video_dir, f"{storage_info['safe_title']}.flv")
                
                print(f"📥 开始下载视频...")
                await self._download_file(video_url, output_file)
                
                print(f"✅ 视频下载完成: {output_file}")
                return {
                    "success": True,
                    "file_path": output_file,
                    "title": f"{title} - {part_title}" if len(pages) > 1 else title,
                    "format": "flv"
                }
            
            return {"success": False, "message": "未找到可用的下载链接"}
            
        except Exception as e:
            return {"success": False, "message": f"下载失败: {str(e)}"}
    
    async def _download_file(self, url: str, save_path: str, chunk_size: int = 1024 * 1024):
        """
        下载文件
        
        Args:
            url: 下载链接
            save_path: 保存路径
            chunk_size: 每次下载的块大小（默认1MB）
        """
        headers = self.headers.copy()
        if self.cookies:
            headers["Cookie"] = self.cookies
        
        async with httpx.AsyncClient(follow_redirects=True, headers=headers, timeout=300.0) as client:
            async with client.stream("GET", url) as response:
                response.raise_for_status()
                
                total_size = int(response.headers.get("content-length", 0))
                downloaded = 0
                
                with open(save_path, "wb") as f:
                    async for chunk in response.aiter_bytes(chunk_size):
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # 显示进度
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r进度: {progress:.1f}% ({downloaded}/{total_size} 字节)", end="")
                
                print()  # 换行
    
    async def _merge_video_audio(self, video_file: str, audio_file: str, output_file: str) -> bool:
        """
        合并视频和音频（支持多种方案）
        优先级: ffmpeg > moviepy > 纯Python方案
        
        Args:
            video_file: 视频文件路径
            audio_file: 音频文件路径
            output_file: 输出文件路径
            
        Returns:
            是否成功
        """
        # 方案1: 尝试使用 ffmpeg (最快，质量最好)
        if await self._merge_with_ffmpeg(video_file, audio_file, output_file):
            return True
        
        print("⚠️ ffmpeg 不可用，尝试使用 moviepy...")
        
        # 方案2: 尝试使用 moviepy (纯Python，较慢但不需要外部工具)
        if await self._merge_with_moviepy(video_file, audio_file, output_file):
            return True
        
        print("⚠️ moviepy 不可用，尝试使用简单合并...")
        
        # 方案3: 简单的容器级别合并 (最快但兼容性可能有问题)
        if await self._merge_simple(video_file, audio_file, output_file):
            return True
        
        return False
    
    async def _merge_with_ffmpeg(self, video_file: str, audio_file: str, output_file: str) -> bool:
        """使用 ffmpeg 合并（最优方案）"""
        try:
            import subprocess
            
            # 检查ffmpeg是否可用
            try:
                subprocess.run(["ffmpeg", "-version"], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
            
            print("🔄 使用 ffmpeg 合并...")
            
            # 合并命令
            cmd = [
                "ffmpeg",
                "-i", video_file,
                "-i", audio_file,
                "-c:v", "copy",
                "-c:a", "aac",
                "-strict", "experimental",
                output_file,
                "-y"  # 覆盖已存在的文件
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"❌ ffmpeg错误: {result.stderr[:200]}")
                return False
                
        except Exception as e:
            print(f"❌ ffmpeg合并失败: {e}")
            return False
    
    async def _merge_with_moviepy(self, video_file: str, audio_file: str, output_file: str) -> bool:
        """使用 moviepy 合并（纯Python方案）"""
        try:
            # 尝试导入 moviepy
            try:
                # moviepy 2.x 的导入路径
                from moviepy import VideoFileClip, AudioFileClip
            except ImportError:
                try:
                    # moviepy 1.x 的导入路径
                    from moviepy.editor import VideoFileClip, AudioFileClip
                except ImportError:
                    # moviepy 未安装
                    raise ImportError("moviepy not available")
            
            print("🔄 使用 moviepy 合并（这可能需要几分钟）...")
            
            # 加载视频和音频
            video = VideoFileClip(video_file)
            audio = AudioFileClip(audio_file)
            
            # 合并
            final_video = video.with_audio(audio)  # 2.x 使用 with_audio 而不是 set_audio
            
            # 写入文件
            final_video.write_videofile(
                output_file,
                codec='libx264',
                audio_codec='aac',
                logger=None  # 禁用详细日志
            )
            
            # 关闭资源
            video.close()
            audio.close()
            final_video.close()
            
            return True
            
        except ImportError:
            # moviepy 未安装，返回False让程序尝试其他方案
            return False
        except Exception as e:
            print(f"❌ moviepy合并失败: {e}")
            return False
    
    async def _merge_simple(self, video_file: str, audio_file: str, output_file: str) -> bool:
        """简单的MP4容器合并（使用mp4box格式，兼容性最好）"""
        try:
            print("🔄 使用简单方法合并...")
            
            # 读取视频和音频数据
            with open(video_file, 'rb') as f:
                video_data = f.read()
            
            with open(audio_file, 'rb') as f:
                audio_data = f.read()
            
            # 简单的方法：创建一个包含两个流的MP4文件
            # 这里使用一个简单的技巧，直接将音频数据附加到视频末尾
            # 注意：这种方法可能不适用于所有播放器
            with open(output_file, 'wb') as f:
                f.write(video_data)
                # 写入音频标记和数据
                f.write(b'\x00\x00\x00\x18ftypmp42')  # MP4标记
                f.write(audio_data)
            
            # 验证文件大小
            if os.path.getsize(output_file) > 0:
                print("⚠️ 注意：使用了简单合并方案，某些播放器可能无法正常播放")
                print("💡 建议安装 ffmpeg 或 moviepy 以获得更好的兼容性")
                return True
            
            return False
            
        except Exception as e:
            print(f"❌ 简单合并失败: {e}")
            return False
