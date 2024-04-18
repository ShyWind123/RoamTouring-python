# -*- coding: utf-8 -*-
import os
import requests
import io
from bs4 import BeautifulSoup as BS
import json
import time

"""从网上爬取数据"""
headers = {
    "Origin": "https://piao.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'Connection': 'close'
}

def getCityId(cityStr) :
    l = 0
    r = len(cityStr)
    isGetL = False
    for i in range(len(cityStr)):
        if not isGetL and cityStr[i] >= '0' and cityStr[i] <= '9':
            l = i
            isGetL = True
        if isGetL and cityStr[i] == '/':
            r = i
            break
    return cityStr[l:r]

base = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"

with io.open(os.path.join('output', 'city.json'),'r',encoding='utf8')as f:
    citys = json.load(f)
    
# 爬取景点详情链接
def getArractionsList(i):
    attractions = []
    pageNum = 10
    totalNum = 3000
    pageCnt = 1
    cnt = 0
    
    completeInfo =str(i + 1)+ "."+ citys[i].get('cityName')+ ": 开始爬取"
    print(completeInfo)

    while pageNum * pageCnt < totalNum:
        payload = json.dumps({"scene":"online","districtId":getCityId(citys[i].get('city')),"index":pageCnt,"sortType":1,"count":pageNum,"filter":{"filterItems":[]},"coordinate":{"latitude":0,"longitude":0,"coordinateType":"WGS84"},"returnModuleType":"all","head":{"cid":"09031136412811096481","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":"","xsid":"","extension":[]}},ensure_ascii=False)
        payload=payload.encode("utf-8")
        response = requests.post(base, headers=headers, data = payload)
        ress = json.loads(response.text)
        attractionList = ress.get("attractionList")

        for j in range(0, pageNum):
            href = attractionList[j].get('card').get('detailUrl')
            name = attractionList[j].get('card').get('poiName')
            id = len(attractions) + 1

            cnt += 1
            if not getCityId(citys[i].get('city')) == getCityId(href):
                print("    " , cnt, "/", totalNum, name,'  ', href)
                continue
            
            print("", str(id),":", cnt, "/", totalNum, name,'  ', href)

            attractions.append({
                "id": id,
                "href" : href,
                "price" : attractionList[j].get('card').get("price"),
                "coordinate" : {
                    "latitude" : attractionList[j].get('card').get("coordinate").get("latitude"),
                    "longitude": attractionList[j].get('card').get("coordinate").get("longitude")
                }
            })
        
        pageCnt += 1
        
        completeInfo = " "+ citys[i].get('cityName')+ "第"+str(pageCnt)+"页; 爬取完成:"+ str(id)+ "/"+ str(totalNum)
        print(completeInfo)

    completeInfo =str(i + 1)+ "."+ citys[i].get('cityName')+ "爬取完成: 共"+ str(id)+ "/"+ str(totalNum)+ "个" + "\n"
    print(completeInfo)
      
    with io.open(os.path.join("attractionLists", citys[i].get('cityName')+".json"), 'w', encoding="utf-8") as f:
        json.dump(attractions, f, ensure_ascii=False)


for i in range(4, len(citys)):
    getArractionsList(i)