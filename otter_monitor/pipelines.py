# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os, json, logging
from datetime import datetime


def alert2DingDing(alert_item, alert_level=1, alart_type=3, **params):
    '''
    alert to dingding
    '''
    msg = {
        "systemName": "Otter监控预警",
        "alarmLevel": alert_level,
        "alarmType": alart_type,
        "monitorItem": alert_item,
        "params": params
    }
    postCmd = r'''curl -H "Content-Type: application/json" -X POST -d '%s' http://172.0.0.1:8081/api/sendAlarmMessage''' % json.dumps(msg)
    logging.warn(postCmd)

class OtterPipeline(object):
    '''
    class docstring
    '''
    alertList = []
    def process_item(self, item, spider):
        '''
        function docstring
        '''
        self.alertList.append(item)
        return item

    def close_spider(self, spider):
        '''
        function docstring
        '''
        alertSortList = sorted(self.alertList, key=lambda k:k['channelId'])
        with open("log/alert_info.log", "a") as f:
            if len(alertSortList) > 0:
                f.write('-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n \
-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n \
-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n')
                for item in alertSortList:
                    f.write('[%s] - Channel ID: %s, Pipeline ID: %s, Pipeline Name: %s, mainstem状态: %s, 最后位点时间: %s\n' %
                        (datetime.now(), item['channelId'], item['pplId'], item['pplName'], item['pplStatus'], item['lastSync']))
            else:
                f.write('[%s] - \n' % datetime.now())
        # Should alert with dingding ?
        alertDingList = [i for i in alertSortList if (datetime.now()-datetime.strptime(i['lastSync'], "%Y-%m-%d %H:%M:%S")).seconds > 150*60]
        params = {}
        if len(alertDingList) > 0:
            params['Receiver'] = 'Mr.Zhou'
            params['Message'] = 'Important!Important!Important!UC Vs. WC'
            alert2DingDing(alert_item='otppldzt', **params)
