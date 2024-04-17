# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup as BS
import json
import happybase

def findAttraction (cityName, id):
  con = happybase.Connection('8.134.215.31',9090)
  con.open()
  table = con.table('Attractions-' + cityName)  # games是表名，table('games')获取某一个表对象
  # 查看信息
  one_row = table.row(str(id))  # 获取一行数据,0001是行键
  print("查询", cityName, id)
  for key in one_row.keys():  # 遍历字典
      keyVal = key.decode('utf-8')
      val = one_row[key].decode('utf-8')
      if keyVal[0:9] != 'basicInfo':
          print('', keyVal, json.loads(val))
      else:
          print('', keyVal, val) 
  con.close()  # 关闭传输

findAttraction('杭州', '1')