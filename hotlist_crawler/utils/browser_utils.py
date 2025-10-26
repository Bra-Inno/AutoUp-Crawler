from typing import Optional
from playwright.async_api import async_playwright, BrowserContext


async def launch_browser(
    user_data_dir: str,
    headless: bool = False,
    user_agent: Optional[str] = None,
) -> BrowserContext:
    if user_agent is None:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    p = await async_playwright().start()
    browser = await p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        headless=headless,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--no-first-run",
            "--disable-blink-features=AutomationControlled",
            "--exclude-switches=enable-automation",
            "--disable-infobars",
            "--disable-extensions",
            "--disable-default-apps",
            "--test-type",
            "--disable-web-security",
            "--disable-features=TranslateUI,VizDisplayCompositor",
            "--use-fake-ui-for-media-stream",
            "--disable-component-update",
            "--disable-domain-reliability",
            "--disable-sync",
            "--disable-background-networking",
            "--disable-breakpad",
            "--disable-component-extensions-with-background-pages",
            "--disable-client-side-phishing-detection",
            "--disable-hang-monitor",
            "--disable-prompt-on-repost",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-ipc-flooding-protection",
            "--password-store=basic",
            "--use-mock-keychain",
        ],
        viewport={"width": 1280, "height": 800},
        user_agent=user_agent,
        ignore_default_args=["--enable-automation", "--enable-blink-features=AutomationControlled"],
        bypass_csp=True,
        locale="zh-CN",
        timezone_id="Asia/Shanghai",
    )

    await browser.add_init_script("""Object.defineProperty(navigator, 'webdriver', {get: () => undefined});""")

    return browser


async def add_stealth_scripts(browser: BrowserContext):
    await browser.add_init_script(
        """
        Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        delete navigator.__proto__.webdriver;
        window.navigator.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}, app: {}};
        Object.defineProperty(navigator, 'plugins', {get: () => [{name: "Chrome PDF Plugin", filename: "internal-pdf-viewer", description: "Portable Document Format"}]});
        Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});
        Object.defineProperty(navigator, 'platform', {get: () => 'Win32'});
        window.document.$cdc_asdjflasutopfhvcZLmcfl_ = undefined;
        window.document.$chrome_asyncScriptInfo = undefined;
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (parameters.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : originalQuery(parameters));
        Date.prototype.getTimezoneOffset = function() {return -480;};
    """
    )
