"""
抖音视频下载工具 - 独立模块
支持通过分享链接直接下载视频
自动从浏览器数据加载Cookie和User-Agent
"""

import asyncio
import httpx
import re
import os
import json
from pathlib import Path
from urllib.parse import urlencode
from typing import Dict, Any, Optional

# ============================================
# 配置区域
# ============================================

def load_cookie_from_browser() -> str:
    """从浏览器数据加载Cookie"""
    try:
        user_data_dir = "./chrome_user_data"
        cookies_file = os.path.join(user_data_dir, "login_data", "douyin_cookies.json")
        
        if os.path.exists(cookies_file):
            with open(cookies_file, 'r', encoding='utf-8') as f:
                cookies_list = json.load(f)
                cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_list])
                print(f"📂 从浏览器数据加载Cookie，共 {len(cookies_list)} 个")
                return cookie_str
    except Exception as e:
        print(f"⚠️ 加载Cookie失败: {e}")
    
    return ""

def load_user_agent_from_browser() -> str:
    """从浏览器数据加载User-Agent"""
    try:
        user_data_dir = "./chrome_user_data"
        ua_file = os.path.join(user_data_dir, "login_data", "user_agent.txt")
        
        if os.path.exists(ua_file):
            with open(ua_file, 'r', encoding='utf-8') as f:
                user_agent = f.read().strip()
                if user_agent:
                    print(f"📂 从浏览器数据加载User-Agent")
                    return user_agent
    except Exception as e:
        print(f"⚠️ 加载User-Agent失败: {e}")
    
    return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

# 默认从浏览器数据加载（如果可用）
COOKIE = load_cookie_from_browser()
USER_AGENT = load_user_agent_from_browser()

# 如果浏览器数据不可用，使用手动配置的Cookie（向后兼容）
if not COOKIE:
    print("💡 提示: 未找到浏览器数据，可以手动在下方配置Cookie")
    # 从浏览器开发者工具的Network标签页复制完整的Cookie字符串
    COOKIE = """__ac_nonce=068e36ed20084903da92d; __ac_signature=_02B4Z6wo00f01tdVnwgAAIDCmnSmocHh-0bXZJuAAN1D54; __security_mc_1_s_sdk_cert_key=efc4b9a3-458e-ad5d; __security_mc_1_s_sdk_crypt_sdk=b7c45f8d-4613-a463; __security_mc_1_s_sdk_sign_data_key_web_protect=56392f0a-4435-8c35; __security_server_data_status=1; _bd_ticket_crypt_cookie=cfd07fb8d2a0d1025f42c2ee17c61466; architecture=amd64; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCTEZPeTFzelRCNnVwN3JidytORXVWc3U2WlRuMFlnUFJIVnhqWVVndWZpelNJK2tBNmsyM3kzZmw3NlcyT2dOOHhQRTZLaVExNTA3eGNDVThCdWVxZEk9IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ==; bd_ticket_guard_client_data_v2=eyJyZWVfcHVibGljX2tleSI6IkJMRk95MXN6VEI2dXA3cmJ3K05FdVZzdTZaVG4wWWdQUkhWeGpZVWd1Zml6U0kra0E2azIzeTNmbDc2VzJPZ044eFBFNktpUTE1MDd4Y0NVOEJ1ZXFkST0iLCJ0c19zaWduIjoidHMuMi5jYjkyMGJlZjRiY2I0OTg2OGFiNTI2YTBhZTRlOThhNzA2YzI5NzE3MDdhNTBhNjNmYjk1MDRjYjZiYzA3MTFkYzRmYmU4N2QyMzE5Y2YwNTMxODYyNGNlZGExNDkxMWNhNDA2ZGVkYmViZWRkYjJlMzBmY2U4ZDRmYTAyNTc1ZCIsInJlcV9jb250ZW50Ijoic2VjX3RzIiwicmVxX3NpZ24iOiJGdm1HWGVQQXNYQVhDSTN4dXBVRGd6Z3o2dmtSdm1iTGwvTU9tZ2hGVWVBPSIsInNlY190cyI6IiNlSWoyRFdVdDlwMTNHdUZwQlNvZUxXbXJ5aC9Oa1hHRFlkMTRwMzg4UHowRGtRNWh1eXBIUmdEbTZTeEUifQ==; bd_ticket_guard_client_web_domain=2; sessionid=56d86eaa9e312f2179f3fad262f61f71; sessionid_ss=56d86eaa9e312f2179f3fad262f61f71; ttwid=1|kua-ocR2BbNzx6ePnQHIFsTgf1Yvln-g-DbFs4qBros|1759735568|78957873a464e1589cf8218af687e7d1120ec20d5b7e14a056ef4fe50021ced1"""

# ============================================
# ABogus签名生成 (简化版)
# ============================================

class SimpleBogus:
    """简化的Bogus签名生成器"""
    
    @staticmethod
    def get_value(params: dict) -> str:
        """生成a_bogus参数 - 这里使用简化实现"""
        # 注意:实际的ABogus算法很复杂,这里使用占位符
        # 如果需要完整功能,请使用原项目的signature.py
        return "placeholder_abogus"


# ============================================
# 视频下载器类
# ============================================

class DouyinVideoDownloader:
    """抖音视频下载器 - 独立版本"""
    
    USER_POST_ENDPOINT = "https://www.douyin.com/aweme/v1/web/aweme/post/"
    AWEME_DETAIL_ENDPOINT = "https://www.douyin.com/aweme/v1/web/aweme/detail/"
    
    def __init__(self, cookie: str = COOKIE, user_agent: str = USER_AGENT):
        """
        初始化下载器
        
        Args:
            cookie: 抖音Cookie
            user_agent: User-Agent
        """
        self.cookie = cookie
        self.user_agent = user_agent
        self.headers = {
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "User-Agent": user_agent,
            "Referer": "https://www.douyin.com/",
            "Cookie": cookie
        }
        self.client = httpx.AsyncClient(
            headers=self.headers,
            timeout=30.0,
            follow_redirects=True,
            http2=True
        )
    
    async def parse_share_url(self, share_url: str) -> Dict[str, str]:
        """
        解析分享链接,获取作品ID和用户ID
        
        支持的链接格式:
        - https://v.douyin.com/xxxxxx/  (短链接)
        - https://www.douyin.com/video/7520726025291058482
        - https://www.douyin.com/user/MS4wLjABAAAA.../video/7520726025291058482
        
        Args:
            share_url: 抖音分享链接
            
        Returns:
            dict: {'aweme_id': xxx, 'sec_user_id': xxx, 'url': xxx}
        """
        print(f"\n🔍 正在解析链接...")
        print(f"   输入: {share_url[:80]}...")
        
        try:
            # 如果是短链接,先重定向获取真实链接
            if 'v.douyin.com' in share_url or 'iesdouyin.com' in share_url:
                async with httpx.AsyncClient(follow_redirects=True, timeout=10) as client:
                    response = await client.get(share_url)
                    real_url = str(response.url)
                    print(f"   重定向: {real_url[:80]}...")
                    share_url = real_url
            
            # 从URL中提取作品ID
            aweme_id = None
            sec_user_id = None
            
            # 匹配作品ID: /video/数字
            video_match = re.search(r'/video/(\d+)', share_url)
            if video_match:
                aweme_id = video_match.group(1)
            
            # 匹配用户ID: /user/MS4wLjABAAAA...
            user_match = re.search(r'/user/([^/\?]+)', share_url)
            if user_match:
                sec_user_id = user_match.group(1)
            
            # 也可以从modal_id参数中获取
            if not aweme_id:
                modal_match = re.search(r'modal_id=(\d+)', share_url)
                if modal_match:
                    aweme_id = modal_match.group(1)
            
            # 如果只有视频ID没有用户ID,尝试通过访问页面获取重定向URL
            if aweme_id and not sec_user_id:
                print(f"   ⚠️  链接缺少用户ID,尝试自动获取...")
                sec_user_id = await self._fetch_user_id_from_video(aweme_id)
                if sec_user_id:
                    print(f"   ✓ 成功获取用户ID: {sec_user_id[:20]}...")
                else:
                    print(f"   × 无法自动获取用户ID")
            
            if aweme_id:
                print(f"✅ 解析成功!")
                print(f"   作品ID: {aweme_id}")
                if sec_user_id:
                    print(f"   用户ID: {sec_user_id[:20]}...")
            else:
                print(f"❌ 未能提取作品ID")
            
            return {
                'aweme_id': aweme_id,
                'sec_user_id': sec_user_id,
                'url': share_url
            }
            
        except Exception as e:
            print(f"❌ 解析链接失败: {e}")
            return {}
    
    async def _fetch_user_id_from_video(self, aweme_id: str) -> Optional[str]:
        """
        从视频ID获取用户ID (多种方法尝试)
        
        Args:
            aweme_id: 视频ID
            
        Returns:
            str: 用户ID,失败返回None
        """
        # 方法1: 通过重定向获取
        try:
            video_url = f"https://www.douyin.com/video/{aweme_id}"
            headers = {
                **self.headers,
                'Cookie': self.cookie,
            }
            
            async with httpx.AsyncClient(follow_redirects=True, timeout=15) as client:
                response = await client.get(video_url, headers=headers)
                final_url = str(response.url)
                
                # 检查重定向后的URL是否包含用户ID
                user_match = re.search(r'/user/([^/\?]+)', final_url)
                if user_match:
                    return user_match.group(1)
                
                # 方法2: 从HTML页面解析
                html = response.text
                
                # 尝试从HTML中提取用户ID
                # 搜索 "authorSecId":"MS4wLjABAAAA..." 模式
                sec_id_match = re.search(r'"authorSecId"\s*:\s*"([^"]+)"', html)
                if sec_id_match:
                    return sec_id_match.group(1)
                
                # 搜索 sec_uid= 参数
                sec_uid_match = re.search(r'sec_uid=([^&\s"\']+)', html)
                if sec_uid_match:
                    return sec_uid_match.group(1)
                
        except Exception as e:
            print(f"      方法1失败: {e}")
        
        # 方法3: 尝试通过详情接口获取
        try:
            aweme_detail = await self.fetch_aweme_detail(aweme_id)
            if aweme_detail and isinstance(aweme_detail, dict):
                author = aweme_detail.get('author', {})
                sec_uid = author.get('sec_uid')
                if sec_uid:
                    return sec_uid
        except Exception as e:
            print(f"      方法2失败: {e}")
        
        return None
    
    async def fetch_user_posts(self, sec_user_id: str, max_cursor: int = 0, 
                              count: int = 20) -> Dict[str, Any]:
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
        
        # 生成a_bogus参数
        a_bogus = SimpleBogus.get_value(params)
        params["a_bogus"] = a_bogus
        
        url = f"{self.USER_POST_ENDPOINT}?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"请求失败: {e}")
            return {"status_code": -1}
    
    async def fetch_aweme_detail(self, aweme_id: str) -> Dict[str, Any]:
        """
        通过作品ID直接获取作品详情
        
        Args:
            aweme_id: 作品ID
            
        Returns:
            dict: 作品详情数据
        """
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
        
        # 生成a_bogus参数
        a_bogus = SimpleBogus.get_value(params)
        params["a_bogus"] = a_bogus
        
        url = f"{self.AWEME_DETAIL_ENDPOINT}?{urlencode(params)}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            data = response.json()
            
            # 检查返回数据
            if data.get("status_code") == 0:
                aweme_detail = data.get("aweme_detail")
                if aweme_detail:
                    return aweme_detail
            
            # 如果详情接口返回空,尝试从HTML页面解析
            print(f"   详情接口返回空数据,尝试其他方法...")
            return await self.fetch_aweme_from_webpage(aweme_id)
            
        except Exception as e:
            print(f"   请求详情失败: {e}")
            # 尝试从网页获取
            return await self.fetch_aweme_from_webpage(aweme_id)
    
    async def fetch_aweme_from_webpage(self, aweme_id: str) -> Optional[dict]:
        """
        从网页中解析作品信息(备用方法)
        
        Args:
            aweme_id: 作品ID
            
        Returns:
            dict: 作品信息,失败返回None
        """
        try:
            # 访问视频页面,需要Cookie
            url = f"https://www.douyin.com/video/{aweme_id}"
            
            headers = {
                **self.headers,
                'Cookie': self.cookie,
            }
            
            response = await self.client.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            html = response.text
            
            # 从HTML中提取数据
            # 抖音的视频数据通常在 <script id="RENDER_DATA"> 标签中
            import json
            import urllib.parse
            
            print(f"   正在解析HTML...")
            
            # 查找RENDER_DATA
            if 'id="RENDER_DATA"' in html:
                print(f"   ✓ 找到RENDER_DATA标签")
                start = html.find('id="RENDER_DATA"')
                if start > 0:
                    start = html.find('>', start) + 1
                    end = html.find('</script>', start)
                    if end > start:
                        data_str = html[start:end].strip()
                        print(f"   数据长度: {len(data_str)} 字符")
                        # 解码URL编码的数据
                        try:
                            decoded = urllib.parse.unquote(data_str)
                            print(f"   解码后长度: {len(decoded)} 字符")
                            data = json.loads(decoded)
                            print(f"   ✓ JSON解析成功")
                            
                            # 提取视频详情
                            # 数据结构可能是: data['app']['videoDetail'] 或类似路径
                            if isinstance(data, dict):
                                print(f"   顶层键: {list(data.keys())[:10]}")
                                
                                # 递归搜索包含 aweme_id 的字典
                                def find_aweme_data(obj, depth=0, max_depth=5):
                                    """递归查找包含 aweme_id 的数据"""
                                    if depth > max_depth:
                                        return None
                                    
                                    if isinstance(obj, dict):
                                        # 如果当前字典包含 aweme_id,可能就是视频数据
                                        if 'aweme_id' in obj or 'awemeId' in obj:
                                            return obj
                                        
                                        # 递归搜索子字典
                                        for key, value in obj.items():
                                            result = find_aweme_data(value, depth + 1, max_depth)
                                            if result:
                                                return result
                                    
                                    elif isinstance(obj, list):
                                        # 搜索列表中的第一个元素
                                        for item in obj:
                                            result = find_aweme_data(item, depth + 1, max_depth)
                                            if result:
                                                return result
                                    
                                    return None
                                
                                aweme = find_aweme_data(data)
                                
                                if aweme:
                                    print(f"   ✓ 找到包含视频数据的字典")
                                    if isinstance(aweme, dict):
                                        print(f"   数据键(前10): {list(aweme.keys())[:10]}")
                                    return aweme
                                else:
                                    print(f"   × 未找到包含 aweme_id 的数据")
                                
                                # 打印app的结构以便调试
                                if 'app' in data and isinstance(data['app'], dict):
                                    print(f"   app的键: {list(data['app'].keys())[:10]}")
                        except json.JSONDecodeError as je:
                            print(f"   × JSON解析失败: {je}")
                            print(f"   前100字符: {decoded[:100] if 'decoded' in locals() else data_str[:100]}")
                        except Exception as parse_e:
                            print(f"   × 解析异常: {parse_e}")
            else:
                print(f"   × HTML中未找到RENDER_DATA标签")
            
            print(f"   无法从网页解析数据")
            return None
            
        except Exception as e:
            print(f"   从网页获取失败: {e}")
            return None
    
    async def find_video_in_posts(self, sec_user_id: str, aweme_id: str, 
                                 max_pages: int = 20) -> Optional[dict]:
        """
        从用户作品列表中查找指定视频
        
        Args:
            sec_user_id: 用户ID
            aweme_id: 作品ID
            max_pages: 最多查找页数
            
        Returns:
            dict: 作品信息,未找到返回None
        """
        print(f"\n🔎 正在搜索作品...")
        
        max_cursor = 0
        
        for page in range(max_pages):
            res = await self.fetch_user_posts(sec_user_id, max_cursor, 20)
            
            if res.get("status_code") != 0:
                print(f"   获取失败: {res.get('status_msg', '未知错误')}")
                return None
            
            aweme_list = res.get("aweme_list", [])
            
            # 在当前页查找目标作品
            for aweme in aweme_list:
                if aweme.get('aweme_id') == aweme_id:
                    print(f"✅ 找到作品! (第{page+1}页)")
                    return aweme
            
            # 检查是否还有更多
            if not res.get("has_more", False):
                print(f"   已搜索完所有 {page+1} 页")
                break
            
            max_cursor = res.get("max_cursor", 0)
            
            if (page + 1) % 5 == 0:
                print(f"   已搜索 {page+1} 页...")
            
            await asyncio.sleep(0.3)  # 避免请求过快
        
        print(f"❌ 未找到作品 (搜索了{min(page+1, max_pages)}页)")
        return None
    
    def extract_video_info(self, aweme: dict) -> dict:
        """从作品数据中提取视频信息"""
        video = aweme.get('video', {})
        author = aweme.get('author', {})
        statistics = aweme.get('statistics', {})
        
        # 获取视频地址
        play_addr = video.get('play_addr', {}).get('url_list', [])
        download_addr = video.get('download_addr', {}).get('url_list', [])
        
        # 获取不同清晰度
        bit_rate = video.get('bit_rate', [])
        quality_urls = {}
        for item in bit_rate:
            gear_name = item.get('gear_name', 'unknown')
            urls = item.get('play_addr', {}).get('url_list', [])
            if urls:
                quality_urls[gear_name] = urls[0]
        
        return {
            'aweme_id': aweme.get('aweme_id'),
            'desc': aweme.get('desc', ''),
            'create_time': aweme.get('create_time', 0),
            'author': {
                'nickname': author.get('nickname', ''),
                'unique_id': author.get('unique_id', ''),
                'sec_uid': author.get('sec_uid', ''),
            },
            'video': {
                'duration': video.get('duration', 0) / 1000,  # 转为秒
                'width': video.get('width', 0),
                'height': video.get('height', 0),
                'ratio': video.get('ratio', ''),
                'cover_url': video.get('cover', {}).get('url_list', [''])[0],
                'play_url': play_addr[0] if play_addr else '',
                'download_url': download_addr[0] if download_addr else '',
                'quality_urls': quality_urls,
            },
            'statistics': {
                'digg_count': statistics.get('digg_count', 0),
                'comment_count': statistics.get('comment_count', 0),
                'share_count': statistics.get('share_count', 0),
                'collect_count': statistics.get('collect_count', 0),
            }
        }
    
    def print_video_info(self, info: dict):
        """打印视频信息"""
        print("\n" + "="*80)
        print("📹 视频信息")
        print("="*80)
        
        print(f"\n📝 基本信息:")
        print(f"   作品ID: {info['aweme_id']}")
        desc = info['desc']
        print(f"   描述: {desc[:60]}{'...' if len(desc) > 60 else ''}")
        
        from datetime import datetime
        if info['create_time']:
            dt = datetime.fromtimestamp(info['create_time'])
            print(f"   发布时间: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        
        author = info['author']
        print(f"\n👤 作者:")
        print(f"   昵称: {author['nickname']}")
        if author['unique_id']:
            print(f"   抖音号: {author['unique_id']}")
        
        video = info['video']
        print(f"\n🎬 视频:")
        print(f"   时长: {video['duration']:.1f} 秒")
        print(f"   分辨率: {video['width']}x{video['height']}")
        
        stats = info['statistics']
        print(f"\n📊 数据:")
        print(f"   👍 点赞: {stats['digg_count']:,}")
        print(f"   💬 评论: {stats['comment_count']:,}")
        print(f"   🔗 分享: {stats['share_count']:,}")
        print(f"   ⭐ 收藏: {stats['collect_count']:,}")
    
    async def download_video(self, video_url: str, save_path: str) -> bool:
        """
        下载视频
        
        Args:
            video_url: 视频下载地址
            save_path: 保存路径
            
        Returns:
            bool: 是否下载成功
        """
        try:
            print(f"\n⬇️  开始下载视频...")
            
            # 创建保存目录
            Path(save_path).parent.mkdir(parents=True, exist_ok=True)
            
            # 下载视频
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream('GET', video_url, headers={
                    'User-Agent': self.user_agent,
                    'Referer': 'https://www.douyin.com/',
                }) as response:
                    response.raise_for_status()
                    
                    # 获取文件大小
                    total_size = int(response.headers.get('content-length', 0))
                    
                    # 写入文件
                    downloaded = 0
                    with open(save_path, 'wb') as f:
                        async for chunk in response.aiter_bytes(chunk_size=1024*1024):  # 1MB
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # 显示进度
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                mb_downloaded = downloaded / (1024*1024)
                                mb_total = total_size / (1024*1024)
                                print(f"\r   进度: {progress:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)", end='')
            
            print(f"\n✅ 下载完成!")
            print(f"   保存路径: {save_path}")
            return True
            
        except Exception as e:
            print(f"\n❌ 下载失败: {e}")
            return False
    
    async def download_from_url(self, share_url: str, save_dir: str = "downloads") -> str:
        """
        从分享链接下载视频 (主要方法)
        
        Args:
            share_url: 抖音分享链接
            save_dir: 保存目录
            
        Returns:
            str: 保存的文件路径,失败返回空字符串
        """
        print("\n" + "="*80)
        print("🎬 抖音视频下载工具")
        print("="*80)
        
        # 1. 解析链接
        parse_result = await self.parse_share_url(share_url)
        aweme_id = parse_result.get('aweme_id')
        sec_user_id = parse_result.get('sec_user_id')
        
        if not aweme_id:
            print("❌ 无法从链接中提取作品ID")
            return ""
        
        # 2. 查找视频
        aweme = None
        
        if sec_user_id:
            # 如果有用户ID,从用户作品列表中查找
            print(f"\n� 从用户作品列表中查找视频...")
            aweme = await self.find_video_in_posts(sec_user_id, aweme_id)
        else:
            # 如果没有用户ID,直接获取视频详情
            print(f"\n🔍 直接获取视频详情...")
            print(f"   视频ID: {aweme_id}")
            aweme = await self.fetch_aweme_detail(aweme_id)
        
        if not aweme:
            print("\n❌ 无法获取视频信息")
            print("\n💡 可能的原因:")
            print("   1. 视频已被删除或设为私密")
            print("   2. Cookie已过期,请更新config.py中的COOKIE")
            print("   3. 该视频需要登录才能访问")
            print("   4. 该视频链接格式不完整")
            print("\n💡 建议:")
            print("   • 请使用包含用户ID的完整链接,例如:")
            print("     https://www.douyin.com/user/MS4w.../video/755578...")
            print("   • 或者先在浏览器中打开视频,确认能正常访问后再尝试下载")
            print("   • 确保Cookie是最新的(从浏览器开发者工具复制)")
            return ""
        
        # 3. 提取视频信息
        video_info = self.extract_video_info(aweme)
        self.print_video_info(video_info)
        
        # 4. 获取下载地址
        video_data = video_info['video']
        download_url = video_data.get('download_url') or video_data.get('play_url')
        
        if not download_url:
            print("\n❌ 未找到视频下载地址")
            return ""
        
        # 5. 构造文件名
        author_name = video_info['author']['nickname']
        desc = video_info['desc'][:30]
        
        # 清理文件名中的非法字符
        safe_author = re.sub(r'[<>:"/\\|?*]', '_', author_name)
        safe_desc = re.sub(r'[<>:"/\\|?*]', '_', desc)
        
        filename = f"{safe_author}_{aweme_id}_{safe_desc}.mp4"
        save_path = str(Path(save_dir) / filename)
        
        # 6. 下载视频
        success = await self.download_video(download_url, save_path)
        
        if success:
            # 获取文件大小
            file_size = Path(save_path).stat().st_size / (1024*1024)
            print(f"   文件大小: {file_size:.2f} MB")
            return save_path
        else:
            return ""
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


# ============================================
# 使用示例
# ============================================

async def download_single_video(share_url: str, save_dir: str = "downloads"):
    """
    下载单个视频 - 简单接口
    
    Args:
        share_url: 抖音分享链接
        save_dir: 保存目录
        
    Returns:
        str: 保存的文件路径
    """
    downloader = DouyinVideoDownloader()
    
    try:
        save_path = await downloader.download_from_url(share_url, save_dir)
        return save_path
    finally:
        await downloader.close()


async def main():
    """主函数 - 演示使用"""
    
    print("="*80)
    print("抖音视频下载工具 - 独立版")
    print("="*80)
    print("\n💡 使用说明:")
    print("   1. 打开抖音网页版,找到想下载的视频")
    print("   2. 复制浏览器地址栏中的完整链接")
    print("   3. 链接应包含 /user/xxx/video/xxx 格式")
    print("   4. 将链接粘贴到下方代码中")
    print("\n" + "="*80)
    
    # ============================================
    # 在这里修改要下载的视频链接
    # ============================================
    
    share_url = "https://www.douyin.com/user/MS4wLjABAAAAac4yMAmgDe3eYvI3mwoFfg6W_-bNTvuc5YsAGoo-yaA/video/7520726025291058482"
    
    # 也支持短链接(如果包含用户信息)
    # share_url = "https://v.douyin.com/iRNBho6U/"
    
    # ============================================
    
    # 下载视频
    save_path = await download_single_video(share_url, save_dir="downloads")
    
    if save_path:
        print("\n" + "="*80)
        print("🎉 下载成功!")
        print(f"文件位置: {save_path}")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ 下载失败,请检查:")
        print("   1. Cookie是否正确配置")
        print("   2. 链接格式是否正确(需要包含用户ID)")
        print("   3. 网络连接是否正常")
        print("="*80)


if __name__ == "__main__":
    # 运行下载
    asyncio.run(main())
