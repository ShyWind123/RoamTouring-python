# -*- coding: utf-8 -*-
from math import floor
import os
import requests
import io
from bs4 import BeautifulSoup as BS
import time
import json
import happybase

con = happybase.Connection('8.134.215.31',9090)

requests.adapters.DEFAULT_RETRIES = 5
s = requests.session()
s.keep_alive = False

"""从爬到的样式表中获取图片url"""
def getURL(styleStr) :
    for i in range(len(styleStr)):
        if styleStr[i] == '(':
            l = i
        if styleStr[i] == ')':
            r = i;
    return styleStr[l:r+1]

def getCityId(cityStr) :
    for i in range(len(cityStr)):
        if cityStr[i] >= '0' and cityStr[i] <= '9':
            l = i
            break
    return cityStr[l:len(cityStr)]

def getCity(href) :
    r = href.rfind('/')
    l = href.rfind('/', 0, r)
    return href[(l + 1):r]

"""从网上爬取数据"""
headers = {
    "Origin": "https://piao.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'Connection': 'close'
}

with io.open(os.path.join('output', 'city.json'),'r',encoding='utf8')as f:
    citys = json.load(f)

base = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"

def getCityAttractions (i, start):
    l = []
    pageNum = 10
    tableName = 'Attractions-'+citys[i].get('cityName')

    # 获取总数
    payload = json.dumps({"scene":"online","districtId":getCityId(citys[i].get('city')),"index":1,"sortType":1,"count":pageNum,"filter":{"filterItems":[]},"coordinate":{"latitude":0,"longitude":0,"coordinateType":"WGS84"},"returnModuleType":"all","head":{"cid":"09031136412811096481","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":"","xsid":"","extension":[]}},ensure_ascii=False)
    payload=payload.encode("utf-8")
    response = requests.post(base, headers=headers, data = payload)
    ress = json.loads(response.text)

    totalNum = ress.get('totalCount')
    pageCnt = floor((start - 1) / pageNum) + 1
    cnt = (pageCnt - 1) * pageNum
    fakeCnt = 0

    completeInfo =str(i + 1)+ "."+ citys[i].get('cityName')+ ": 开始爬取"
    print(completeInfo)
    with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
        f.write("["+ time.asctime(time.localtime())+"] "+completeInfo + "\n")
    
    con.open()  # 打开传输
    needCreate = True
    tables = con.tables()
    for table in tables:
        if str(table, "UTF-8") == tableName:
            needCreate = False
            break
    if needCreate:
        families = {
            'basicInfo':dict(),
            'imgs':dict(),
            'detailInfo':dict(),
            'nearby':dict()
        }
        con.create_table(tableName, families)  
    con.close()  # 关闭传输

    while pageCnt * pageNum < totalNum:
    # while pageCnt < 3:
        payload = json.dumps({"scene":"online","districtId":getCityId(citys[i].get('city')),"index":pageCnt,"sortType":1,"count":pageNum,"filter":{"filterItems":[]},"coordinate":{"latitude":0,"longitude":0,"coordinateType":"WGS84"},"returnModuleType":"all","head":{"cid":"09031136412811096481","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":"","xsid":"","extension":[]}},ensure_ascii=False)
        payload=payload.encode("utf-8")
        response = requests.post(base, headers=headers, data = payload)
        ress = json.loads(response.text)
        attractions = ress.get("attractionList")

        for j in range(pageNum):
            try:
                cnt += 1
                # 获取子网页链接地址
                href = attractions[j].get('card').get('detailUrl')

                # 再次请求子网页，获取景点详细信息
                res = requests.get(href, headers=headers)
                # with open("3.html", "w", encoding="utf-8") as f:
                #     f.write(res.text)
                soupi = BS(res.text, "html.parser")

                name = soupi.find(name="div", attrs={"class":"title"}).h1.get_text()

                if not citys[i].get('city') == getCity(href):
                    print("    " , cnt, "/", totalNum, name,'  ', href)
                    continue
                fakeCnt += 1

                print("", fakeCnt,":", cnt, "/", totalNum, name,'  ', href)

                heat = '0'
                if soupi.find(name="div", attrs={"class":"heatScoreText"}):
                    heat = soupi.find(name="div", attrs={"class":"heatScoreText"}).get_text()

                introduce = []
                preferentialTreatmentPolicy = []
                serviceFacilities = []
                opentime = []
                moduleTitles = soupi.find_all(name="div", attrs={"class":"moduleTitle"})
                for moduleTitle in moduleTitles:
                    if moduleTitle.get_text() == '介绍':
                        for moduleCotent in moduleTitle.find_next_siblings('div')[0].children:
                            introduce.append(moduleCotent.get_text())
                    if moduleTitle.get_text() == '开放时间':
                        for moduleCotent in moduleTitle.find_next_siblings('div')[0].children:
                            opentime.append(moduleCotent.get_text())
                    if moduleTitle.get_text() == '优待政策':
                        for moduleCotent in moduleTitle.find_next_siblings('div')[0].children:
                            preferentialTreatmentPolicy.append(moduleCotent.get_text())
                    if moduleTitle.get_text() == '服务设施':
                        for moduleCotent in moduleTitle.find_next_siblings('div')[0].children:
                            serviceFacilities.append(moduleCotent.get_text())
                if introduce == None:
                    introduce.append('')
                if preferentialTreatmentPolicy == None:
                    preferentialTreatmentPolicy.append('')
                if serviceFacilities == None:
                    serviceFacilities.append('')
                if opentime == None:
                    opentime.append('')


                score = '暂无评分'
                if soupi.find(name="div", attrs={"class": "commentScore"}):
                    score = soupi.find(name="div", attrs={"class": "commentScore"}).p.get_text()

                imgs = []
                imglinks = soupi.find_all(name="div", attrs={"class":"swiperItem"})
                for img in imglinks:
                    imgs.append(getURL(img.attrs["style"]))

                position = ""
                phone = ""
                baseInfoTitles = soupi.find_all(name="p", attrs={"class": "baseInfoTitle"})
                if len(baseInfoTitles) >= 1:
                    position = baseInfoTitles[0].find_next_siblings('p')[0].get_text()
                if len(baseInfoTitles) >= 3:
                    phone = baseInfoTitles[2].find_next_siblings('p')[0].get_text()

                nearby = {
                    "nearbyAttractions":[],
                    "nearbyFoods":[],
                    "nearbyShoppingMalls":[]
                }
                nearbyList = soupi.find_all(name='div', attrs={"class": "nearbyList"})
                for nearbyAttraction in nearbyList[0].contents[1].contents[0].children:
                    score = '暂无评分'
                    if len(nearbyAttraction.contents[1].contents[1].find_all(recursive=False)) >= 2:
                        score = nearbyAttraction.contents[1].contents[1].contents[0].get_text()
                    nearby["nearbyAttractions"].append({
                        "image":nearbyAttraction.contents[0].img.get('src'),
                        "name":nearbyAttraction.contents[1].contents[0].get_text(),
                        "score":score,
                        "distance":nearbyAttraction.contents[1].contents[2].get_text(),
                    })
                for nearbyFood in nearbyList[1].contents[1].contents[0].children:
                    score = '暂无评分'
                    if len(nearbyFood.contents[1].contents[1].find_all(recursive=False)) >= 2:
                        score = nearbyFood.contents[1].contents[1].contents[0].get_text()
                    nearby["nearbyFoods"].append({
                        "image":nearbyFood.contents[0].img.get('src'),
                        "name":nearbyFood.contents[1].contents[0].get_text(),
                        "score":score,
                        "distance":nearbyFood.contents[1].contents[2].get_text(),
                    })
                for nearbyShoppingMall in nearbyList[2].contents[1].children:
                    score = '暂无评分'
                    if len(nearbyShoppingMall.contents[1].contents[1].find_all(recursive=False)) >= 2:
                        score = nearbyShoppingMall.contents[1].contents[1].contents[0].get_text()
                    nearby["nearbyShoppingMalls"].append({
                        "image":nearbyShoppingMall.contents[0].img.get('src'),
                        "name":nearbyShoppingMall.contents[1].contents[0].get_text(),
                        "score":score,
                        "distance":nearbyShoppingMall.contents[1].contents[2].get_text(),
                    })

                price = attractions[j].get('card').get("priceTypeDesc")
                coordinate = {
                    "latitude" : attractions[j].get('card').get("coordinate").get("latitude"),
                    "longitude": attractions[j].get('card').get("coordinate").get("longitude")
                }

                info = {}
                info["id"] = fakeCnt
                info["name"] = name
                info["heat"] = heat
                info["score"] = score
                info["phone"] = phone
                info["position"] = position
                info["city"] = citys[i].get('cityName')
                info["price"] = price
                info["coordinate"] = coordinate

                info["introduce"] = introduce
                info["openTime"] = opentime
                info["preferentialTreatmentPolicy"] = preferentialTreatmentPolicy
                info["serviceFacilities"] = serviceFacilities
                
                info["imgs"] = imgs
                
                info["nearby"]=nearby

                l.append(info)

                con.open()  # 打开传输
                table = con.table(tableName)  # games是表名，table('games')获取某一个表对象
                attractionRow = {
                    'basicInfo:id': str(info['id']),
                    'basicInfo:name': info['name'],
                    'basicInfo:heat': info['heat'],
                    'basicInfo:score': info['score'],
                    'basicInfo:phone': info['phone'],
                    'basicInfo:position': info['position'],
                    'basicInfo:city': info['city'],
                    'basicInfo:price': info['price'],
                    'basicInfo:coordinate': json.dumps(info['coordinate']),
                    'imgs:imgs':json.dumps(info['imgs']),
                    'detailInfo:introduce':json.dumps(info['introduce']),
                    'detailInfo:openTime':json.dumps(info['openTime']),
                    'detailInfo:preferentialTreatmentPolicy':json.dumps(info['preferentialTreatmentPolicy']),
                    'detailInfo:serviceFacilities':json.dumps(info['serviceFacilities']),
                    'nearby:nearby':json.dumps(info['nearby'])
                }
                table.put(str(info['id']), attractionRow)  # 提交数据
                con.close()  # 关闭传输

                time.sleep(5)
            except Exception as e:
                print("E",e)
                with io.open(os.path.join("logs", "error.txt"), "a", encoding="utf-8") as f:
                    f.write("["+time.asctime(time.localtime())+"] "+ str(e) + "\n")
                pass
        
        completeInfo = " "+ citys[i].get('cityName')+ "第"+str(pageCnt)+"页; 爬取完成:"+ str(cnt)+ "/"+ str(totalNum)
        print(completeInfo)
        with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
            f.write(" ["+ time.asctime(time.localtime())+ "] " + completeInfo + "\n")
        pageCnt += 1

    completeInfo =str(i + 1)+ "."+ citys[i].get('cityName')+ "爬取完成: 共"+ str(fakeCnt)+ "/"+ str(totalNum)+ "个" + "\n"
    print(completeInfo)
    with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
        f.write( "["+ time.asctime(time.localtime())+"] "+completeInfo + "\n")
    with io.open(os.path.join("output", citys[i].get('cityName')+'.json'), 'a', encoding="utf-8") as f:
        json.dump(l, f, ensure_ascii=False)


for i in range(0,1500):
# for i in range(1500,len(citys)):
    getCityAttractions(i, 1)