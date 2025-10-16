"""
小红书Provider - 符合项目统一规范
支持获取单个笔记、批量搜索、用户笔记列表等功能
"""

import asyncio
import json
import os
import time
import random
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from loguru import logger

from .base import BaseProvider
from ..models import ScrapedDataItem
from ..storage import storage_manager
from ..utils.xhs.apis.xhs_pc_apis import XHS_Apis
from ..file_utils import get_file_extension
from ..utils.xhs.xhs_utils.data_util import handle_note_info, norm_str
from ..config import settings


class XiaohongshuProvider(BaseProvider):
    """
    小红书爬虫 - 符合项目统一规范
    
    继承BaseProvider，提供标准的笔记获取功能
    同时保留原有的批量搜索、用户笔记列表等高级功能
    """
    
    def __init__(
        self, 
        platform_name: str = "xiaohongshu",
        cookies: Optional[str] = None,
        user_agent: Optional[str] = None,
        max_pages: int = 10,
        count_per_page: int = 20,
        delay: float = 2.0,
        max_retries: int = 3,
        base_delay: float = 5.0,
        save_dir: str = "downloads/xiaohongshu"
    ):
        """
        初始化小红书Provider
        
        Args:
            platform_name: 平台名称，默认"xiaohongshu"
            cookies: 小红书cookies字符串，如果为None则自动从浏览器数据加载
            user_agent: User-Agent字符串，如果为None则自动从浏览器数据加载
            max_pages: 每个用户最多爬取的页数，默认10
            count_per_page: 每页获取的笔记数，默认20
            delay: 请求间隔（秒），默认2.0
            max_retries: 最大重试次数，默认3
            base_delay: 重试基础延时，默认5.0秒
            save_dir: 数据保存目录，默认"downloads/xiaohongshu"
        """
        # 使用虚拟参数初始化BaseProvider，小红书不使用这些参数
        super().__init__(
            url="", 
            rules={}, 
            save_images=True, 
            output_format="markdown",
            force_save=True,
            platform_name=platform_name
        )
        
        # 自动加载cookies和user_agent
        self.cookies = cookies or self._load_saved_cookies()
        self.user_agent = user_agent or self._load_user_agent()
        
        self.max_pages = max_pages
        self.count_per_page = count_per_page
        self.delay = delay
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.save_dir = save_dir
        
        self.xhs_apis = XHS_Apis()
        
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)
        
        logger.info(f"初始化小红书Provider完成")
    
    def _load_saved_cookies(self) -> str:
        """从浏览器数据加载保存的cookies"""
        cookie_file = Path(settings.LOGIN_DATA_DIR) / "xiaohongshu_cookies.json"
        if cookie_file.exists():
            try:
                with open(cookie_file, 'r', encoding='utf-8') as f:
                    cookies_data = json.load(f)
                    
                    # 处理两种可能的格式
                    if isinstance(cookies_data, dict):
                        if "value" in cookies_data and isinstance(cookies_data["value"], list):
                            # 格式: {"value": [{"name": "xxx", "value": "yyy"}, ...]}
                            cookie_list = cookies_data["value"]
                            cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in cookie_list])
                            logger.info(f"成功加载保存的cookies，共{len(cookie_list)}个")
                        else:
                            # 格式: {"name1": "value1", "name2": "value2", ...}
                            cookies_str = "; ".join([f"{k}={v}" for k, v in cookies_data.items()])
                            logger.info(f"成功加载保存的cookies，共{len(cookies_data)}个")
                    elif isinstance(cookies_data, list):
                        # 格式: [{"name": "xxx", "value": "yyy"}, ...]
                        cookies_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies_data])
                        logger.info(f"成功加载保存的cookies，共{len(cookies_data)}个")
                    else:
                        logger.warning(f"未知的cookies格式: {type(cookies_data)}")
                        return ""
                    
                    return cookies_str
            except Exception as e:
                logger.warning(f"加载cookies失败: {e}")
        
        logger.warning("未找到保存的cookies，请先运行 scripts/save_xiaohongshu_cookies.py")
        return ""
    
    def _load_user_agent(self) -> str:
        
        # 使用配置文件中的User-Agent
        logger.info("使用配置的User-Agent")
        return settings.USER_AGENT
    
    async def fetch_and_parse(self, note_url: Optional[str] = None) -> Optional[ScrapedDataItem]:
        """
        实现BaseProvider要求的方法：获取并解析单个笔记
        
        这是符合项目规范的统一接口，使用storage_manager保存数据
        
        Args:
            note_url: 笔记URL，如果为None则使用self.url
            
        Returns:
            ScrapedDataItem对象，失败返回None
        """
        if note_url is None:
            note_url = self.url
        
        if not note_url:
            logger.error("未提供笔记URL")
            return None
        
        logger.info(f"开始获取笔记: {note_url}")
        
        # 使用原有的fetch_note方法获取笔记
        note_data = await self.fetch_note(note_url)
        
        if not note_data:
            logger.error(f"获取笔记失败: {note_url}")
            return None
        
        # 提取笔记详情
        detail = self.extract_note_detail(note_data)
        
        # 获取基本信息
        title = detail.get('title', 'untitled')
        author = detail.get('author_name', 'Unknown')
        content_text = detail.get('content', '')
        
        # 创建Markdown格式内容
        markdown_content = f"""# {title}

**作者**: {author}
**发布时间**: {detail.get('publish_time', 'Unknown')}
**点赞数**: {detail.get('likes', 0)}
**收藏数**: {detail.get('collects', 0)}
**评论数**: {detail.get('comments', 0)}

## 正文

{content_text}

## 标签

{', '.join(detail.get('topics', []))}

---
原文链接: {note_url}
"""
        
        # 使用storage_manager创建存储目录
        storage_info = storage_manager.create_article_storage(
            platform=self.platform_name,
            title=title,
            url=note_url,
            author=author
        )
        
        # 保存Markdown内容
        storage_manager.save_markdown_content(
            storage_info=storage_info,
            content=markdown_content
        )
        
        # 保存纯文本内容
        storage_manager.save_text_content(
            storage_info=storage_info,
            content=content_text
        )
        
        # 保存原始JSON数据
        raw_data_path = os.path.join(storage_info['article_dir'], "raw_data.json")
        with open(raw_data_path, 'w', encoding='utf-8') as f:
            json.dump(note_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"笔记保存完成: {storage_info['article_dir']}")
        
        # 返回ScrapedDataItem
        return ScrapedDataItem(
            title=title,
            author=author,
            content=content_text,
            markdown_content=markdown_content,
            images=[],  # 小红书图片处理可以后续扩展
            save_directory=storage_info['article_dir']
        )

    async def fetch_note(
        self, 
        note_url: str, 
        proxies: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        获取单个笔记的详细信息
        
        Args:
            note_url: 笔记URL
            proxies: 代理设置
            
        Returns:
            API响应数据
        """
        note_info = None
        success = False
        msg = "未开始处理"
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    # 计算延时时间，每次重试增加延时
                    delay = self.base_delay * (2 ** (attempt - 1)) + random.uniform(1, 3)
                    logger.info(f'第{attempt}次重试，等待{delay:.1f}秒...')
                    await asyncio.sleep(delay)
                
                success, msg, response_data = self.xhs_apis.get_note_info(note_url, self.cookies, proxies or {})
                logger.info(f'API调用结果 (尝试{attempt + 1}): success={success}, msg={msg}')
                
                # 检查是否是限流错误
                if response_data and isinstance(response_data, dict):
                    if response_data.get('code') == 300013:  # 访问频次异常
                        logger.warning(f'检测到访问频次限制，第{attempt + 1}次尝试')
                        if attempt < self.max_retries:
                            continue
                        else:
                            success = False
                            msg = '重试次数用尽，仍然遇到访问频次限制'
                            break
                
                if success and response_data:
                    # 检查数据结构
                    if not isinstance(response_data, dict):
                        success = False  
                        msg = f'API返回数据不是字典格式: {type(response_data)}'
                    elif 'data' not in response_data:
                        success = False
                        msg = f'API返回数据中没有data字段，可用字段: {list(response_data.keys())}'
                    elif not isinstance(response_data['data'], dict):
                        success = False
                        msg = f'data字段不是字典格式: {type(response_data["data"])}'
                    elif 'items' not in response_data['data']:
                        success = False
                        msg = f'data中没有items字段，可用字段: {list(response_data["data"].keys())}'
                    elif not isinstance(response_data['data']['items'], list):
                        success = False
                        msg = f'items不是列表格式: {type(response_data["data"]["items"])}'
                    elif len(response_data['data']['items']) == 0:
                        success = False
                        msg = 'items列表为空'
                    else:
                        note_info = response_data['data']['items'][0]
                        note_info['url'] = note_url
                        note_info = handle_note_info(note_info)
                        logger.info('笔记信息处理成功')
                        break  # 成功处理，跳出重试循环
                else:
                    logger.warning(f'API调用失败或返回数据为空: success={success}')
                    if attempt < self.max_retries:
                        continue
                    
                break  # 如果不需要重试，跳出循环
                    
            except Exception as e:
                success = False
                msg = f'处理笔记时发生异常: {str(e)}'
                logger.error(f'爬取笔记异常 (尝试{attempt + 1}): {e}', exc_info=True)
                if attempt < self.max_retries:
                    continue
                break
            
        logger.info(f'爬取笔记信息完成 {note_url}: success={success}, msg={msg}')
        
        if success and note_info:
            return note_info
        else:
            raise Exception(f"获取笔记失败: {msg}")

    async def fetch_multiple_notes(
        self, 
        note_urls: List[str], 
        proxies: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        批量获取多个笔记的信息
        
        Args:
            note_urls: 笔记URL列表
            proxies: 代理设置
            
        Returns:
            笔记信息列表
        """
        note_list = []
        total_notes = len(note_urls)
        
        print(f"\n开始批量爬取 {total_notes} 个笔记...")
        print("=" * 60)
        
        for index, note_url in enumerate(note_urls, 1):
            print(f"\n[{index}/{total_notes}] 正在爬取笔记: {note_url[-20:]}...")
            
            try:
                note_info = await self.fetch_note(note_url, proxies)
                note_list.append(note_info)
                print(f"✓ 笔记爬取完成: {note_info.get('title', '未知标题')[:30]}...")
                
            except Exception as e:
                print(f"✗ 笔记爬取失败: {e}")
            
            # 笔记之间的延迟
            if index < total_notes:
                print(f"等待 {self.delay} 秒后继续下一个笔记...")
                await asyncio.sleep(self.delay)
        
        # 统计信息
        print("\n" + "=" * 60)
        print("批量爬取完成!")
        print(f"成功: {len(note_list)} 个笔记")
        print(f"失败: {total_notes - len(note_list)} 个笔记")
        print("=" * 60 + "\n")
        
        return note_list

    async def fetch_all_user_notes(
        self, 
        user_url: str, 
        max_notes: Optional[int] = None,
        proxies: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        获取一个用户的所有笔记
        
        Args:
            user_url: 用户主页URL
            max_notes: 最多获取的笔记数，None表示不限制
            proxies: 代理设置
            
        Returns:
            笔记列表
        """
        note_list = []
        
        print(f"开始爬取用户的所有笔记: {user_url}")
        
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, self.cookies, proxies or {})
            
            if not success:
                # 如果是JavaScript相关的错误或者解析错误，返回空结果
                if ("list index out of range" in msg or 
                    "Cannot find module" in msg or 
                    "js" in msg.lower()):
                    logger.warning(f'用户笔记获取功能受限: {msg}')
                    print(f"⚠️ 用户笔记获取功能暂时受限，返回空结果")
                    return []
                else:
                    raise Exception(f"获取用户笔记列表失败: {msg}")
            
            logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
            
            # 构建笔记URL列表
            note_urls = []
            for simple_note_info in all_note_info:
                note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                note_urls.append(note_url)
            
            # 如果设置了最大笔记数，截取
            if max_notes and len(note_urls) > max_notes:
                note_urls = note_urls[:max_notes]
                print(f"限制获取数量为 {max_notes} 个笔记")
            
            # 批量获取笔记详情
            note_data = await self.fetch_multiple_notes(note_urls, proxies)
            
            print(f"用户笔记爬取完成，共获取 {len(note_data)} 个笔记")
            return note_data
            
        except Exception as e:
            logger.error(f'爬取用户所有笔记失败 {user_url}: {e}')
            raise
    
    async def fetch_multiple_users_notes(
        self,
        user_urls: List[str],
        max_notes_per_user: Optional[int] = None,
        proxies: Optional[Dict] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        获取多个用户的所有笔记
        
        Args:
            user_urls: 用户URL列表
            max_notes_per_user: 每个用户最多获取的笔记数，None表示不限制
            proxies: 代理设置
            
        Returns:
            字典，key为用户URL，value为笔记列表
        """
        results = {}
        total_users = len(user_urls)
        
        print(f"\n开始批量爬取 {total_users} 个用户的笔记...")
        print("=" * 60)
        
        for index, user_url in enumerate(user_urls, 1):
            print(f"\n[{index}/{total_users}] 正在爬取用户: {user_url[-30:]}...")
            
            try:
                notes = await self.fetch_all_user_notes(
                    user_url=user_url,
                    max_notes=max_notes_per_user,
                    proxies=proxies
                )
                results[user_url] = notes
                print(f"✓ 用户 {user_url[-30:]} 爬取完成: {len(notes)} 个笔记")
                
            except Exception as e:
                print(f"✗ 用户 {user_url[-30:]} 爬取失败: {e}")
                results[user_url] = []
            
            # 用户之间的延迟
            if index < total_users:
                print(f"等待 {self.delay} 秒后继续下一个用户...")
                await asyncio.sleep(self.delay)
        
        # 统计信息
        print("\n" + "=" * 60)
        print("批量爬取完成!")
        print(f"成功: {sum(1 for notes in results.values() if notes)} 个用户")
        print(f"失败: {sum(1 for notes in results.values() if not notes)} 个用户")
        print(f"总笔记数: {sum(len(notes) for notes in results.values())} 个")
        print("=" * 60 + "\n")
        
        return results

    async def search_notes(
        self, 
        query: str, 
        require_num: int,
        sort_type_choice: int = 0,
        note_type: int = 0,
        note_time: int = 0,
        note_range: int = 0,
        pos_distance: int = 0,
        geo: Optional[Dict] = None,
        proxies: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索指定数量的笔记
        
        Args:
            query: 搜索关键词
            require_num: 搜索数量
            sort_type_choice: 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
            note_type: 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
            note_time: 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
            note_range: 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
            pos_distance: 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
            geo: 地理位置信息
            proxies: 代理设置
            
        Returns:
            搜索到的笔记列表
        """
        print(f"开始搜索关键词: {query}，目标数量: {require_num}")
        
        try:
            success, msg, notes = self.xhs_apis.search_some_note(
                query, require_num, self.cookies, sort_type_choice, 
                note_type, note_time, note_range, pos_distance, 
                str(geo) if geo else "", proxies or {}
            )
            
            if not success:
                # 如果是JavaScript相关的错误，返回空结果而不是抛出异常
                if "Cannot find module" in msg or "js" in msg.lower():
                    logger.warning(f'搜索功能因JavaScript问题被禁用: {msg}')
                    print(f"⚠️ 搜索功能暂时不可用（JavaScript依赖问题），返回空结果")
                    return []
                else:
                    raise Exception(f"搜索失败: {msg}")
            
            # 过滤出笔记类型
            notes = list(filter(lambda x: x['model_type'] == "note", notes))
            logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
            
            # 构建笔记URL列表
            note_urls = []
            for note in notes:
                note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                note_urls.append(note_url)
            
            # 批量获取笔记详情
            note_data = await self.fetch_multiple_notes(note_urls, proxies)
            
            print(f"搜索完成，共获取 {len(note_data)} 个笔记")
            return note_data
            
        except Exception as e:
            logger.error(f'搜索关键词 {query} 失败: {e}')
            raise
    
    @staticmethod
    def extract_note_detail(note: Dict[str, Any]) -> Dict[str, Any]:
        """
        从原始笔记数据中提取详细信息
        
        Args:
            note: 原始笔记数据字典
            
        Returns:
            提取后的结构化笔记详情
        """
        # 基本信息
        note_id = note.get('note_id', '')
        title = note.get('title', '')
        desc = note.get('desc', '')
        time_str = note.get('time', '')
        note_url = note.get('url', '')
        
        # 统计数据
        interact_info = note.get('interact_info', {})
        statistics = {
            'liked_count': interact_info.get('liked_count', 0),      # 点赞数
            'collected_count': interact_info.get('collected_count', 0), # 收藏数
            'comment_count': interact_info.get('comment_count', 0),   # 评论数
            'share_count': interact_info.get('share_count', 0),       # 分享数
        }
        
        # 作者信息
        user_info = note.get('user', {})
        author_info = {
            'user_id': user_info.get('user_id', ''),
            'nickname': user_info.get('nickname', ''),
            'avatar': user_info.get('avatar', ''),
            'desc': user_info.get('desc', ''),
        }
        
        # 内容信息
        content_info = {
            'type': note.get('type', ''),  # 笔记类型：normal/video
            'cover': note.get('cover', {}).get('url_default', '') if note.get('cover') else '',
            'images': [],
            'video_url': '',
        }
        
        # 处理图片
        image_list = note.get('image_list', [])
        for img in image_list:
            if isinstance(img, dict) and 'url_default' in img:
                content_info['images'].append(img['url_default'])
        
        # 处理视频
        video_info = note.get('video', {})
        if video_info:
            media = video_info.get('media', {})
            if media and 'stream' in media:
                stream = media['stream']
                if isinstance(stream, dict) and 'h264' in stream:
                    h264_list = stream['h264']
                    if h264_list and len(h264_list) > 0:
                        content_info['video_url'] = h264_list[0].get('master_url', '')
        
        # 话题标签
        tag_list = note.get('tag_list', [])
        hashtags = []
        for tag in tag_list:
            if isinstance(tag, dict) and 'name' in tag:
                hashtags.append({
                    'id': tag.get('id', ''),
                    'name': tag.get('name', ''),
                    'type': tag.get('type', '')
                })
        
        return {
            'note_id': note_id,
            'title': title,
            'desc': desc,
            'time': time_str,
            'url': note_url,
            'statistics': statistics,
            'author': author_info,
            'content': content_info,
            'hashtags': hashtags,
            'link': f"https://www.xiaohongshu.com/explore/{note_id}",
            'raw_data': note  # 保留原始数据以备需要
        }
    
    @staticmethod
    def extract_note_details_batch(note_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量提取笔记详细信息
        
        Args:
            note_list: 笔记列表
            
        Returns:
            提取后的笔记详情列表
        """
        return [XiaohongshuProvider.extract_note_detail(note) for note in note_list]
    
    @staticmethod
    def print_note_detail(detail: Dict[str, Any], index: int = 1):
        """
        打印笔记详细信息
        
        Args:
            detail: 笔记详情字典
            index: 序号
        """
        print(f"\n{'='*70}")
        print(f"笔记 {index}: {detail['note_id']}")
        print(f"{'='*70}")
        
        print(f"\n📝 基本信息:")
        print(f"  标题: {detail['title']}")
        print(f"  描述: {detail['desc'][:100]}{'...' if len(detail['desc']) > 100 else ''}")
        print(f"  发布时间: {detail['time']}")
        print(f"  链接: {detail['link']}")
        
        print(f"\n📊 统计数据:")
        stats = detail['statistics']
        print(f"  👍 点赞: {stats['liked_count']:,}")
        print(f"  ⭐ 收藏: {stats['collected_count']:,}")
        print(f"  💬 评论: {stats['comment_count']:,}")
        print(f"  🔗 分享: {stats['share_count']:,}")
        
        print(f"\n🎬 内容信息:")
        content = detail['content']
        print(f"  类型: {content['type']}")
        if content['images']:
            print(f"  图片数: {len(content['images'])}")
        if content['video_url']:
            print(f"  视频: 有")
        print(f"  封面: {content['cover'][:60]}..." if content['cover'] else "  封面: 无")
        
        print(f"\n👤 作者信息:")
        author = detail['author']
        print(f"  昵称: {author['nickname']}")
        print(f"  用户ID: {author['user_id']}")
        print(f"  签名: {author['desc'][:50]}{'...' if len(author['desc']) > 50 else ''}")
        
        if detail['hashtags']:
            print(f"\n🏷️  话题标签:")
            for tag in detail['hashtags'][:5]:  # 最多显示5个
                print(f"  #{tag['name']}")
    
    async def fetch_and_extract_user_notes(
        self,
        user_url: str,
        max_notes: Optional[int] = None,
        extract: bool = True,
        proxies: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        获取用户笔记并提取详细信息
        
        Args:
            user_url: 用户主页URL
            max_notes: 最多获取的笔记数
            extract: 是否提取详细信息（False则返回原始数据）
            proxies: 代理设置
            
        Returns:
            笔记列表（提取后的详情或原始数据）
        """
        # 获取原始笔记数据
        raw_notes = await self.fetch_all_user_notes(user_url, max_notes, proxies)
        
        if not extract:
            return raw_notes
        
        # 提取详细信息
        print(f"\n正在提取 {len(raw_notes)} 个笔记的详细信息...")
        details = self.extract_note_details_batch(raw_notes)
        print(f"✓ 提取完成")
        
        return details
    
    async def search_and_extract_notes(
        self,
        query: str,
        require_num: int,
        extract: bool = True,
        sort_type_choice: int = 0,
        note_type: int = 0,
        proxies: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索笔记并提取详细信息
        
        Args:
            query: 搜索关键词
            require_num: 搜索数量
            extract: 是否提取详细信息
            sort_type_choice: 排序方式
            note_type: 笔记类型
            proxies: 代理设置
            
        Returns:
            笔记列表（提取后的详情或原始数据）
        """
        # 搜索原始笔记数据
        raw_notes = await self.search_notes(
            query=query,
            require_num=require_num,
            sort_type_choice=sort_type_choice,
            note_type=note_type,
            proxies=proxies
        )
        
        if not extract:
            return raw_notes
        
        # 提取详细信息
        print(f"\n正在提取 {len(raw_notes)} 个笔记的详细信息...")
        details = self.extract_note_details_batch(raw_notes)
        print(f"✓ 提取完成")
        
        return details
    
    def save_note_to_file(self, note: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """
        保存单个笔记数据到文件
        
        Args:
            note: 笔记数据字典
            user_id: 用户ID（可选，如果提供则保存到用户目录下）
            
        Returns:
            保存的文件路径
        """
        note_id = note.get('note_id', '')
        title = note.get('title', '无标题')
        
        # 标准化文件名
        safe_title = norm_str(title)[:40]
        if not safe_title.strip():
            safe_title = '无标题'
        
        # 确定保存路径
        if user_id:
            # 尝试多种方式获取昵称（适配不同的数据结构）
            nickname = (note.get('nickname') or 
                       note.get('user', {}).get('nickname') or 
                       'unknown')
            safe_nickname = norm_str(nickname)[:20]
            if not safe_nickname.strip():
                safe_nickname = 'unknown'
            save_path = os.path.join(self.save_dir, f"{safe_nickname}_{user_id}")
        else:
            save_path = self.save_dir
        
        # 创建目录
        os.makedirs(save_path, exist_ok=True)
        
        # 生成文件名（包含时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"note_{note_id}_{timestamp}.json"
        filepath = os.path.join(save_path, filename)
        
        # 保存JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        
        logger.info(f"笔记已保存到: {filepath}")
        return filepath
    
    def save_notes_to_file(self, notes: List[Dict[str, Any]], user_id: Optional[str] = None) -> List[str]:
        """
        批量保存笔记数据到文件
        
        Args:
            notes: 笔记数据列表
            user_id: 用户ID（可选）
            
        Returns:
            保存的文件路径列表
        """
        filepaths = []
        for note in notes:
            try:
                filepath = self.save_note_to_file(note, user_id)
                filepaths.append(filepath)
            except Exception as e:
                logger.error(f"保存笔记失败: {e}")
        
        logger.info(f"批量保存完成，共保存 {len(filepaths)}/{len(notes)} 个笔记")
        return filepaths
    
    def save_user_notes_summary(self, user_id: str, notes: List[Dict[str, Any]]) -> str:
        """
        保存用户笔记汇总文件
        
        Args:
            user_id: 用户ID
            notes: 用户的所有笔记列表
            
        Returns:
            保存的文件路径
        """
        if not notes:
            return ""
        
        # 获取用户信息
        first_note = notes[0]
        # 尝试多种方式获取昵称
        nickname = (first_note.get('nickname') or 
                   first_note.get('user', {}).get('nickname') or 
                   'unknown')
        safe_nickname = norm_str(nickname)[:20]
        if not safe_nickname.strip():
            safe_nickname = 'unknown'
        
        # 创建用户目录
        user_dir = os.path.join(self.save_dir, f"{safe_nickname}_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # 生成汇总数据
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary = {
            'user_id': user_id,
            'nickname': nickname,
            'crawl_time': timestamp,
            'total_notes': len(notes),
            'notes': notes
        }
        
        # 保存汇总文件
        filename = f"user_{user_id}_summary_{timestamp}.json"
        filepath = os.path.join(user_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"用户笔记汇总已保存到: {filepath}")
        return filepath
    
    async def search_and_save(
        self,
        query: str,
        require_num: int = 20,
        sort_type: int = 0,
        note_type: int = 0,
        save_format: str = "markdown",
        custom_save_dir: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        搜索关键词并自动保存笔记到文件 - 统一接口
        
        按关键词分类保存，每个关键词一个文件夹
        
        Args:
            query: 搜索关键词
            require_num: 搜索数量，默认20
            sort_type: 排序方式 (0=综合, 1=最新, 2=点赞, 3=评论, 4=收藏)
            note_type: 笔记类型 (0=不限, 1=视频, 2=图文)
            save_format: 保存格式 "markdown" 或 "json" 或 "both"
            custom_save_dir: 自定义保存根目录，如果提供则覆盖默认的 save_dir
            
        Returns:
            包含搜索结果和保存信息的字典:
            {
                'success': bool,           # 是否成功
                'query': str,              # 搜索关键词
                'total_found': int,        # 找到的笔记数
                'saved': int,              # 成功保存的笔记数
                'failed': int,             # 失败的笔记数
                'save_directory': str,     # 保存的根目录
                'directories': List[str],  # 所有笔记目录
                'statistics': Dict         # 统计数据（点赞、收藏等）
            }
        
        Example:
            >>> provider = XiaohongshuProvider()
            >>> # 使用默认目录
            >>> result = await provider.search_and_save("Python编程", require_num=10)
            >>> 
            >>> # 自定义保存目录
            >>> result = await provider.search_and_save(
            ...     query="美食",
            ...     require_num=5,
            ...     custom_save_dir="D:/my_notes/xiaohongshu"
            ... )
            >>> print(f"成功保存 {result['saved']} 个笔记")
            >>> print(f"保存位置: {result['save_directory']}")
        """
        start_time = datetime.now()
        
        logger.info(f"开始搜索并保存: 关键词='{query}', 数量={require_num}")
        
        try:
            # 1. 搜索笔记（已包含批量获取详情）
            print(f"\n{'='*70}")
            print(f"🔍 搜索关键词: {query}")
            print(f"📊 搜索数量: {require_num}")
            print(f"{'='*70}\n")
            
            raw_notes = await self.search_notes(
                query=query,
                require_num=require_num,
                sort_type_choice=sort_type,
                note_type=note_type
            )
            
            if not raw_notes:
                logger.warning(f"未搜索到任何笔记: {query}")
                return {
                    'success': False,
                    'query': query,
                    'total_found': 0,
                    'saved': 0,
                    'failed': 0,
                    'save_directory': '',
                    'directories': [],
                    'statistics': {
                        'error': '未搜索到任何笔记',
                        'duration_seconds': (datetime.now() - start_time).total_seconds()
                    }
                }
            
            # 2. 提取详细信息
            print(f"\n📝 正在提取 {len(raw_notes)} 个笔记的详细信息...")
            details = self.extract_note_details_batch(raw_notes)
            print(f"✅ 详情提取完成\n")
            
            # 3. 按关键词创建保存目录
            import re
            # 使用自定义目录或默认目录
            base_save_dir = custom_save_dir if custom_save_dir else self.save_dir
            
            # 清理关键词作为文件夹名
            safe_query = re.sub(r'[\\/:*?"<>|]', '_', query).strip()[:30]
            if not safe_query:
                safe_query = 'search_results'
            keyword_dir = os.path.join(base_save_dir, safe_query)
            os.makedirs(keyword_dir, exist_ok=True)
            
            # 4. 保存笔记
            saved_directories = []
            successful_saves = 0
            
            print(f"💾 正在保存笔记到: {keyword_dir}")
            
            for i, (raw_note, detail) in enumerate(zip(raw_notes, details), 1):
                try:
                    # 获取笔记信息
                    title = detail.get('title', '无标题')
                    note_id = detail.get('note_id', '')
                    author = detail.get('author', {}).get('nickname', '未知作者')
                    note_url = detail.get('link', '')
                    
                    # 生成唯一ID和目录名
                    import hashlib
                    article_id = hashlib.md5(f"{note_url}_{title}".encode()).hexdigest()[:12]
                    # 清理标题作为文件夹名
                    safe_title = re.sub(r'[\\/:*?"<>|]', '_', title).strip()[:100]
                    if not safe_title:
                        safe_title = 'untitled'
                    article_dir_name = f"{article_id}_{safe_title}"
                    article_dir = os.path.join(keyword_dir, article_dir_name)
                    
                    # 创建目录结构
                    os.makedirs(article_dir, exist_ok=True)
                    images_dir = os.path.join(article_dir, "images")
                    os.makedirs(images_dir, exist_ok=True)
                    
                    # 构建内容（使用 raw_note 以获取正确的统计数据）
                    content_text = self._build_note_content_text(raw_note, detail)
                    markdown_content = self._build_note_content_markdown(raw_note, detail)
                    
                    # 保存文本内容
                    text_file = os.path.join(article_dir, f"{safe_title}.txt")
                    with open(text_file, 'w', encoding='utf-8') as f:
                        f.write(content_text)
                    
                    # 保存 Markdown 内容
                    if save_format in ["markdown", "both"]:
                        markdown_file = os.path.join(article_dir, f"{safe_title}.md")
                        with open(markdown_file, 'w', encoding='utf-8') as f:
                            f.write(markdown_content)
                    
                    # 保存原始 JSON 数据
                    if save_format in ["json", "both"]:
                        raw_data_path = os.path.join(article_dir, "raw_data.json")
                        with open(raw_data_path, 'w', encoding='utf-8') as f:
                            json.dump(raw_note, f, ensure_ascii=False, indent=2)
                    
                    # 下载图片
                    storage_info = {'article_dir': article_dir}
                    await self._download_note_images(raw_note, storage_info)
                    
                    # 创建增强的元数据（包含统计数据）
                    statistics = detail.get('statistics', {})
                    metadata = {
                        "article_id": article_id,
                        "title": title,
                        "author": author,
                        "url": note_url,
                        "platform": self.platform_name,
                        "keyword": query,
                        "note_id": note_id,
                        "note_type": raw_note.get('note_type', ''),
                        "created_at": datetime.now().isoformat(),
                        "upload_time": raw_note.get('upload_time', ''),
                        "ip_location": raw_note.get('ip_location', ''),
                        "statistics": {
                            "liked_count": int(raw_note.get('liked_count', 0)) if isinstance(raw_note.get('liked_count'), (int, str)) else 0,
                            "collected_count": int(raw_note.get('collected_count', 0)) if isinstance(raw_note.get('collected_count'), (int, str)) else 0,
                            "comment_count": int(raw_note.get('comment_count', 0)) if isinstance(raw_note.get('comment_count'), (int, str)) else 0,
                            "share_count": int(raw_note.get('share_count', 0)) if isinstance(raw_note.get('share_count'), (int, str)) else 0,
                            "images_count": len(raw_note.get('image_list', [])),
                            "content_length": len(content_text)
                        },
                        "tags": raw_note.get('tags', []),
                        "files": {
                            "text_file": f"{safe_title}.txt",
                            "markdown_file": f"{safe_title}.md" if save_format in ["markdown", "both"] else None,
                            "raw_data": "raw_data.json" if save_format in ["json", "both"] else None
                        }
                    }
                    
                    # 保存元数据
                    metadata_file = os.path.join(article_dir, "metadata.json")
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
                    
                    saved_directories.append(article_dir)
                    successful_saves += 1
                    
                    if (i % 5 == 0) or (i == len(raw_notes)):
                        print(f"   已保存: {i}/{len(raw_notes)} 个笔记")
                    
                except Exception as e:
                    logger.error(f"保存笔记失败 {detail.get('title', 'Unknown')}: {e}")
                    import traceback

                    traceback.print_exc()
                    continue
            
            print(f"✅ 保存完成: {successful_saves}/{len(raw_notes)} 个笔记\n")
            
            # 5. 统计数据
            total_likes = sum(int(raw_note.get('liked_count', 0)) if isinstance(raw_note.get('liked_count'), (int, str)) else 0 for raw_note in raw_notes)
            total_collects = sum(int(raw_note.get('collected_count', 0)) if isinstance(raw_note.get('collected_count'), (int, str)) else 0 for raw_note in raw_notes)
            total_comments = sum(int(raw_note.get('comment_count', 0)) if isinstance(raw_note.get('comment_count'), (int, str)) else 0 for raw_note in raw_notes)
            total_shares = sum(int(raw_note.get('share_count', 0)) if isinstance(raw_note.get('share_count'), (int, str)) else 0 for raw_note in raw_notes)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # 打印结果摘要
            print(f"\n{'='*70}")
            print(f"✅ 搜索并保存完成!")
            print(f"{'='*70}")
            print(f"🔍 搜索关键词: {query}")
            print(f"📊 找到笔记: {len(raw_notes)} 个")
            print(f"💾 成功保存: {successful_saves} 个")
            print(f"📁 保存位置: {keyword_dir}")
            print(f"⏱️  耗时: {duration:.1f} 秒")
            print(f"\n📈 互动数据统计:")
            print(f"   总点赞: {total_likes:,}")
            print(f"   总收藏: {total_collects:,}")
            print(f"   总评论: {total_comments:,}")
            print(f"   总分享: {total_shares:,}")
            print(f"{'='*70}\n")
            
            result = {
                'success': True,
                'query': query,
                'total_found': len(raw_notes),
                'saved': successful_saves,
                'failed': len(raw_notes) - successful_saves,
                'save_directory': keyword_dir,
                'directories': saved_directories,
                'statistics': {
                    'total_likes': total_likes,
                    'total_collects': total_collects,
                    'total_comments': total_comments,
                    'total_shares': total_shares,
                    'avg_likes': total_likes / len(raw_notes) if raw_notes else 0,
                    'avg_collects': total_collects / len(raw_notes) if raw_notes else 0,
                    'duration_seconds': duration
                }
            }
            
            logger.info(f"搜索保存完成: {query}, 成功: {successful_saves}/{len(raw_notes)}")
            return result
            
        except Exception as e:
            logger.error(f"搜索并保存失败: {e}", exc_info=True)
            return {
                'success': False,
                'query': query,
                'total_found': 0,
                'saved': 0,
                'failed': 0,
                'save_directory': '',
                'directories': [],
                'statistics': {
                    'error': str(e),
                    'duration_seconds': (datetime.now() - start_time).total_seconds()
                }
            }
    
    def _build_note_content_text(self, raw_note: Dict[str, Any], detail: Dict[str, Any]) -> str:
        """
        构建笔记的纯文本内容
        
        Args:
            raw_note: 原始笔记数据（包含正确的统计数据）
            detail: 笔记详情字典
            
        Returns:
            纯文本内容
        """
        parts = []
        
        # 标题
        title = raw_note.get('title', detail.get('title', ''))
        if title:
            parts.append(title)
            parts.append('')
        
        # 描述
        desc = raw_note.get('desc', detail.get('desc', ''))
        if desc:
            parts.append(desc)
            parts.append('')
        
        # 互动数据（使用 raw_note 的数据）
        liked_count = raw_note.get('liked_count', 0)
        collected_count = raw_note.get('collected_count', 0)
        comment_count = raw_note.get('comment_count', 0)
        share_count = raw_note.get('share_count', 0)
        
        # 转换为整数（有些可能是字符串）
        # 格式化数字显示（处理中文单位如"1.4万"）
        def format_count(count):
            """格式化数字,保持原样或转换为带千位分隔符的格式"""
            if isinstance(count, str):
                # 如果是字符串(如"1.4万"),直接返回
                return count
            try:
                # 如果是数字,添加千位分隔符
                return f"{int(count):,}"
            except:
                return str(count) if count else "0"
        
        parts.append(f"点赞: {format_count(liked_count)}")
        parts.append(f"收藏: {format_count(collected_count)}")
        parts.append(f"评论: {format_count(comment_count)}")
        parts.append(f"分享: {format_count(share_count)}")
        parts.append('')
        
        # 链接
        link = raw_note.get('note_url', detail.get('link', ''))
        if link:
            # 移除 xsec_token 参数
            if '?' in link:
                link = link.split('?')[0]
            parts.append(f"原文链接: {link}")
        
        return '\n'.join(parts)
    
    def _build_note_content_markdown(self, raw_note: Dict[str, Any], detail: Dict[str, Any]) -> str:
        """
        构建笔记的 Markdown 内容（和其他平台格式一致）
        
        Args:
            raw_note: 原始笔记数据（包含正确的统计数据）
            detail: 笔记详情字典
            
        Returns:
            Markdown 格式的文本
        """
        # 基本信息
        title = raw_note.get('title', detail.get('title', '无标题'))
        desc = raw_note.get('desc', detail.get('desc', ''))
        note_type = raw_note.get('note_type', '')
        author_name = raw_note.get('nickname', '')
        upload_time = raw_note.get('upload_time', '')
        ip_location = raw_note.get('ip_location', '')
        
        # 链接（去除 token）
        link = raw_note.get('note_url', detail.get('link', ''))
        if '?' in link:
            link = link.split('?')[0]
        
        # 互动数据（使用 raw_note 的数据）
        liked_count = raw_note.get('liked_count', 0)
        collected_count = raw_note.get('collected_count', 0)
        comment_count = raw_note.get('comment_count', 0)
        share_count = raw_note.get('share_count', 0)
        
        # 格式化数字显示（处理中文单位如"1.4万"）
        def format_count(count):
            """格式化数字,保持原样或转换为带千位分隔符的格式"""
            if isinstance(count, str):
                # 如果是字符串(如"1.4万"),直接返回
                return count
            try:
                # 如果是数字,添加千位分隔符
                return f"{int(count):,}"
            except:
                return str(count) if count else "0"
        
        # 标签
        tags = raw_note.get('tags', [])
        tags_str = ' '.join([f"#{tag}" for tag in tags]) if tags else '无标签'
        
        # 构建Markdown内容
        md_content = f"""# {title}

---

## 📝 基本信息

- **作者**: {author_name}
- **发布时间**: {upload_time}
- **笔记类型**: {note_type}
- **IP归属地**: {ip_location}
- **原文链接**: [{link}]({link})

## 📊 互动数据

- 👍 点赞: **{format_count(liked_count)}**
- ⭐ 收藏: **{format_count(collected_count)}**
- 💬 评论: **{format_count(comment_count)}**
- 🔗 分享: **{format_count(share_count)}**

## 📄 内容描述

{desc}

## 🏷️ 话题标签

{tags_str}

---

*本文件由小红书爬虫自动生成*  
*生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        return md_content

    async def _download_note_images(self, raw_note: Dict[str, Any], storage_info: Dict[str, Any]) -> None:
        """
        下载笔记的所有图片
        
        Args:
            raw_note: 原始笔记数据
            storage_info: 存储信息字典
        """
        try:
            # 获取图片列表
            image_list = raw_note.get('image_list', [])
            if not image_list:
                return
            
            # 创建 images 目录
            images_dir = os.path.join(storage_info['article_dir'], 'images')
            os.makedirs(images_dir, exist_ok=True)
            
            # 下载所有图片
            downloaded_count = 0
            total_images = len(image_list)
            
            timeout = httpx.Timeout(timeout=30)
            async with httpx.Client(timeout=timeout) as session:
                for idx, image_url in enumerate(image_list, 1):
                    try:
                        if not image_url:
                            continue
                        
                        # 下载图片
                        async with session.get(image_url) as response:
                            if response.status == 200:
                                content = await response.read()
                                
                                # 智能检测图片格式
                                content_type = response.headers.get('Content-Type')
                                ext = get_file_extension(content_type=content_type, url=image_url, content=content)
                                
                                # 生成文件名：使用序号命名
                                filename = f"image_{idx:03d}.{ext}"
                                filepath = os.path.join(images_dir, filename)
                                
                                with open(filepath, 'wb') as f:
                                    f.write(content)
                                downloaded_count += 1
                            else:
                                logger.warning(f"图片下载失败 (状态码 {response.status}): {image_url}")
                        
                        # 避免请求过快
                        await asyncio.sleep(0.2)
                        
                    except Exception as e:
                        logger.warning(f"下载图片 {idx}/{total_images} 失败: {e}")
                        continue
            
            if downloaded_count > 0:
                logger.info(f"   📷 成功下载 {downloaded_count}/{total_images} 张图片")
            
        except Exception as e:
            logger.error(f"下载笔记图片失败: {e}")

    async def close(self):
        """关闭连接（为了接口一致性）"""
        # 小红书爬虫暂无需特殊关闭操作，保留接口以保持一致性
        pass


# ============================================================================
# 兼容性封装（保持旧接口可用）
# ============================================================================


class Data_Spider:
    """
    兼容性类，保持旧接口可用（同步版本）
    
    ⚠️ 已废弃 (Deprecated)：建议使用异步版本 XiaohongshuProvider
    此类仅为向后兼容而保留，功能较少且缺少延迟控制
    将在未来版本中移除
    
    推荐迁移指南: 参考 docs/XHS_ASYNC_MIGRATION.md
    """

    def __init__(self, save_dir: str = "data/xiaohongshu"):
        """
        初始化数据爬虫
        
        Args:
            save_dir: 数据保存目录，默认"data/xiaohongshu"
        """
        self.xhs_apis = XHS_Apis()
        self.save_dir = save_dir
        
        # 确保保存目录存在
        os.makedirs(save_dir, exist_ok=True)

    def spider_note(self, note_url: str, cookies_str: str, proxies=None, max_retries=3, base_delay=5):
        """
        爬取一个笔记的信息，带重试和延时机制
        :param note_url: 笔记URL
        :param cookies_str: cookies字符串
        :param proxies: 代理设置
        :param max_retries: 最大重试次数
        :param base_delay: 基础延时时间（秒）
        :return: (success, msg, note_info)
        """
        note_info = None
        success = False
        msg = "未开始处理"
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    # 计算延时时间，每次重试增加延时
                    delay = base_delay * (2 ** (attempt - 1)) + random.uniform(1, 3)
                    logger.info(f'第{attempt}次重试，等待{delay:.1f}秒...')
                    time.sleep(delay)
                
                success, msg, response_data = self.xhs_apis.get_note_info(note_url, cookies_str, proxies or {})
                logger.info(f'API调用结果 (尝试{attempt + 1}): success={success}, msg={msg}')
                
                # 检查是否是限流错误
                if response_data and isinstance(response_data, dict):
                    if response_data.get('code') == 300013:  # 访问频次异常
                        logger.warning(f'检测到访问频次限制，第{attempt + 1}次尝试')
                        if attempt < max_retries:
                            continue
                        else:
                            success = False
                            msg = '重试次数用尽，仍然遇到访问频次限制'
                            break
                
                if success and response_data:
                    # 检查数据结构
                    if not isinstance(response_data, dict):
                        success = False
                        msg = f'API返回数据不是字典格式: {type(response_data)}'
                    elif 'data' not in response_data:
                        success = False
                        msg = f'API返回数据中没有data字段，可用字段: {list(response_data.keys())}'
                    elif not isinstance(response_data['data'], dict):
                        success = False
                        msg = f'data字段不是字典格式: {type(response_data["data"])}'
                    elif 'items' not in response_data['data']:
                        success = False
                        msg = f'data中没有items字段，可用字段: {list(response_data["data"].keys())}'
                    elif not isinstance(response_data['data']['items'], list):
                        success = False
                        msg = f'items不是列表格式: {type(response_data["data"]["items"])}'
                    elif len(response_data['data']['items']) == 0:
                        success = False
                        msg = 'items列表为空'
                    else:
                        note_info = response_data['data']['items'][0]
                        note_info['url'] = note_url
                        note_info = handle_note_info(note_info)
                        logger.info('笔记信息处理成功')
                        break  # 成功处理，跳出重试循环
                else:
                    logger.warning(f'API调用失败或返回数据为空: success={success}')
                    if attempt < max_retries:
                        continue
                    
                break  # 如果不需要重试，跳出循环
                    
            except Exception as e:
                success = False
                msg = f'处理笔记时发生异常: {str(e)}'
                logger.error(f'爬取笔记异常 (尝试{attempt + 1}): {e}', exc_info=True)
                if attempt < max_retries:
                    continue
                break
            
        logger.info(f'爬取笔记信息完成 {note_url}: success={success}, msg={msg}')
        return success, msg, note_info

    def spider_some_note(self, notes: list, cookies_str: str, proxies=None):
        """
        爬取一些笔记的信息
        :param notes: 笔记URL列表
        :param cookies_str: cookies字符串
        :param proxies: 代理设置
        :return: 笔记信息列表
        """
        note_list = []
        for note_url in notes:
            success, msg, note_info = self.spider_note(note_url, cookies_str, proxies)
            if note_info is not None and success:
                note_list.append(note_info)
        return note_list

    def spider_user_all_note(self, user_url: str, cookies_str: str, proxies=None):
        """
        爬取一个用户的所有笔记
        :param user_url: 用户主页URL
        :param cookies_str: cookies字符串
        :param proxies: 代理设置
        :return: (note_data, success, msg)
        """
        note_list = []
        try:
            success, msg, all_note_info = self.xhs_apis.get_user_all_notes(user_url, cookies_str, proxies or {})
            if success:
                logger.info(f'用户 {user_url} 作品数量: {len(all_note_info)}')
                for simple_note_info in all_note_info:
                    note_url = f"https://www.xiaohongshu.com/explore/{simple_note_info['note_id']}?xsec_token={simple_note_info['xsec_token']}"
                    note_list.append(note_url)
                note_data = self.spider_some_note(note_list, cookies_str, proxies)
                return note_data, success, msg
        except Exception as e:
            success = False
            msg = str(e)
        logger.info(f'爬取用户所有视频 {user_url}: {success}, msg: {msg}')
        return [], success, msg

    def spider_some_search_note(self, query: str, require_num: int, cookies_str: str, sort_type_choice=0, note_type=0, note_time=0, note_range=0, pos_distance=0, geo: Optional[dict] = None, proxies: Optional[dict] = None):
        """
        指定数量搜索笔记，设置排序方式和笔记类型和笔记数量
        :param query: 搜索的关键词
        :param require_num: 搜索的数量
        :param cookies_str: cookies字符串
        :param sort_type_choice: 排序方式 0 综合排序, 1 最新, 2 最多点赞, 3 最多评论, 4 最多收藏
        :param note_type: 笔记类型 0 不限, 1 视频笔记, 2 普通笔记
        :param note_time: 笔记时间 0 不限, 1 一天内, 2 一周内天, 3 半年内
        :param note_range: 笔记范围 0 不限, 1 已看过, 2 未看过, 3 已关注
        :param pos_distance: 位置距离 0 不限, 1 同城, 2 附近 指定这个必须要指定 geo
        :param geo: 地理位置信息字典，例如 {"latitude": 39.9725, "longitude": 116.4207}
        :param proxies: 代理设置
        :return: (note_data, success, msg)
        """
        note_list = []
        try:
            success, msg, notes = self.xhs_apis.search_some_note(
                query, require_num, cookies_str, sort_type_choice, 
                note_type, note_time, note_range, pos_distance, 
                str(geo) if geo else "", proxies or {}
            )
            if success:
                notes = list(filter(lambda x: x['model_type'] == "note", notes))
                logger.info(f'搜索关键词 {query} 笔记数量: {len(notes)}')
                for note in notes:
                    note_url = f"https://www.xiaohongshu.com/explore/{note['id']}?xsec_token={note['xsec_token']}"
                    note_list.append(note_url)
                note_data = self.spider_some_note(note_list, cookies_str, proxies)
                return note_data, success, msg
        except Exception as e:
            success = False
            msg = str(e)
        logger.info(f'搜索关键词 {query} 笔记: {success}, msg: {msg}')
        return [], success, msg
    
    def save_note_to_file(self, note: Dict[str, Any], user_id: Optional[str] = None) -> str:
        """
        保存单个笔记数据到文件
        
        Args:
            note: 笔记数据字典
            user_id: 用户ID（可选）
            
        Returns:
            保存的文件路径
        """
        note_id = note.get('note_id', '')
        title = note.get('title', '无标题')
        
        # 标准化文件名
        safe_title = norm_str(title)[:40]
        if not safe_title.strip():
            safe_title = '无标题'
        
        # 确定保存路径
        if user_id:
            # 尝试多种方式获取昵称（适配不同的数据结构）
            nickname = (note.get('nickname') or 
                       note.get('user', {}).get('nickname') or 
                       'unknown')
            safe_nickname = norm_str(nickname)[:20]
            if not safe_nickname.strip():
                safe_nickname = 'unknown'
            save_path = os.path.join(self.save_dir, f"{safe_nickname}_{user_id}")
        else:
            save_path = self.save_dir
        
        # 创建目录
        os.makedirs(save_path, exist_ok=True)
        
        # 生成文件名（包含时间戳）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"note_{note_id}_{timestamp}.json"
        filepath = os.path.join(save_path, filename)
        
        # 保存JSON文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(note, f, ensure_ascii=False, indent=2)
        
        logger.info(f"笔记已保存到: {filepath}")
        return filepath
    
    def save_notes_to_file(self, notes: List[Dict[str, Any]], user_id: Optional[str] = None, save_summary: bool = True) -> List[str]:
        """
        批量保存笔记数据到文件
        
        Args:
            notes: 笔记数据列表
            user_id: 用户ID（可选）
            save_summary: 是否保存汇总文件，默认True
            
        Returns:
            保存的文件路径列表
        """
        if not notes:
            logger.warning("没有笔记需要保存")
            return []
        
        filepaths = []
        
        # 保存单个笔记文件
        for note in notes:
            try:
                filepath = self.save_note_to_file(note, user_id)
                filepaths.append(filepath)
            except Exception as e:
                logger.error(f"保存笔记失败: {e}")
        
        # 保存汇总文件
        if save_summary and user_id:
            try:
                self.save_user_notes_summary(user_id, notes)
            except Exception as e:
                logger.error(f"保存汇总文件失败: {e}")
        
        logger.info(f"批量保存完成，共保存 {len(filepaths)}/{len(notes)} 个笔记")
        return filepaths
    
    def save_user_notes_summary(self, user_id: str, notes: List[Dict[str, Any]]) -> str:
        """
        保存用户笔记汇总文件
        
        Args:
            user_id: 用户ID
            notes: 用户的所有笔记列表
            
        Returns:
            保存的文件路径
        """
        if not notes:
            return ""
        
        # 获取用户信息
        first_note = notes[0]
        # 尝试多种方式获取昵称
        nickname = (first_note.get('nickname') or 
                   first_note.get('user', {}).get('nickname') or 
                   'unknown')
        safe_nickname = norm_str(nickname)[:20]
        if not safe_nickname.strip():
            safe_nickname = 'unknown'
        
        # 创建用户目录
        user_dir = os.path.join(self.save_dir, f"{safe_nickname}_{user_id}")
        os.makedirs(user_dir, exist_ok=True)
        
        # 生成汇总数据
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        summary = {
            'user_id': user_id,
            'nickname': nickname,
            'crawl_time': timestamp,
            'total_notes': len(notes),
            'notes': notes
        }
        
        # 保存汇总文件
        filename = f"user_{user_id}_summary_{timestamp}.json"
        filepath = os.path.join(user_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"用户笔记汇总已保存到: {filepath}")
        return filepath
