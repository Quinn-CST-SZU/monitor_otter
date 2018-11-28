# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import logging

class OtterPipeline(object):
    '''
    class docstring
    '''
    def process_item(self, item, spider):
        '''
        function docstring
        '''
        logging.info(item)
        return item

    def close_spider(self, spider):
        '''
        function docstring
        '''
        pass
