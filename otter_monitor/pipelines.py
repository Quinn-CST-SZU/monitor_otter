# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os, re, json, subprocess, logging
from datetime import datetime, timedelta
from collections import Counter

def getAlertNums(host):
    # tail alert log
    pipe = subprocess.Popen("tail -n 400 /kettle/scripts/log/alert_otter.log | grep -v -e '---*' -e '- $'", shell=True, stdout=subprocess.PIPE)
    lines = pipe.stdout.readlines()
    # extract info
    l = []
    pattern='^\[(\d+\-\d+\-\d+ \d+:\d+:\d+)\] - Host:(\d+\.\d+\.\d+\.\d+), Channel ID: (\d+).*$'
    regex=re.compile(pattern)
    for line in lines:
        r = regex.match(line.decode('utf-8'))
        if not r:
            continue
        grp = r.groups()
        if datetime.strptime(grp[0], '%Y-%m-%d %H:%M:%S') > datetime.now()-timedelta(hours=3) and grp[1] == host:
            l.append(grp)
    # calc alert record nums
    c = Counter(i[2] for i in l)
    # 160/180: channelId fail with 160 minutes in 180 minutes
    return len(i for i in c.values() if i > 160/5)
    
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
    host = ''
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
                f.write('-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n')
                for item in alertSortList:
                    f.write('[%s] - Host: %s, Channel ID: %s, Pipeline ID: %s, Pipeline Name: %s, mainstem状态: %s, 最后位点时间: %s\n' %
                        (datetime.now(), item['host'], item['channelId'], item['pplId'], item['pplName'], item['pplStatus'], item['lastSync']))
                    self.host = item['host']
            else:
                f.write('[%s] - \n' % datetime.now())
        # Should alert with dingding ?
        if not self.host:
            return
        # alertDingList = [i for i in alertSortList if (datetime.now()-datetime.strptime(i['lastSync'], "%Y-%m-%d %H:%M:%S")).seconds > 150*60]
        params = {}
        alertNums = getAlertNums(self.host)
        if alertNums > 0:
            params['Receiver'] = 'Mr.Zhou'
            params['Message'] = 'Otter on %s has %d abnormal channels' % (self.host, alertNums)
            alert2DingDing(alert_item='otppldzt', **params)
