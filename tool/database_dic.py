#!/usr/bin/env python
# -*- coding:utf-8 -*-

import xlwt, pymysql

output_file = "nbest_dic.xls"

# 创建数据库连接
conn = pymysql.connect(host='localhost', port=3306, user='dbuser', passwd='dbpass', db='test')

sql = '''
SELECT concat(concat(t1.table_schema, '.'), t1.table_name) table_name
  ,t2.table_comment
  ,t1.column_name
  ,t1.column_type
  ,t1.column_default
  ,t1.is_nullable
  ,case t1.column_key
    when 'PRI' then '主键约束'
    when 'UNI' then '唯一约束'
    when 'MUL' then '可以重复'
  end column_key
  ,t1.column_comment
  ,t1.ordinal_position
from information_schema.columns t1
join information_schema.tables t2
on t1.table_schema = t2.table_schema
and t1.table_name = t2.table_name
where t1.table_schema not in ('information_schema', 'mysql', 'sys', 'retl', 'mysqlslap', 'test', 'performance_schema')
'''
cursor = conn.cursor()
cursor.execute(sql)
rows = cursor.fetchall()
tables = list(set(row[:2] for row in rows))

# 设置单元格格式
style = xlwt.XFStyle()
pattern = xlwt.Pattern()
pattern.pattern = xlwt.Pattern.SOLID_PATTERN
pattern.pattern_fore_colour = 0
style.pattern = pattern
fnt = xlwt.Font()
fnt.name = u'微软雅黑'
fnt.colour_index = 1
fnt.bold = True
style.font = fnt

book = xlwt.Workbook()
sheet_index = book.add_sheet('index')
sheet_index.write(0, 0, 'table_name', style)
sheet_index.write(0, 1, 'table_comment', style)
# Excel处理
for i in range(len(tables)):
    sheet = book.add_sheet('%05d' % i)
# row 1, table info
    sheet.write(0, 0, tables[i][0])
    sheet.write(0, 1, tables[i][1])
    sheet.write(0, 3, xlwt.Formula('HYPERLINK("#index!A1";"返回")'))
# row 2 and below, column info
    sheet.write(1, 0, 'column_name', style)
    sheet.write(1, 1, 'column_type', style)
    sheet.write(1, 2, 'column_default', style)
    sheet.write(1, 3, 'is_nullable', style)
    sheet.write(1, 4, 'column_key', style)
    sheet.write(1, 5, 'column_comment', style)
    sheet.write(1, 6, 'ordinal_position', style)
    columns = [row[2:] for row in rows if row[0]==tables[i][0]]
    for r in range(len(columns)):
        for c in range(len(columns[0])):
            sheet.write(r+2, c, columns[r][c])
    link = 'HYPERLINK("#%s!A1";"%s")' % ('%05d' % i, '%s' % tables[i][0])
    sheet_index.write(i+1, 0, xlwt.Formula(link))
    sheet_index.write(i+1, 1, tables[i][1])
book.save(output_file)
conn.close()    
