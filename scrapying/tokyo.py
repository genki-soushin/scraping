#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import codecs
import csv
import requests
import ssl
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# CONST
HEADERS = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_3) AppleWebKit/602.4.8 (KHTML, like Gecko) Version/10.0.3 Safari/602.4.8'}

# get image url from thumbnail
# Return text "NO IMAGE" if no image
def getImageURL(block):
    imageTagData = block.select_one('div.cassetteitem_object-item img[src]')
    if imageTagData.has_attr('rel'):
        return imageTagData['rel']
    else:
        return "NO IMAGE"

# get all items without Class
# もしクラス違いがあったりするとタグだけで取れないとき(getAllWithTagClass)で,
# クラス("")空白にすることはできるがクラスがあるやつを取得しなくなる
def getAllWithTag(source, tag):
    return source.find_all(tag)

# get all items with Class
def getAllWithTagClass(source, tag, className):
    return source.find_all(tag, attrs={'class':className})

# 指定タグの中のテキストを取得することができる
def getTextWithTag(tag, block, className):
    return block.find(tag, attrs={'class':className}).text

# 同じタグの子供が2つある場合これで取ってこれる
def getTextWithTag2(tag, block):
    data = block.find_all(tag)
    return data[0].text + "," + data[1].text
# 同じタグの子供が３つある場合これで取ってこれる
def getTextWithTag3(tag, block):
    data = block.find_all(tag)
    return data[0].text + "," + data[1].text + "," + data[2].text

# get item with li tag
def getItemWithLi(block, className):
    return block.find('li', attrs={'class': className})

# to retrieve each data
# 今回使わん　aptPicture = 画像URL = データx1　
# 今回使わん　aptName = 物件名 = データx1
# aptAddress = 住所 = データx1
# aptTransportation = 交通手段 = データx3
# aptDetail = 築年数/階数 = データx2
###
def generateBasicData(item):
    aptPicture, aptName, aptAddress = "", "", ""
    aptTransportation, aptDetail, comma = "", "", ","
    #aptPicture = getImageURL(item) # get aptPicture
    #aptName = getTextWithTag('div', item, 'cassetteitem_content-title') # get aptName
    aptAddress = getTextWithTag('li', item, 'cassetteitem_detail-col1') # get aptAddress
    cassetteitem_detail_col2s = getItemWithLi(item, 'cassetteitem_detail-col2') # get a block for aptTransportation
    aptTransportation = getTextWithTag3('div', cassetteitem_detail_col2s) # get aptTransportation

    #駅情報は3つあるのでカンマでsplitして一つ一つに分解する
    aptTransportationArray = aptTransportation.split(",")
    max = len(aptTransportationArray)
    newAptTransportationArray = []
    for i in range(0,max):
        if(aptTransportationArray[i]): # 駅と距離のバリューが存在するかどうか
            stationAndDist = aptTransportationArray[i].split("/")[1].split(" ") # 駅と距離をarrayで出す
            station, dist ="",""
            if(len(stationAndDist) == 2):
                station, dist = stationAndDist[0], stationAndDist[1]
                if(dist[0] == "歩"):
                    dist = dist[1:-1]
                else: # バスだった場合は除外する
                    station, dist = "-", "-"
            else: # もし 駅と距離が1セットでない場合は除外する　例: (有楽町駅 バス16分 (バス停)勝どき3丁目 歩1分)
                station, dist = "-", "-"
        else:
            station, dist = "-", "-"
        newAptTransportationArray.append(station)
        newAptTransportationArray.append(dist)
    aptTransportation = ",".join(newAptTransportationArray)
    return aptAddress + comma + aptTransportation + comma + aptDetail

    cassetteitem_detail_col3s = getItemWithLi(item, 'cassetteitem_detail-col3') # get a block for aptDetail
    aptDetail = getTextWithTag2('div', cassetteitem_detail_col3s) # get aptDetail

    #築年数を数字にする現状階数はやる必要があるのか不明のためやっていない
    aptDetail = aptDetail.split(",")
    if (len(aptDetail[0]) == 2):
        aptDetail[0] = 0
    else:
        aptDetail[0] = aptDetail[0][1:-1]
    aptDetail = ",".join(aptDetail)
    return aptAddress + comma + aptTransportation + comma + aptDetail


# to retrieve each data
# [0]- [1]- [2]階 Floor [3]賃料 Rent [4]管理費 Admin [5]敷/礼/保証/敷引,償却 Sec
# [6]間取り type [7]専有面積 square [8]- [9]お気に入り [10]- Link
#
###
def generateRoomData(item):
    rmData = ""
    tds = getAllWithTag(item, 'td')
    for i in range(2,8):
        if((i == 2 or i == 4) and tds[i]): #階層の階もしくは管理費の円を削除
            rmData += tds[i].text[0:-1] + ","
        elif(i == 3 and tds[i]): #家賃の万円を消してintにする
            tds[i] = int(float(tds[i].text[0:-2])*10000)
            rmData += (str(tds[i]) + ",")
        elif(i == 5 and tds[i]): # 敷礼などを分解及び万円を消してintに
            tmp = tds[i].text.split("/")
            for j in tmp:
                if(j != "-"):
                    j = int(float(j[0:-2])*10000)
                    rmData += (str(j) + ",")
                else:
                    rmData += j + ","
        elif(i == 7 and tds[i]): #専有面積のm2を消してintにする
            rmData += (tds[i].text[0:-2])
        else:
            rmData += (tds[i].text + ",")
    #rmData += tds[10].find('a')['href'] # get Link(詳細ページ用)
    return rmData


# Generating data
#
###
def generateData(items, tmpDataList):
    basicDataInfo = ""
    for item in items:
        #basicDataInfoとは, 物件住所や移動手段、賃貸ルームではなく建物に対するデータについて
        basicDataInfo = generateBasicData(item)
        # 建物に対する部屋データを取得してroomsにinsert
        rooms = getAllWithTag(item, 'tbody')
        for room in rooms:
            # 部屋の情報を作っている
            roomDataInfo = generateRoomData(room)
            tmpDataList.append(basicDataInfo + "," + roomDataInfo)
    return tmpDataList

# to get pagenation
# return True if thre is next page else False(ページネーション)
def checkPagenation(source):
    pagenation = source.find('div', attrs={'class' : 'pagination pagination_set-nav'})
    backOrForward = pagenation.find_all("p")
    right = False
    for bof in backOrForward:
        bofText = bof.find('a').text
        if bofText == "次へ":
            right = True
    return right

def main():
    # set initial page number
    logging.info('STARTED')
    print('STARTED')
    page = 1
    url = "https://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=040&bs=040&ta=17&sc=17201&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2=&pn="
    dataList = ["住所,移動1,距離1,移動2,距離2,移動3,距離3,築年数,全階数,部屋階,賃料,管理費,敷,礼,保証,敷引|償却,間取り,専有面積,詳細リンク"] # to store each csv data
    fileName = "output"

    while True:

        query = url + str(page)
        response = requests.get(query, headers = HEADERS)

        # store contents in soup
        soup = BeautifulSoup(response.content, "html.parser")

        # Parent box which contain all the data for each apt
        items = getAllWithTagClass(soup, 'div', 'cassetteitem')

        # ここでcsvを生成している
        dataList = generateData(items, dataList) # update

        # break if there is no more "Next Page"
        if not checkPagenation(soup):
            break

        page += 1

        logging.info('PAGE: ' + str(page))
        print('PAGE: ' + str(page))
        break

    # with open(fileName + '.csv', 'w') as f:
    #     wr = csv.writer(f, delimiter='\n')
    #     wr.writerow(dataList)
    i = 0;
    data1 = dataList[0].split(',')
    data2 = dataList[1].split(',')
    for i in range(0, len(data1) - 2):
        print(data1[i] + " : " + data2[i])
    print("SUCCESS")

if __name__ == '__main__':
    main()
