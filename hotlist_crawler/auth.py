"""
hotlist_crawler 登录模块 - 符合API设计规范
提供简洁的登录接口，返回bool值表示登录是否成功
"""
import os
import asyncio
import json
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright
import time

from .types import PlatformType, USER_DATA_DIR, PLATFORM_LOGIN_URLS


async def login(platform: PlatformType, headless: bool = False) -> bool:
    """
    用户登录函数 - 符合API设计规范
    
    Args:
        platform: 平台类型 (PlatformType枚举)
        headless: 是否无头模式运行（建议False，方便用户操作）
    
    Returns:
        bool: 登录是否成功保存
        - True: 登录成功并保存
        - False: 登录失败或保存失败
    
    Example:
        from hotlist_crawler.types import PlatformType
        
        # 登录知乎
        success = await login(PlatformType.ZHIHU)
        if success:
            print("知乎登录成功！")
        else:
            print("知乎登录失败！")
    """
    
    # 验证平台类型
    if not isinstance(platform, PlatformType):
        print(f"❌ 无效的平台类型: {platform}")
        return False
    
    login_url = PLATFORM_LOGIN_URLS.get(platform)
    if not login_url:
        print(f"❌ 不支持的平台: {platform}")
        return False
    
    # 确保用户数据目录存在
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    
    print(f"🚀 开始登录 {platform.upper()} 平台...")
    print(f"📍 登录页面: {login_url}")
    print(f"📁 用户数据目录: {USER_DATA_DIR}")
    
    try:
        async with async_playwright() as p:
            # 启动浏览器，使用持久化用户数据
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--disable-gpu'
                ],
                viewport={'width': 1280, 'height': 800}
            )
            
            try:
                page = await browser.new_page()
                page.set_default_timeout(300000)  # 5分钟超时
                
                # 打开登录页面
                print("🌐 正在打开登录页面...")
                await page.goto(login_url, wait_until='networkidle')
                
                print("\n" + "="*50)
                print("👤 请在浏览器中完成登录操作")
                print("💡 登录成功后，浏览器会自动保存登录状态")
                print("⏳ 登录完成后请关闭浏览器窗口，或按 Ctrl+C 结束")
                print("="*50)
                
                # 等待登录完成
                login_success = await _wait_for_login_completion(page, platform)
                
                if login_success:
                    # 获取cookies和保存登录数据
                    cookies = await page.context.cookies()
                    
                    # 保存登录数据
                    save_success = await _save_login_data(platform, cookies, page)
                    
                    if save_success:
                        print("✅ 登录成功并保存！")
                        print(f"🍪 保存了 {len(cookies)} 个cookies")
                        return True
                    else:
                        print("❌ 登录成功但保存失败")
                        return False
                else:
                    print("❌ 登录未完成或失败")
                    return False
                    
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ 登录过程中出现错误: {e}")
        return False


async def _wait_for_login_completion(page, platform: PlatformType, timeout: int = 300) -> bool:
    """等待登录完成"""
    start_time = time.time()
    
    # 根据平台定义登录成功的判断条件
    success_indicators = {
        PlatformType.ZHIHU: {
            "urls": ["https://www.zhihu.com/", "https://www.zhihu.com/explore"],
            "selectors": [".Avatar", ".AppHeader-profile"]
        },
        PlatformType.WEIBO: {
            "urls": ["https://weibo.com/", "https://m.weibo.cn/"],
            "selectors": [".gn_name", ".username"]
        },
        PlatformType.XIAOHONGSHU: {
            "urls": ["https://www.xiaohongshu.com/explore"],
            "selectors": [".avatar", ".user-avatar"]
        },
        PlatformType.WEIXIN: {
            "urls": ["https://mp.weixin.qq.com/cgi-bin/home"],
            "selectors": [".weui-desktop-account__nickname"]
        },
        PlatformType.DOUYIN: {
            "urls": ["https://www.douyin.com/"],
            "selectors": [".semi-avatar"]
        },
        PlatformType.BILIBILI: {
            "urls": ["https://www.bilibili.com/"],
            "selectors": [".header-avatar-wrap", ".user-con"]
        }
    }
    
    indicators = success_indicators.get(platform, {"urls": [], "selectors": []})
    
    while time.time() - start_time < timeout:
        try:
            current_url = page.url
            
            # 检查URL变化
            for url_indicator in indicators["urls"]:
                if url_indicator in current_url:
                    print(f"🎉 检测到登录成功（URL变化）: {current_url}")
                    return True
            
            # 检查页面元素
            for selector in indicators["selectors"]:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        print(f"🎉 检测到登录成功（找到用户元素）")
                        return True
                except:
                    pass
            
            # 通用检查：查找常见的用户信息元素
            common_selectors = [
                ".avatar", ".user-avatar", ".header-avatar",
                ".username", ".user-name", ".nickname",
                "[data-testid='avatar']", "[class*='avatar']"
            ]
            
            for selector in common_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element and await element.is_visible():
                        print(f"🎉 检测到登录成功（找到通用用户元素）")
                        return True
                except:
                    pass
            
            await asyncio.sleep(2)  # 每2秒检查一次
            
        except Exception as e:
            print(f"⚠️ 检查登录状态时出错: {e}")
            await asyncio.sleep(2)
    
    return False


async def _save_login_data(platform: PlatformType, cookies: list, page) -> bool:
    """保存登录数据，返回是否保存成功"""
    try:
        login_data_dir = os.path.join(USER_DATA_DIR, "login_data")
        os.makedirs(login_data_dir, exist_ok=True)
        
        # 准备用户信息
        user_info = {
            "platform": str(platform),
            "login_time": time.time(),
            "current_url": page.url,
            "page_title": await page.title(),
            "cookies_count": len(cookies),
            "status": "success"
        }
        
        # 保存登录信息
        login_file = os.path.join(login_data_dir, f"{platform}_login.json")
        with open(login_file, 'w', encoding='utf-8') as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)
        
        # 保存cookies
        cookies_file = os.path.join(login_data_dir, f"{platform}_cookies.json")
        with open(cookies_file, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        
        print(f"💾 登录数据已保存到: {login_data_dir}")
        return True
        
    except Exception as e:
        print(f"❌ 保存登录数据失败: {e}")
        return False


def is_online(platform: PlatformType) -> bool:
    """
    检查指定平台是否在线（是否有有效登录状态）
    
    Args:
        platform: 平台类型
    
    Returns:
        bool: 是否在线
        - True: 有有效登录状态
        - False: 没有登录或登录已过期
    
    Example:
        if is_online(PlatformType.ZHIHU):
            print("知乎已登录")
        else:
            print("知乎未登录")
    """
    
    if not isinstance(platform, PlatformType):
        return False
    
    try:
        login_file = os.path.join(USER_DATA_DIR, "login_data", f"{platform}_login.json")
        
        if not os.path.exists(login_file):
            return False
        
        with open(login_file, 'r', encoding='utf-8') as f:
            login_data = json.load(f)
        
        # 检查登录时间，超过7天认为过期
        login_time = login_data.get("login_time", 0)
        current_time = time.time()
        days_passed = (current_time - login_time) / (24 * 3600)
        
        if days_passed > 7:
            return False
        
        # 检查是否有cookies文件
        cookies_file = os.path.join(USER_DATA_DIR, "login_data", f"{platform}_cookies.json")
        if not os.path.exists(cookies_file):
            return False
        
        # 检查cookies是否有效（至少要有一些cookies）
        with open(cookies_file, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        return len(cookies) > 0
        
    except Exception as e:
        print(f"⚠️ 检查在线状态时出错: {e}")
        return False


def logout(platform: PlatformType) -> bool:
    """
    登出指定平台（删除本地登录数据）
    
    Args:
        platform: 平台类型
    
    Returns:
        bool: 是否成功登出
        - True: 成功删除登录数据
        - False: 删除失败或本来就没有登录
    
    Example:
        if logout(PlatformType.ZHIHU):
            print("知乎登出成功")
        else:
            print("知乎登出失败")
    """
    
    if not isinstance(platform, PlatformType):
        return False
    
    try:
        login_data_dir = os.path.join(USER_DATA_DIR, "login_data")
        
        # 删除登录信息文件
        login_file = os.path.join(login_data_dir, f"{platform}_login.json")
        cookies_file = os.path.join(login_data_dir, f"{platform}_cookies.json")
        
        files_deleted = 0
        
        if os.path.exists(login_file):
            os.remove(login_file)
            files_deleted += 1
            print(f"🗑️ 已删除登录信息文件")
        
        if os.path.exists(cookies_file):
            os.remove(cookies_file)
            files_deleted += 1
            print(f"🗑️ 已删除cookies文件")
        
        if files_deleted > 0:
            print(f"✅ {platform} 登出成功")
            return True
        else:
            print(f"⚠️ {platform} 本来就没有登录")
            return False
            
    except Exception as e:
        print(f"❌ 登出失败: {e}")
        return False


# 同步版本的login函数（如果需要的话）
def login_sync(platform: PlatformType, headless: bool = False) -> bool:
    """
    同步版本的登录函数
    
    Args:
        platform: 平台类型
        headless: 是否无头模式
    
    Returns:
        bool: 登录是否成功
    """
    return asyncio.run(login(platform, headless))


# 便捷函数：获取所有平台的在线状态
def get_all_online_status() -> Dict[str, bool]:
    """
    获取所有支持平台的在线状态
    
    Returns:
        Dict[str, bool]: 平台名称到在线状态的映射
    """
    status = {}
    for platform in PlatformType:
        status[str(platform)] = is_online(platform)
    return status