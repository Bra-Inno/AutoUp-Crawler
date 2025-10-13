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


def login(platform: PlatformType, headless: bool = False) -> bool:
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
        success = login(PlatformType.ZHIHU)
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
    
    # 同步调用异步函数
    try:
        import sys
        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except:
                pass
        
        # 运行异步登录逻辑
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(_login_async(platform, login_url, headless))
        
    except Exception as e:
        print(f"❌ 登录过程中出现错误: {e}")
        return False


async def _login_async(platform: PlatformType, login_url: str, headless: bool) -> bool:
    """异步登录实现"""
    try:
        async with async_playwright() as p:
            # 启动浏览器，使用持久化用户数据 - 最强反检测配置
            browser = await p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--no-first-run',
                    '--disable-blink-features=AutomationControlled',  # 核心：隐藏自动化控制
                    '--exclude-switches=enable-automation',          # 核心：排除自动化标识
                    '--disable-infobars',                           # 核心：禁用信息条
                    '--disable-extensions',                          
                    '--disable-default-apps',
                    '--test-type',                                  # 测试模式，减少提示
                    '--disable-web-security',
                    '--disable-features=TranslateUI,VizDisplayCompositor',
                    '--use-fake-ui-for-media-stream',              # 伪装媒体流UI
                    '--disable-component-update',                   # 禁用组件更新
                    '--disable-domain-reliability',                # 禁用域可靠性
                    '--disable-sync',                              # 禁用同步
                    '--disable-background-networking',             # 禁用后台网络
                    '--disable-breakpad',                          # 禁用崩溃报告
                    '--disable-component-extensions-with-background-pages',
                    '--disable-client-side-phishing-detection',   # 禁用钓鱼检测
                    '--disable-default-apps',
                    '--disable-hang-monitor',                      # 禁用挂起监控
                    '--disable-prompt-on-repost',                 # 禁用重新提交提示
                    '--disable-background-timer-throttling',      # 禁用后台定时器限制
                    '--disable-renderer-backgrounding',           # 禁用渲染器后台化
                    '--disable-backgrounding-occluded-windows',   # 禁用遮挡窗口后台化
                    '--disable-ipc-flooding-protection',          # 禁用IPC洪水保护
                    '--password-store=basic',                      # 基本密码存储
                    '--use-mock-keychain'                          # 使用模拟钥匙串
                ],
                viewport={'width': 1280, 'height': 800},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                ignore_default_args=['--enable-automation', '--enable-blink-features=AutomationControlled'],  # 忽略所有自动化参数
                bypass_csp=True,
                # 额外设置
                locale='zh-CN',
                timezone_id='Asia/Shanghai'
            )
            
            try:
                page = await browser.new_page()
                page.set_default_timeout(300000)  # 5分钟超时
                
                # 设置额外的浏览器属性来隐藏自动化
                await browser.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                # 注入脚本隐藏自动化特征
                await page.add_init_script("""
                    // 删除webdriver属性
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    // 删除自动化相关属性
                    delete navigator.__proto__.webdriver;
                    
                    // 修改chrome对象
                    window.navigator.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    
                    // 覆盖插件信息，模拟真实浏览器
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [{
                            name: "Chrome PDF Plugin",
                            filename: "internal-pdf-viewer",
                            description: "Portable Document Format"
                        }],
                    });
                    
                    // 覆盖语言信息
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                    });
                    
                    // 覆盖自动化检测相关属性
                    Object.defineProperty(navigator, 'platform', {
                        get: () => 'Win32',
                    });
                    
                    // 隐藏Selenium相关属性
                    window.document.$cdc_asdjflasutopfhvcZLmcfl_ = undefined;
                    window.document.$chrome_asyncScriptInfo = undefined;
                    
                    // 修改permission API
                    const originalQuery = window.navigator.permissions.query;
                    window.navigator.permissions.query = (parameters) => (
                        parameters.name === 'notifications' ?
                            Promise.resolve({ state: Notification.permission }) :
                            originalQuery(parameters)
                    );
                    
                    // 覆盖getTimezoneOffset
                    Date.prototype.getTimezoneOffset = function() {
                        return -480; // UTC+8 (中国时区)
                    };
                """)
                
                # 打开登录页面
                print("🌐 正在打开登录页面...")
                await page.goto(login_url, wait_until='networkidle')
                
                print("\n" + "="*50)
                print("👤 请在浏览器中完成登录操作")
                print("💡 登录状态将在45秒后自动保存")
                print("⏳ 请在45秒内完成登录操作")
                print("="*50)
                
                # 等待用户操作，45秒后自动保存或用户按回车手动保存
                await _wait_for_user_action(page, platform, timeout=45)
                
                # 获取并保存当前cookies状态
                cookies = await page.context.cookies()
                
                # 保存登录数据
                save_success = await _save_login_data(platform, cookies, page)
                
                if save_success:
                    if len(cookies) > 0:
                        print("✅ 登录状态已保存！")
                        print(f"🍪 保存了 {len(cookies)} 个cookies")
                        return True
                    else:
                        print("⚠️ 已保存状态，但未检测到cookies（可能未登录）")
                        return False
                else:
                    print("❌ 保存失败")
                    return False
                    
            finally:
                await browser.close()
                
    except Exception as e:
        print(f"❌ 异步登录过程中出现错误: {e}")
        return False


async def _wait_for_user_action(page, platform: PlatformType, timeout: int = 45):
    """等待用户操作：45秒倒计时或用户按回车键手动保存"""
    import threading
    import queue
    
    print(f"⏰ 开始倒计时 {timeout} 秒...")
    print("💡 提示：您可以随时按回车键保存当前登录状态")
    
    # 使用队列来接收用户输入
    input_queue = queue.Queue()
    
    def input_thread():
        """在独立线程中监听用户输入"""
        try:
            input()  # 等待用户按回车
            input_queue.put("user_input")
        except:
            pass
    
    # 启动输入监听线程
    thread = threading.Thread(target=input_thread, daemon=True)
    thread.start()
    
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        remaining = timeout - elapsed
        
        # 每5秒显示一次倒计时
        if elapsed % 5 == 0 and elapsed > 0:
            print(f"⏳ 剩余时间: {remaining} 秒 (按回车键立即保存)")
        
        # 检查是否有用户输入
        try:
            input_queue.get_nowait()
            print("👍 检测到用户输入，立即保存登录状态")
            return
        except queue.Empty:
            pass
        
        await asyncio.sleep(1)
    
    print(f"⏰ 已等待 {timeout} 秒，自动保存当前状态")


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


# 同步版本的login函数（如果需要的话）
def login_sync(platform: PlatformType, headless: bool = False) -> bool:
    """
    同步版本的登录函数（现在login本身就是同步的，这个函数保持兼容性）
    
    Args:
        platform: 平台类型
        headless: 是否无头模式
    
    Returns:
        bool: 登录是否成功
    """
    return login(platform, headless)


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