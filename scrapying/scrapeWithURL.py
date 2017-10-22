import csv
import sys
import requests
import ssl
import os
from bs4 import BeautifulSoup
from datetime import datetime

# get text with div tag
def findTextWithDiv(block, className):
    return block.find('div', attrs={'class':className}).text

# if two divs are under certain item with div tag
def findTextWithDivs2(block):
    data = block.find_all('div')
    return data[0].text, data[1].text

# get item with li tag
def findItemWithLi(block, className):
    return block.find('li', attrs={'class': className})

# to retrieve each data
def generateData(items, tmpDataList):
    apartmentName, apartmentAge, apartmentFloors, comma = "", "", "", ","
    for item in items:
        apartmentName = findTextWithDiv(item, 'cassetteitem_content-title')
        cassetteitem_detail_col3s = findItemWithLi(item, 'cassetteitem_detail-col3')
        apartmentAge, apartmentFloors = findTextWithDivs2(cassetteitem_detail_col3s)
        tmpDataList.append(apartmentName + comma + apartmentAge + comma + apartmentFloors)
    return tmpDataList

def findAllWithTag(source, tag, className):
    return source.find_all(tag, attrs={'class':className})

# to get pagenation
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
    # 取得したいでーたを持ってくる
    url = sys.argv[1]
    #url = "http://suumo.jp/jj/chintai/ichiran/FR301FC001/?ar=030&bs=040&ta=10&sc=10420&cb=0.0&ct=9999999&et=9999999&cn=9999999&mb=0&mt=9999999&shkr1=03&shkr2=03&shkr3=03&shkr4=03&fw2="

    page = 1
    dataList = ["名前,築年数,階数"] # to store each csv data
    fileName = "suumo3"
    with requests.Session() as session:
        while True:
            response = session.get(url.format(page=page))
            # store contents in soup
            soup = BeautifulSoup(response.content, "html.parser")

            # Parent box which contain all the data for each apartment
            items = findAllWithTag(soup, 'div', 'cassetteitem')
            dataList = generateData(items, dataList)
            
            # break if there is no more "Next Page"
            if not checkPagenation(soup):
                break

            page += 1

    with open(fileName + '.csv', 'w') as f:
        wr = csv.writer(f, delimiter='\n')
        wr.writerow(dataList)
    
    print("SUCCESS")
    
if __name__ == '__main__':
    main()