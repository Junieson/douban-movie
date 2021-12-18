import json
import re

import pandas as pd
import scrapy
from faker import Factory
from .. import load
from douban_movie.items import DoubanMovieItem, DoubanMovieCommentItem
import time,random
# 获取cookies
from ..dns_cache import _setDNSCache

cookies_dict = dict()

# 随机请求头
f = Factory.create()

class MovieItemSpider(scrapy.Spider):
    name = 'comment2'
    allowed_domains = ['m.douban.com', 'douban.com','movie.douban.com']
    start_urls = ['https://www.douban.com/doulist/1641439/?start=0&sort=seq&playable=0&sub_type=']
    num = 0 # 爬取数目
    custom_settings = {  # 自定义该spider的pipeline输出
        'ITEM_PIPELINES': {
             'douban_movie.pipelines.MovieCommentPipeline20': 1,
        }
    }

    headers = {
        'User-Agent': f.user_agent(),
    }

    pages = 14 # 总的爬取页面数
    # page = 0   # 起始的页面号

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

    # scrapy请求的开始时start_request
    def start_requests(self):
        self.get_cookie()
        # 储存dns缓存
        _setDNSCache()
        # 获取movie_id构建转跳每条电影的评论页面
        data = pd.read_csv("./top_movie_id")
        id_list = data['movie_id'].tolist()[40:60]
        # 对每个电影
        for id in id_list:

            # 爬取当前页面
            p_addr ='https://movie.douban.com/subject/%s/comments?percent_type=h&start=0' % id
            m_addr ='https://movie.douban.com/subject/%s/comments?percent_type=m&start=0' % id
            l_addr ='https://movie.douban.com/subject/%s/comments?percent_type=l&start=0' % id
            addr_list= [p_addr,m_addr,l_addr]
            # addr_list = [p_addr]
            for addr in addr_list:
                page = 0
                url_set = []  # 话题url的集合
                yield scrapy.Request(url=addr,
                                     headers=self.headers,
                                     callback=self.parse_comment_url,
                                     cookies=cookies_dict,
                                     dont_filter=True)

                # 获取所有翻页
                yield scrapy.Request(url=addr,
                                     headers=self.headers,
                                     meta={"url_set":url_set,"page":page},
                                     callback=self.parse_next_page,
                                     cookies=cookies_dict,
                                     dont_filter=True)

    # 获取所有next页面
    def parse_next_page(self, response):
        _setDNSCache()
        tail = response.xpath("//div[@class='article']/div[@id='comments']/div[@id='paginator']/a[@class='next']/@href").extract_first()
        # print(tail)
        url_set = response.meta["url_set"]
        page = response.meta["page"]
        id =re.findall("\d+", response.url)[0]
        try:
            if tail and (page < self.pages):
                print("正在获取%s所有页面信息"%id)
                next_url = response.urljoin(tail)
                url_set.append(next_url)
                page += 1
                # 将 「下一页」的链接传递给自身，并重新分析,获取所有页面信息
                yield scrapy.Request(url=next_url,
                                     cookies=cookies_dict,
                                     headers=self.headers,
                                     meta={"url_set":url_set,"page": page},
                                     callback=self.parse_next_page,
                                     dont_filter=True)
            else:
                size= (len(url_set)+1)*3*20
                print("我已经爬id为%s的"%id+"电影%d条!!!!"%size)
                for url in url_set:
                    yield scrapy.Request(url=url,
                                         cookies=cookies_dict,
                                         headers=self.headers,
                                         callback=self.parse_comment_url,
                                         dont_filter = True
                                         )

        except:
            print("下页错误!!!")
            print(response.status)
            print(response.urljoin(response.xpath('//a[@class="next"]/@href').extract()))
            return

    def parse_comment_url(self, response):
        _setDNSCache()
        comment = DoubanMovieCommentItem()
        comment['movie_id'] = re.findall("\d+", response.url)[0]
        comment['URL'] = response.url
        items = response.xpath('//div[@class="comment-item "]')
        self.num+=20
        for item in items:
            # 短评的唯一id

            comment['comment_id'] = int(
                item.xpath('div[@class="comment"]/h3/span[@class="comment-vote"]/input/@value').extract()[0].strip())
            # 多少人评论有用
            comment['useful_num'] = \
            item.xpath('div[@class="comment"]/h3/span[@class="comment-vote"]/span/text()').extract()[0].strip()
            # 评分
            comment['star'] = \
            item.xpath('div[@class="comment"]/h3/span[@class="comment-info"]/span[2]/@class').extract()[0].strip()
            # 评论时间
            comment['time'] = item.xpath(
                'div[@class="comment"]/h3/span[@class="comment-info"]/span[@class="comment-time "]/@title').extract()
            # 评论内容
            comment['content'] = item.xpath('div[@class="comment"]/p/span/text()').extract()
            # 评论者名字（唯一）
            comment['people'] = item.xpath('div[@class="avatar"]/a/@title').extract()[0]
            # 评论者页面
            comment['people_url'] = item.xpath('div[@class="avatar"]/a/@href').extract()[0]

            yield comment
        if self.num % 100 == 0:
            print("*****************当前爬了%d条****************"%self.num)
        if self.num % 2000 ==0:
            self.get_cookie()
        # print(self.num)