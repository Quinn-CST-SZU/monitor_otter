# -*- coding: utf-8 -*-
import logging
logging.basicConfig(level=logging.INFO,
    format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',
    datefmt='%a, %d %b %Y %H:%M:%S',
    filename='log/otter_logging.log',
    filemode='a')
from datetime import datetime, timedelta

import scrapy
import urllib.request

class OtterSpider(scrapy.Spider):
    name = 'otter'
	host = 'localhost'
	port = '8080'
    #allowed_domains = ['otter.test']
	def __init__(self, host='localhost', port=8080 *args, **kwargs):
	    self.host = host
		self.port = port
		super(OtterSpider, self).__init__(*args, **kwargs)

    def start_requests(self):
        login_url = 'http://%s:%s/login.htm' % (self.host, self.port)
        formdata = {
            "redir": "http://%s:%s" % (self.host, self.port),
            "action": "user_action",
            "event_submit_do_login": "1",
            "_fm.l._0.n": "admin",
            "_fm.l._0.p": "admin"
        }
        yield scrapy.FormRequest(
            url=login_url,
            # cookie
            # headers
            formdata=formdata,
            callback=self.parse_channel)

    def parse_channel(self, response):
        pageIndex = response.xpath("//div[@class='page']/b/text()").extract()
        channels = response.xpath('//tr/td[@width="5%"]/text()').extract()
        for c in channels:
            yield scrapy.Request("http://%s:%s/pipeline_list.htm?channelId=%d" % (self.host, self.port, int(c)), \
                dont_filter=True, \
                callback=self.parse_pipeline, meta={'pageIndex': int(pageIndex[0]), 'channelId': int(c)})
        # has next ?
        selNext = self.get_next(response.xpath("//div[@class='page']/a[@class='prev']"))
        if selNext:
            formdata = {
                'pageIndex': selNext.xpath('@onclick').extract()[0][-2],
                'searchKey': ''
            }
            # self.logger.info('Parse Channel{next=%s}' % formdata['pageIndex'])
            yield scrapy.FormRequest.from_response(response, dont_filter=True, formdata=formdata, callback=self.parse_channel)

    def get_next(self, sels):
        for sel in sels:
            if '下一页' in sel.xpath('text()').extract():
                return sel

    def parse_pipeline(self, response):
        channelId = response.meta['channelId']
        pageIndex = response.meta['pageIndex']
        # self.logger.info('Parse Pipeline{channelId=%d, pageIndex=%d}' % (channelId, pageIndex))
        pplNames = response.xpath("//td[@width='6%']/div/a")
        pplIds = response.xpath("//td[@width='3%']")
        pplIds = pplIds[::int(len(pplIds)/len(pplNames))]
        status = response.xpath("//td[@width='5%']")
        status = status[::int(len(status)/len(pplNames))]
        for i in range(len(status)):
            status[i] = status[i] if len(status[i].xpath('text()')[0].extract().strip())>0 else status[i].xpath('*')
        lastSync = response.xpath("//td[@width='8%']")
        lastSync = lastSync[1::int(len(lastSync)/len(pplNames))]
        for i in range(len(pplNames)):
            if status[i].xpath('text()').extract()[0].strip() != '工作中' or  (datetime.now()-datetime.strptime(lastSync[i].xpath('text()').extract()[0].strip(), "%Y-%m-%d %H:%M:%S")).seconds>30*60:
                yield {"host": self.host,
				    "channelId": channelId,
                    "pplId": pplIds[i].xpath('text()').extract()[0].strip(),
                    "pplName": pplNames[i].xpath('text()').extract()[0].strip(),
                    "pplStatus": status[i].xpath('text()').extract()[0].strip(),
                    "lastSync": lastSync[i].xpath('text()').extract()[0].strip()}
                if (datetime.now()-datetime.strptime(lastSync[i].xpath('text()').extract()[0].strip(), "%Y-%m-%d %H:%M:%S")).seconds >= 120*60 and \
                    (datetime.now()-datetime.strptime(lastSync[i].xpath('text()').extract()[0].strip(), "%Y-%m-%d %H:%M:%S")).seconds < 150*60:
                    yield scrapy.Request("http://%s:%s/channel_list.htm?action=channelAction&channelId=%d&status=stop&pageIndex=%d&searchKey=&eventSubmitDoStatus=true" % (self.host, self.port, channelId, pageIndex), \
                        dont_filter=True, 
                        callback=self.stop_channel, \
                        meta={'pageIndex':pageIndex, 'channelId':channelId})

    def stop_channel(self, response):
        channelId = response.meta['channelId']
        pageIndex = response.meta['pageIndex']
        self.logger.info('http://%s:%s/?action=channelAction&channelId=%d&status=start&pageIndex=%d&searchKey=&eventSubmitDoStatus=true' % (self.host, self.port, channelId, pageIndex))
        yield scrapy.Request("http://%s:%s/?action=channelAction&channelId=%d&status=start&pageIndex=%d&searchKey=&eventSubmitDoStatus=true" % (self.host, self.port, channelId, pageIndex), \
            dont_filter=True, 
            callback=self.start_channel, \
            meta={'pageIndex': pageIndex, 'channelId': channelId})

    def start_channel(self, response):
        self.logger.info('host: %s, channelId: %s, pageIndex: %s has been restarted' % (self.host, response.meta['channelId'], response.meta['pageIndex']))
