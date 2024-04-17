# -*- coding: utf-8 -*-
import os
import requests
import io
from bs4 import BeautifulSoup as BS
import json

"""从网上爬取数据"""
headers = {
    "Origin": "https://piao.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'Connection': 'close'
}

# 爬取城市名字
citys = []
citylistURL = "https://you.ctrip.com/countrysightlist/china110000/p1.html"
soup = BS(requests.get(citylistURL, headers=headers).text, 'html.parser')
pageNum = soup.find(name="b", attrs={"class": "numpage"}).get_text()
cnt = 1
for i in range(1, int(pageNum)+ 1):
# for i in range(1, 10):
    citylistURL = "https://you.ctrip.com/countrysightlist/china110000/p" + str(i) + ".html"
    response = requests.get(citylistURL, headers=headers)
    html = response.text
    soup = BS(html, 'html.parser')
    cityList = soup.find_all(name="div", attrs={"class": "list_mod1"})
    for city in cityList:
        cityName = city.dl.dt.a
        cityHerf = cityName.get('href')
        citys.append({
            'cityName':cityName.get_text(),
            'city':cityHerf[7:len(cityHerf) - 5]
        })
        print(cnt, cityName.get_text())
        cnt += 1

with io.open(os.path.join("output", "city.json"), 'w', encoding="utf-8") as f:
    json.dump(citys, f, ensure_ascii=False)