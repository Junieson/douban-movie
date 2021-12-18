import json

import scrapy
from faker import Factory

from douban_movie import load

# 获取cookies
cookies_dict = dict()

# 随机请求头
f = Factory.create()
class TestSpider(scrapy.Spider):
    name = 'test'
    allowed_domains = ['www.douban.com']
    start_urls = ['http://www.douban.com/']
    # request请求头
    headers = {
        'User-Agent': f.user_agent(),
    }

    def question(self, response):
        with open('db_find.html', 'w', encoding='utf-8') as f:
            f.write(response.text)  # 写入文件，保存成.html文件
        pass

    # 获取cookies
    def get_cookie(self):
        # if not os.path.isfile("./dbCookies.json"):
        load.load_web("https://accounts.douban.com/passport/login?source=main")
        # 毕竟每次执行都要登录还是挺麻烦的，我们要充分利用cookies的作用
        # 从文件中获取保存的cookies
        with open('dbCookies.json', 'r', encoding='utf-8') as f:
            listcookies = json.loads(f.read())  # 获取cookies
        # 把获取的cookies处理成dict类型
        for cookie in listcookies:
            # 在保存成dict时，我们其实只要cookies中的name和value，而domain等其他都可以不要
            cookies_dict[cookie['name']] = cookie['value']
        print(cookies_dict)

    # scrapy请求的开始时start_request
    def start_requests(self):
        self.get_cookie()
        db_findUrl = "https://www.douban.com/doulist/1641439/?start=0&sort=seq&playable=0&sub_type="
        # Scrapy发起其他页面请求时，带上cookies=cookies_dict即可，同时记得带上header值，
        yield scrapy.Request(url=db_findUrl,
                             cookies=cookies_dict,
                             callback=self.question,
                             dont_filter=True,
                             headers=self.headers
                             )

    def parse(self, response):
        pass
