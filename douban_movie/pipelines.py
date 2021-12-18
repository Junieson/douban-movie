# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import codecs
import json
from itemadapter import ItemAdapter


class MovieItemPipeline:
    def __init__(self):
        self.file = codecs.open('./data/movie_item1.json', 'a', encoding='utf-8')

    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item

    def spider_closed(self, spider):
        self.file.close()

################ Comment ####################

class MovieCommentPipeline20(object):
    def __init__(self):
        self.file = codecs.open('./data/movie_comment60.json', 'a', encoding='utf-8')
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
    def spider_closed(self, spider):
        self.file.close()

################ people ####################
class MoviePeoplePipeline(object):
    def __init__(self):
        self.file = codecs.open('./data/movie_people1.json', 'a', encoding='utf-8')
    def process_item(self, item, spider):
        line = json.dumps(dict(item), ensure_ascii=False) + "\n"
        self.file.write(line)
        return item
    def spider_closed(self, spider):
        self.file.close()
