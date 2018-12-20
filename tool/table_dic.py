#!/usr/bin/env python
# -*- coding:utf-8 -*-

import datetime 

import pymysql
import pandas as pd

output_file = "_dic.xls"

# 创建数据库连接
conn = pymysql.connect(host='localhost', port=3306, user='username', passwd='password', db='test')

sql = '''
SELECT concat(concat(table_schema, '.'), table_name) table_name
  ,column_name
  ,column_type
  ,column_default
  ,is_nullable
  ,case column_key
    when 'PRI' then '主键'
    when 'UNI' then '唯一键'
    when 'MUL' then '可重复'
  end column_key
  ,column_comment
  ,ordinal_position
from information_schema.columns
where table_schema not in ('information_schema', 'mysql', 'sys', 'retl', 'mysqlslap', 'test', 'performance_schema')
'''
df = pd.read_sql(sql, con=conn)

writer = pd.ExcelWriter(output_file)
# Excel处理
for name in set(df['table_name']):
    df_t = df[df['table_name'] == name]
    
    # df_t.columns=["数据表名", "数据列名", "列类型", "列默认值", "是否可为空值", "键约束", "列备注", "字段序号"]
    df_t.to_excel(writer, sheet_name=name.replace('fb4_', '')[:31], index=False)

df['table_name'].drop_duplicates().to_excel(writer, sheet_name="目录", index=False)
writer.save()
conn.close()
