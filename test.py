import hotlist_crawler
from hotlist_crawler import PlatformType

a = 5


match a:
    case 1:
            
        success = hotlist_crawler.login(PlatformType.WEIBO, headless=False)
        if success:
            print("登录成功")
        else:
            print("登录失败")

    case 2:
        if hotlist_crawler.is_online(PlatformType.WEIBO):
            print("当前已登录")
        else:
            print("当前未登录")
    case 3:
        if hotlist_crawler.fetch("https://s.weibo.com/weibo?q=%E8%BF%99%E9%87%8C%E6%98%AF%E4%B8%AD%E5%9B%BD", "./data", save_images=True):
            print("抓取成功")
        else:
            print("抓取失败")
    case 4:
        urls = [
            "https://mp.weixin.qq.com/s/LIHOwmis6H0JIK8OeZsK_w",
            "https://s.weibo.com/weibo?q=%E8%BF%99%E9%87%8C%E6%98%AF%E4%B8%AD%E5%9B%BD",
            "https://s.weibo.com/weibo?q=Python",
            "https://www.zhihu.com/question/10112708097"
        ]

        results = hotlist_crawler.batch_fetch(urls, "./batch_downloads")
    case 5:
        print(hotlist_crawler.get_all_online_status())
