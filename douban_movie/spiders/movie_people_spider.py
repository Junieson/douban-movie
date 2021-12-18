import json
import re

import pandas as pd
import scrapy
from faker import Factory
from .. import load
from douban_movie.items import DoubanMovieItem, DoubanMovieCommentItem, DoubanMovieUser
import time,random
# 获取cookies
from ..dns_cache import _setDNSCache

cookies_dict = dict()

# 随机请求头
f = Factory.create()

class MovieItemSpider(scrapy.Spider):
    name = 'people'
    allowed_domains = ['m.douban.com', 'douban.com','movie.douban.com']
    start_urls = ['https://www.douban.com/doulist/1641439/?start=0&sort=seq&playable=0&sub_type=']
    num = 0 # 爬取数目
    custom_settings = {  # 自定义该spider的pipeline输出
        'ITEM_PIPELINES': {
             'douban_movie.pipelines.MoviePeoplePipeline': 1,
        }
    }

    headers = {
        'User-Agent': f.user_agent(),
    }

    pages = 14 # 总的爬取页面数

    # Scrapy使用保存cookies请求发现模块，看是否是登录之后的状态
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

    def start_requests(self):
        self.get_cookie()
        people = pd.read_csv("top_people_url")
        people_url = people['people_url'].tolist()[:10000]
        for url in people_url:
            # print(url)
            yield scrapy.Request(url=url,  # % people_url,
                                 headers=self.headers,
                                 callback=self.parse_people_url,
                                 cookies=cookies_dict,
                                 dont_filter=True)

    def parse_people_url(self, response):
        #print(response.status)
        _setDNSCache()
        User = DoubanMovieUser()
        User['location'] = response.xpath('//div[@class="user-info"]/a/text()').extract_first()
        User['introduction'] = response.xpath('//span[@id="intro_display"]/text()').extract_first()
        User['friend'] = response.xpath('//div[@id="friend"]/h2/span/a/text()').extract_first()
        attention =response.xpath('//p[@class="rev-link"]/a/text()').extract_first()
        if attention :
            User['be_attention'] =attention[2:]
        yield  User
        self.num+=1
        if self.num%10 == 0:
            print("~~~~~~~~~~~~~~~~~~~我已经爬了%d条~~~~~~~~~~~~~~~~~"%self.num)
        if self.num% 100 == 0:
            self.get_cookie()
