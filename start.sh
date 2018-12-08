#!/bin/sh

cd /kettle/scripts/otter_monitor/ && /opt/anaconda3/bin/scrapy crawl otter -a host=127.16.3.1 -s LOG_FILE=/kettle/scripts/log/otter_logging.log
cd /kettle/scripts/otter_monitor/ && /opt/anaconda3/bin/scrapy crawl otter -a host=127.16.3.2 -s LOG_FILE=/kettle/scripts/log/otter_logging.log
