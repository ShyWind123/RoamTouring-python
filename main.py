# -*- coding: utf-8 -*-
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

"""从网上爬取数据"""
headers = {
    "Origin": "https://piao.ctrip.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36",
    'Connection': 'close'
}



places = ["beijing1"]
placenames = ["北京"]

print(places)
print(placenames)

base = "https://m.ctrip.com/restapi/soa2/20684/json/productSearch"
base2 = "https://m.ctrip.com/restapi/soa2/18109/json/getAttractionList"

l = {}
for i in range(len(places)):
    l[placenames[i]] = []
    pageCnt = 1
    pageNum = 1
    totalNum = 100
    cnt = 0

    completeInfo =str(i + 1)+ "."+ placenames[i]+ ": 开始爬取"
    print(completeInfo)
    with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
        f.write("["+ time.asctime(time.localtime())+"] "+completeInfo + "\n")
    
    con.open()  # 打开传输
    families = {
        'basicInfo':dict(),
        'imgs':dict(),
        'detailInfo':dict(),
        'nearby':dict()
    }
    con.create_table('Attractions-'+placenames[i], families)  
    con.close()  # 关闭传输

    # while pageCnt * pageNum < totalNum:
    while pageCnt < 2:
        payload = json.dumps({"head":{"cid":"09031136412811096481","syscode":"999","extension":[{"name":"bookingTransactionId","value":"1713264847565_4585"}]},"imageOption":{"width":568,"height":320},"requestSource":"activity","destination":{},"filtered":{"pageIndex":pageCnt,"sort":"1","pageSize":pageNum,"tab":"Ticket2","items":[]},"productOption":{"needBasicInfo":True,"needComment":True,"needPrice":True,"needRanking":True,"needVendor":True,"tagOption":["PRODUCT_TAG","IS_AD_TAG","PROMOTION_TAG","FAVORITE_TAG","GIFT_TAG","COMMENT_TAG","IS_GLOBALHOT_TAG"]},"searchOption":{"filters":[],"needAdProduct":True,"returnMode":"all","needUpStream":False},"extras":{"needScenicSpotNewPrice":"true"},"debug":False,"contentType":"json","client":{"pageId":"10650038368","platformId":None,"crnVersion":"2022-12-01 20:32:03","location":{"cityId":None,"cityType":None,"locatedCityId":None,"lat":"","lon":""},"locale":"zh-CN","currency":"CNY","channel":114,"cid":"09031136412811096481","trace":"69e6faca-2505-552b-1f09-bad564862267","extras":{"client_locatedDistrictId":"0","client_districtId":getCityId(places[i])}}})
        response = requests.post(base, headers=headers, data=payload)
        ress = json.loads(response.text)
        vs = []
        for j in range(0, pageNum): 
            vs.append(ress.get('products')[j].get('basicInfo').get('detailUrl').get('URL'))

        if pageCnt == 1:
            totalNum = ress.get('total')

        for k in range(len(vs)):
            try:
                cnt += 1
                # 获取子网页链接地址
                href = vs[k]
                # 再次请求子网页，获取景点详细信息
                res = requests.get(href, headers=headers)
                # with open("3.html", "w", encoding="utf-8") as f:
                #     f.write(res.text)
                soupi = BS(res.text, "html.parser")

                name = soupi.find(name="div", attrs={"class":"title"}).h1.get_text()

                print("", cnt, "/", totalNum, name, href)

                heat = 0
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

                score = '暂无评分'
                if soupi.find(name="div", attrs={"class": "commentScore"}):
                    score = soupi.find(name="div", attrs={"class": "commentScore"}).p.get_text()

                imgs = []
                imglinks = soupi.find_all(name="div", attrs={"class":"swiperItem"})
                for img in imglinks:
                    imgs.append(getURL(img.attrs["style"]))

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

                payload2 = json.dumps({"scene":"onlinesearch","districtId":getCityId(places[i]),"index":1,"sortType":1,"count":1,"filter":{"filterItems":["0"]},"keyword":name ,"coordinate":{"latitude":0,"longitude":0,"coordinateType":"WGS84"},"returnModuleType":"all","head":{"cid":"09031136412811096481","ctok":"","cver":"1.0","lang":"01","sid":"8888","syscode":"09","auth":"","xsid":"","extension":[]}},ensure_ascii=False)
                payload2=payload2.encode("utf-8")
                response2 = requests.post(base2, headers=headers, data = payload2)
                ress2 = json.loads(response2.text)
                attraction = ress2.get("attractionList")[0].get("card")
                price = attraction.get("priceTypeDesc")
                coordinate = {
                    "latitude" : attraction.get("coordinate").get("latitude"),
                    "longitude": attraction.get("coordinate").get("longitude")
                }

                info = {}
                info["id"] = k + 1
                info["name"] = name
                info["heat"] = heat
                info["score"] = score
                info["phone"] = phone
                info["position"] = position
                info["city"] = placenames[i]
                info["price"] = price
                info["coordinate"] = coordinate

                info["introduce"] = introduce
                info["openTime"] = opentime
                info["preferentialTreatmentPolicy"] = preferentialTreatmentPolicy
                info["serviceFacilities"] = serviceFacilities
                
                info["imgs"] = imgs
                
                info["nearby"]=nearby

                l[placenames[i]].append(info)

                con.open()  # 打开传输

                table = con.table('Attractions-'+placenames[i])  # games是表名，table('games')获取某一个表对象

                attractionRow = {
                    'basicInfo:id': info['id'],
                    'basicInfo:name': info['name'],
                    'basicInfo:heat': info['heat'],
                    'basicInfo:score': info['score'],
                    'basicInfo:phone': info['phone'],
                    'basicInfo:position': info['position'],
                    'basicInfo:city': info['city'],
                    'basicInfo:price': info['price'],
                    'basicInfo:coordinate': info['coordinate'],
                    'imgs:imgs':info['imgs'],
                    'detailInfo:introduce':info['introduce'],
                    'detailInfo:openTime':info['openTime'],
                    'detailInfo:preferentialTreatmentPolicy':info['preferentialTreatmentPolicy'],
                    'detailInfo:serviceFacilities':info['serviceFacilities'],
                    'nearby:nearby':info['nearby']
                }
                table.put(info['id'], attractionRow)  # 提交数据，0001代表行键，写入的数据要使用字典形式表示

                # 下面是查看信息，如果不懂可以继续看下一个
                one_row = table.row(info['id'])  # 获取一行数据,0001是行键
                for value in one_row.keys():  # 遍历字典
                    print(value.decode('utf-8'), one_row[value].decode('utf-8'))  # 可能有中文，使用encode转码
                con.close()  # 关闭传输

                time.sleep(5)
            except Exception as e:
                print("E",e)
                with io.open(os.path.join("logs", "error.txt"), "a", encoding="utf-8") as f:
                    f.write("["+time.asctime(time.localtime())+"] "+ e + "\n")
                pass
        
        completeInfo = str(i + 1) + "."+ placenames[i]+ "第"+str(pageCnt)+"页; 爬取完成:"+ str(cnt)+ "/"+ str(totalNum)
        print(completeInfo)
        with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
            f.write(" ["+ time.asctime(time.localtime())+ "] " + completeInfo + "\n")
        pageCnt += 1

    completeInfo =str(i + 1)+ "."+ placenames[i]+ "爬取完成: 共"+ str(cnt)+ "/"+ str(totalNum)+ "个" + "\n"
    print(completeInfo)
    with io.open(os.path.join("logs", "progress.txt"), "a", encoding="utf-8") as f:
        f.write( "["+ time.asctime(time.localtime())+"] "+completeInfo + "\n")

with io.open(os.path.join("output","output.json"), 'w', encoding="utf-8") as f:
    json.dump(l, f, ensure_ascii=False)