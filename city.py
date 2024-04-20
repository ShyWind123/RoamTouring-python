# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup as BS
import pymongo

client = pymongo.MongoClient(host='8.134.215.31',
                              port=27017,
                              username='root',
                              password='IamOP114514')
db = client.RoamTouring
collection = db.citys

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

# 爬取城市名字
citylistURL = "https://you.ctrip.com/countrysightlist/china110000/p1.html"
soup = BS(requests.get(citylistURL, headers=headers).text, 'html.parser')
pageNum = soup.find(name="b", attrs={"class": "numpage"}).get_text()
for i in range(1, int(pageNum)+ 1):
# for i in range(1, 10):
    citylistURL = "https://you.ctrip.com/countrysightlist/china110000/p" + str(i) + ".html"
    response = requests.get(citylistURL, headers=headers)
    html = response.text
    soup = BS(html, 'html.parser')
    cityList = soup.find_all(name="div", attrs={"class": "list_mod1"})
    citys = []
    for city in cityList:
        cityName = city.dl.dt.a
        cityHerf = cityName.get('href')
        citys.append({
            'id':getCityId(cityHerf[7:len(cityHerf) - 5]),
            'cityName':cityName.get_text(),
            'city':cityHerf[7:len(cityHerf) - 5]
        })
        print(cityName.get_text(),cityHerf[7:len(cityHerf) - 5])
    collection.insert_many(citys)
    print("第",i,"页完成")