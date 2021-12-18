import json
import os
import scrapy
from faker import Factory
from .. import load
from douban_movie.items import DoubanMovieItem
import time, random

# 获取cookies
cookies_dict = dict()

# 随机请求头
f = Factory.create()


class MovieItemSpider(scrapy.Spider):
    name = 'movie_item'
    allowed_domains = ['m.douban.com', 'douban.com', 'movie.douban.com']
    start_urls = ['https://www.douban.com/doulist/1641439/?start=0&sort=seq&playable=0&sub_type=']
    num = 0  # 爬取数目
    # 自定义该spider的pipeline输出
    custom_settings = {
        'ITEM_PIPELINES': {
            'douban_movie.pipelines.MovieItemPipeline': 1,
        }
    }

    # request请求头
    headers = {
        'User-Agent': f.user_agent(),
    }

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
        db_findUrl = "https://www.douban.com/doulist/1641439/?start=0"
        # Scrapy发起其他页面请求时，带上cookies=cookies_dict即可，同时记得带上header值，
        yield scrapy.Request(url=db_findUrl,
                             cookies=cookies_dict,
                             callback=self.parse,
                             dont_filter=True,
                             headers=self.headers
                             )

    def parse(self, response):
        tr_list = response.xpath("//div[@class='doulist-item']")
        for tr in tr_list:
            item = DoubanMovieItem()
            # 获取票房
            item['box_office'] = tr.xpath("./div/div[@class='ft']/div/blockquote//text()").extract()[-1]
            href = tr.xpath(
                "./div[@class='mod']/div[@class='bd doulist-subject']/div[@class='title']/a/@href").extract_first()
            # 有一个页面获取不到链接就报错，中断导致该条请求后面的全结束，要捕获一场
            if href is None:
                no = tr.xpath("div[@class='mod']/div[@class='hd']/span/text()").extract_first()
                print("第 %s 条有问题" % no)
                continue
            yield scrapy.Request(
                href,
                callback=self.parse_details,
                cookies=cookies_dict,
                meta={"item": item},
                headers=self.headers,
                dont_filter=True
            )
            # 用来计数
            self.num += 1

        # 随机休息1到3秒
        time.sleep(random.random() * 3)
        print("当前已经爬了%d条" % self.num)
        # 翻页只爬前250
        if self.num < 250:
            if self.num in [75, 150, 200]:
                self.get_cookie()#重新改变cookies反爬
            yield scrapy.Request(
                'https://www.douban.com/doulist/1641439/?start=%s&sort=seq&playable=0&sub_type=' % self.num,
                callback=self.parse,
                dont_filter=True,
                cookies=cookies_dict,
                headers=self.headers,
            )
        pass

    def parse_details(self, response):
        movie_item = response.meta["item"]
        # movie id
        movie_item['movie_id'] = response.xpath('.//li/span[@class="rec"]/@id').extract()
        # movie title
        movie_item['movie_title'] = response.xpath('.//h1/span[@property="v:itemreviewed"]/text()').extract()
        # release_date
        movie_item['release_date'] = response.xpath('.//h1/span[@class="year"]/text()').extract()
        # 导演
        movie_item['directedBy'] = response.xpath('.//a[@rel="v:directedBy"]/text()').extract()
        # 电影主演
        movie_item['starring'] = response.xpath('.//a[@rel="v:starring"]/text()').extract()
        # 电影类别
        movie_item['genre'] = response.xpath('.//span[@property="v:genre"]/text()').extract()
        # 电影时长
        movie_item['runtime'] = response.xpath('.//span[@property="v:runtime"]/text()').extract()
        # 电影的国别和语言
        temp = response.xpath('.//div[@id="info"]/text()').extract()
        movie_item['country'] = [p for p in temp if (p.strip() != '') & (p.strip() != '/')][0].strip()
        movie_item['language'] = [p for p in temp if (p.strip() != '') & (p.strip() != '/')][1].strip()
        # 电影的评分
        movie_item['rating_num'] = response.xpath('.//strong[@class="ll rating_num"]/text()').extract()
        # 评分的人数
        movie_item['vote_num'] = response.xpath('.//span[@property="v:votes"]/text()').extract()
        # 电影1-5星的百分比
        movie_item['rating_per_stars5'] = response.xpath('.//span[@class="rating_per"]/text()').extract()[0].strip()
        movie_item['rating_per_stars4'] = response.xpath('.//span[@class="rating_per"]/text()').extract()[1].strip()
        movie_item['rating_per_stars3'] = response.xpath('.//span[@class="rating_per"]/text()').extract()[2].strip()
        movie_item['rating_per_stars2'] = response.xpath('.//span[@class="rating_per"]/text()').extract()[3].strip()
        movie_item['rating_per_stars1'] = response.xpath('.//span[@class="rating_per"]/text()').extract()[4].strip()
        # 电影的剧情简介
        intro = response.xpath('.//span[@class="all hidden"]/text()').extract()
        if len(intro):
            movie_item['intro'] = intro
        else:
            movie_item['intro'] = response.xpath('.//span[@property="v:summary"]/text()').extract()
        # 电影的短评数
        movie_item['comment_num'] = response.xpath('.//div[@class="mod-hd"]/h2/span/a/text()').extract()[0].strip()
        # 电影的提问数有的电影没有
        try:
            movie_item['question_num'] = response.xpath('.//div[@class="mod-hd"]/h2/span/a/text()').extract()[1].strip()
        except:
            movie_item['question_num'] = 0
        # 最后输出
        # yield movie_item
        print(movie_item)