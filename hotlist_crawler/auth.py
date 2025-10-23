"""
hotlist_crawler 登录模块 - 符合API设计规范
提供简洁的登录接口，返回bool值表示登录是否成功
"""

import os
import time
import json
import asyncio
from loguru import logger
from typing import Dict, Optional
from playwright.async_api import async_playwright


from .types import PlatformType, PLATFORM_LOGIN_URLS, PLATFORM_CHECK_URLS


def login(platform: PlatformType, headless: bool = False) -> bool:
    """
    用户登录函数 - 符合API设计规范
    """

    # 验证平台类型
    if not isinstance(platform, PlatformType):
        logger.error(f"❌ 无效的平台类型: {platform}")
        return False

    login_url = PLATFORM_LOGIN_URLS.get(platform)
    if not login_url:
        logger.error(f"❌ 不支持的平台: {platform}")
        return False

    # 确保用户数据目录存在
    os.makedirs("./chrome_user_data", exist_ok=True)

    logger.info(f"🚀 开始登录 {platform.upper()} 平台...")
    logger.info(f"📍 登录页面: {login_url}")
    logger.info(f"📁 用户数据目录: ./chrome_user_data")

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
        logger.error(f"❌ 登录过程中出现错误: {e}")
        return False


async def _login_async(platform: PlatformType, login_url: str, headless: bool) -> bool:
    """异步登录实现"""
    try:
        async with async_playwright() as p:
            # 启动浏览器，使用持久化用户数据 - 最强反检测配置
            browser = await p.chromium.launch_persistent_context(
                user_data_dir="./chrome_user_data",
                headless=headless,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--no-first-run",
                    "--disable-blink-features=AutomationControlled",  # 核心：隐藏自动化控制
                    "--exclude-switches=enable-automation",  # 核心：排除自动化标识
                    "--disable-infobars",  # 核心：禁用信息条
                    "--disable-extensions",
                    "--disable-default-apps",
                    "--test-type",  # 测试模式，减少提示
                    "--disable-web-security",
                    "--disable-features=TranslateUI,VizDisplayCompositor",
                    "--use-fake-ui-for-media-stream",  # 伪装媒体流UI
                    "--disable-component-update",  # 禁用组件更新
                    "--disable-domain-reliability",  # 禁用域可靠性
                    "--disable-sync",  # 禁用同步
                    "--disable-background-networking",  # 禁用后台网络
                    "--disable-breakpad",  # 禁用崩溃报告
                    "--disable-component-extensions-with-background-pages",
                    "--disable-client-side-phishing-detection",  # 禁用钓鱼检测
                    "--disable-default-apps",
                    "--disable-hang-monitor",  # 禁用挂起监控
                    "--disable-prompt-on-repost",  # 禁用重新提交提示
                    "--disable-background-timer-throttling",  # 禁用后台定时器限制
                    "--disable-renderer-backgrounding",  # 禁用渲染器后台化
                    "--disable-backgrounding-occluded-windows",  # 禁用遮挡窗口后台化
                    "--disable-ipc-flooding-protection",  # 禁用IPC洪水保护
                    "--password-store=basic",  # 基本密码存储
                    "--use-mock-keychain",  # 使用模拟钥匙串
                ],
                viewport={"width": 1280, "height": 800},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                ignore_default_args=[
                    "--enable-automation",
                    "--enable-blink-features=AutomationControlled",
                ],  # 忽略所有自动化参数
                bypass_csp=True,
                # 额外设置
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )

            try:
                page = await browser.new_page()
                page.set_default_timeout(300000)  # 5分钟超时

                # 设置额外的浏览器属性来隐藏自动化
                await browser.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """
                )

                # 注入脚本隐藏自动化特征
                await page.add_init_script(
                    """
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
                """
                )

                # 打开登录页面
                logger.debug("🌐 正在打开登录页面...")
                await page.goto(login_url, wait_until="networkidle")

                logger.info("\n" + "=" * 50)
                logger.info("👤 请在浏览器中完成登录操作")
                logger.info("💡 登录状态将在45秒后自动保存")
                logger.debug("⏳ 请在45秒内完成登录操作")
                logger.info("=" * 50)

                # 等待用户操作，45秒后自动保存或用户按回车手动保存
                await _wait_for_user_action(page, platform, timeout=45)

                # 获取并保存当前cookies状态
                cookies = await page.context.cookies()

                # 保存登录数据
                save_success = await _save_login_data(platform, cookies, page)

                if save_success:
                    if len(cookies) > 0:
                        logger.info("✅ 登录状态已保存！")
                        logger.info(f"🍪 保存了 {len(cookies)} 个cookies")
                        return True
                    else:
                        logger.warning("⚠️ 已保存状态，但未检测到cookies（可能未登录）")
                        return False
                else:
                    logger.error("❌ 保存失败")
                    return False

            finally:
                await browser.close()

    except Exception as e:
        logger.error(f"❌ 异步登录过程中出现错误: {e}")
        return False


async def _wait_for_user_action(page, platform: PlatformType, timeout: int = 45):
    """等待用户操作：45秒倒计时或用户按回车键手动保存"""
    import threading
    import queue

    logger.info(f"⏰ 开始倒计时 {timeout} 秒...")
    logger.info("💡 提示：您可以随时按回车键保存当前登录状态")

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
            logger.debug(f"⏳ 剩余时间: {remaining} 秒 (按回车键立即保存)")

        # 检查是否有用户输入
        try:
            input_queue.get_nowait()
            logger.info("👍 检测到用户输入，立即保存登录状态")
            return
        except queue.Empty:
            pass

        await asyncio.sleep(1)

    logger.info(f"⏰ 已等待 {timeout} 秒，自动保存当前状态")


async def _save_login_data(platform: PlatformType, cookies: list, page) -> bool:
    """保存登录数据，返回是否保存成功"""
    try:
        login_data_dir = os.path.join("./chrome_user_data", "login_data")
        os.makedirs(login_data_dir, exist_ok=True)

        # 准备用户信息
        user_info = {
            "platform": str(platform),
            "login_time": time.time(),
            "current_url": page.url,
            "page_title": await page.title(),
            "cookies_count": len(cookies),
            "status": "success",
        }

        # 保存登录信息
        login_file = os.path.join(login_data_dir, f"{platform}_login.json")
        with open(login_file, "w", encoding="utf-8") as f:
            json.dump(user_info, f, ensure_ascii=False, indent=2)

        # 保存cookies
        cookies_file = os.path.join(login_data_dir, f"{platform}_cookies.json")
        with open(cookies_file, "w", encoding="utf-8") as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 登录数据已保存到: {login_data_dir}")
        return True

    except Exception as e:
        logger.error(f"❌ 保存登录数据失败: {e}")
        return False


def is_online(platform: PlatformType) -> bool:
    """
    检查指定平台是否在线（是否有有效登录状态）
    通过访问平台特定页面并检测是否跳转来判断
    """

    if not isinstance(platform, PlatformType):
        return False

    # 检查是否支持该平台的在线检测
    check_url = PLATFORM_CHECK_URLS.get(platform)

    # 微信和抖音平台使用特殊检测方式，不需要 check_url
    if platform not in [PlatformType.WEIXIN, PlatformType.DOUYIN] and not check_url:
        return False

    # 检查是否有cookies文件
    cookies_file = os.path.join("./chrome_user_data", "login_data", f"{platform}_cookies.json")
    if not os.path.exists(cookies_file):
        return False

    try:
        # 使用异步方式检测登录状态
        import sys

        if sys.platform == "win32":
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            except:
                pass

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_check_online_async(platform, check_url, cookies_file))

    except Exception as e:
        logger.warning(f"⚠️ 检查在线状态时出错: {e}")
        return False


async def _check_online_async(platform: PlatformType, check_url: Optional[str], cookies_file: str) -> bool:
    """异步检测登录状态"""
    try:
        # 读取cookies
        with open(cookies_file, "r", encoding="utf-8") as f:
            cookies = json.load(f)

        if not cookies:
            return False

        async with async_playwright() as p:
            # 使用无头模式快速检测
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 添加cookies
            await context.add_cookies(cookies)

            try:
                page = await context.new_page()

                # 微信平台特殊处理：直接访问测试文章
                if platform == PlatformType.WEIXIN:
                    test_article_url = "https://mp.weixin.qq.com/s/T7PYt7UTYiKVT67ENmvtnw"

                    try:
                        # 访问文章页面
                        await page.goto(test_article_url, wait_until="load", timeout=30000)
                        await asyncio.sleep(2)

                        # 获取页面内容
                        content = await page.content()

                        # 检查是否包含文章内容标记
                        has_content = (
                            "rich_media_content" in content
                            or "js_content" in content
                            or '<div class="rich_media_area_primary' in content
                        )

                        # 检查是否被重定向到验证页面
                        is_blocked = "验证" in content or "verify" in page.url.lower() or "captcha" in page.url.lower()

                        await browser.close()
                        return has_content and not is_blocked

                    except Exception as weixin_error:
                        logger.error(f"⚠️ 微信文章访问检测失败: {weixin_error}")
                        await browser.close()
                        return False

                # 抖音平台特殊处理：访问个人页面，检查是否有登录框
                if platform == PlatformType.DOUYIN:
                    douyin_user_url = "https://www.douyin.com/user/self?from_tab_name=main&showTab=record"

                    try:
                        # 访问个人页面
                        await page.goto(douyin_user_url, wait_until="load", timeout=30000)
                        await asyncio.sleep(2)

                        # 检查是否存在登录框元素（支持多个可能的登录框ID）
                        login_panel_1 = await page.query_selector("#login-full-panel-icv6ob2bq1c0")
                        login_panel_2 = await page.query_selector("#douyin-login-new-id")

                        # 如果存在任一登录框，说明未登录
                        if login_panel_1 or login_panel_2:
                            await browser.close()
                            return False

                        # 不存在登录框，说明已登录
                        await browser.close()
                        return True

                    except Exception as douyin_error:
                        logger.error(f"⚠️ 抖音登录检测失败: {douyin_error}")
                        await browser.close()
                        return False

                # 其他平台：访问检测URL - 使用更宽松的等待策略
                # 'load' 等待页面 load 事件触发即可，不等待所有网络请求
                if not check_url:
                    await browser.close()
                    return False

                try:
                    response = await page.goto(check_url, wait_until="load", timeout=30000)
                except Exception as goto_error:
                    # 如果 goto 失败，尝试获取当前页面URL判断是否跳转
                    logger.error(f"⚠️ 页面加载超时或失败: {goto_error}")
                    # 即使超时也可能已经跳转，继续检查URL

                # 等待页面稳定
                await asyncio.sleep(2)

                # 获取最终URL
                final_url = page.url

                # 判断是否发生跳转
                # 如果最终URL与检测URL的域名不同，或者跳转到登录页面，则认为登录失效
                from urllib.parse import urlparse

                check_domain = urlparse(check_url).netloc
                final_domain = urlparse(final_url).netloc

                # 检查是否跳转到登录页面
                login_keywords = ["login", "signin", "passport", "auth"]
                is_login_page = any(keyword in final_url.lower() for keyword in login_keywords)

                # 平台特定检查
                is_valid = True

                if platform == PlatformType.ZHIHU:
                    # 知乎：检查是否还在设置页面
                    is_valid = "/settings/" in final_url and not is_login_page

                elif platform == PlatformType.WEIBO:
                    # 微博：检查是否还在设置页面
                    is_valid = "weibo.com" in final_domain and not is_login_page

                elif platform == PlatformType.XIAOHONGSHU:
                    # 小红书：检查是否能正常访问笔记
                    is_valid = "xiaohongshu.com" in final_domain and not is_login_page

                elif platform == PlatformType.BILIBILI:
                    # B站：检查是否还在个人中心
                    is_valid = "account.bilibili.com" in final_domain and not is_login_page

                await browser.close()
                return is_valid

            except Exception as e:
                logger.error(f"⚠️ 访问检测页面失败: {e}")
                await browser.close()
                return False

    except Exception as e:
        logger.error(f"⚠️ 异步检测失败: {e}")
        return False


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
