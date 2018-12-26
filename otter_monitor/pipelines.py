# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

import os, re, json, subprocess, logging
from datetime import datetime, timedelta

def getAlertNums(host):
    # tail alert log
    pipe = subprocess.Popen("tail -n 200 log/otter_restart.log", shell=True, stdout=subprocess.PIPE)
    lines = pipe.stdout.readlines()
    # extract info
    d = {}
    pattern='^\[(\d+\-\d+\-\d+ \d+:\d+:\d+)\] - Host:(\d+\.\d+\.\d+\.\d+), Channel ID: (\d+), Pipeline ID: (\d+), Pipeline Name: ([0-9a-zA-Z_]+).*$'
    regex=re.compile(pattern)
    for line in lines:
        r = regex.match(line.decode('utf-8'))
        if not r:
            continue
        grp = r.groups()
        if grp[1] == host and (datetime.now() - datetime.strptime(grp[0], '%Y-%m-%d %H:%M:%S')).hours < 5:
            d[(grp[1], grp[2], grp[3])] = d.get((grp[1], grp[2], grp[3]), default=[]).append(datetime.strptime(grp[0], '%Y-%m-%d %H:%M:%S'))
    return len([k for (k,v) in d.items() if len(v)>=3])
    
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
        with open("log/otter_alert.log", "a") as f:
            if len(alertSortList) > 0:
                f.write('-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n-- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - -- - --\n')
                for item in alertSortList:
                    f.write('[%s] - Host: %s, Channel ID: %s, Pipeline ID: %s, Pipeline Name: %s, mainstem状态: %s, 最后位点时间: %s\n' %
                        (datetime.now(), item['host'], item['channelId'], item['pplId'], item['pplName'], item['pplStatus'], item['lastSync']))
                    self.host = item['host']
            else:
                f.write('[%s] - \n' % datetime.now())
        with open("log/otter_restart.log", "a") as f:
            for item in [i for i in alertSortList if (datetime.now()-datetime.strptime(i['lastSync'], '%Y-%m-%d %H:%M:%S')).seconds > 120*60]:
                f.write('[%s] - Host: %s, Channel ID: %s, Pipeline ID: %s, Pipeline Name: %s' %
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), item['host'], item['channelId'], item['pplId'], item['pplName']))
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
