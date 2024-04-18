# -*- coding: utf-8 -*-
import os
import requests
import io
from bs4 import BeautifulSoup as BS
from fastapi import FastAPI
import uvicorn
import json
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

"""从网上爬取数据"""
headers = {
    "Origin": "https://piao.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'Connection': 'close'
}

with io.open(os.path.join('output', 'cityName2City.json'),'r',encoding='utf8')as f:
    cityName2City = json.load(f)

base = 'https://you.ctrip.com'

class BasicInfo(BaseModel):
    cityName: str
    name: str

@app.post("/restaurant/get")
def getRestaurantInfo(restaurantInfo : BasicInfo):
    city = cityName2City[restaurantInfo.cityName]
    url = base + '/restaurantlist/'+ city + '/list-p1.html?keywords=' + restaurantInfo.name
    res = requests.get(url, headers=headers)
    soup = BS(res.text, "html.parser")
    href = base + soup.find_all(name='div', attrs={"class":'rdetailbox'})[0].dl.dt.a.get('href')

    res2 = requests.get(href, headers=headers)
    soup2 = BS(res2.text, "html.parser")

    res = {}

    res['name'] = soup2.find(name='div', attrs={"class":'f_left'}).h1.get_text()
    res['score'] = soup2.find(name='span', attrs={"class":'score'}).b.get_text()

    sightCon = soup2.find_all(name='span', attrs={"class":'s_sight_con'})
    if sightCon[0].find():
        sightCon[0] = sightCon[0].em.get_text()
    else:
        res['price'] = '暂无价格'
    res['caixi'] = []
    caixis = sightCon[1].dd.a
    for cai in caixis:
        res['caixi'].append(cai.get_text())
    res['phone'] = sightCon[2].get_text()
    res['address'] = sightCon[3].get_text()
    res['openTime'] = sightCon[4].get_text()

    res['imgs'] = []
    imgUrls = soup2.find_all(name='div', attrs={"class":'item'})
    for imgUrl in imgUrls:
        res['imgs'].append(imgUrl.a.get('href'))

    detailCon = soup2.find(name='div', attrs={"class":'detailcon'}).find(name='div', attrs={"class":'text_style'})
    res['characteristic'] = detailCon.p.get_text().replace(' ', '').replace('\r', '').replace('\n', '')
    
    return res

# print(getRestaurantInfo({
#     "cityName":"杭州",
#     "name":"杭州七宝"
# }))


@app.post("/shopping/get")
def getShoppingInfo(shoppingInfo : BasicInfo):
    city = cityName2City[shoppingInfo.cityName]
    url = base + '/shoppinglist/'+ city + '.html?keywords=' + shoppingInfo.name
    res = requests.get(url, headers=headers)
    soup = BS(res.text, "html.parser")
    href = base + soup.find_all(name='div', attrs={"class":'rdetailbox'})[0].dl.dt.a.get('href')

    res2 = requests.get(href, headers=headers)
    soup2 = BS(res2.text, "html.parser")

    res = {}

    res['name'] = soup2.find(name='div', attrs={"class":'f_left'}).h1.a.get_text()

    res['score'] = '暂无评分'
    if soup2.find(name='span', attrs={"class":'score'}):
        res['score'] = soup2.find(name='span', attrs={"class":'score'}).b.get_text()

    sightCon = soup2.find_all(name='span', attrs={"class":'s_sight_con'})
    res['address'] = sightCon[0].get_text().replace(' ', '').replace('\r', '').replace('\n', '')
    res['phone'] = sightCon[1].get_text().replace(' ', '').replace('\r', '').replace('\n', '')

    res['openTime'] = soup2.find(name='dl', attrs={"class":'s_sight_in_list'}).dd.get_text()

    res['imgs'] = []
    imgUrls = soup2.find_all(name='div', attrs={"class":'item'})
    for imgUrl in imgUrls:
        res['imgs'].append(imgUrl.a.get('href'))

    res['descript'] = []
    if soup2.find(name='div', attrs={"class":'toggle_l'}):
        description = soup2.find(name='div', attrs={"class":'toggle_l'}).div
        for descript in description.children:
            res['descript'].append(descript.get_text())
    else:
        res['descript'].append('暂无简介')
    
    return res

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=11113)