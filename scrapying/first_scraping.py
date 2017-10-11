import csv
import requests
import ssl
from bs4 import BeautifulSoup
from datetime import datetime

# quote_page = 'http://www.bloomberg.com/quote/SPX:IND'
# page = requests.get(quote_page)
# content = page.content
# soup = BeautifulSoup(content)
# # Take out the <div> of name and get its value
# name_box = soup.find('h1', attrs={'class': 'name'})
#
# # strip() is used to remove starting and trailing
# name = name_box.text.strip()
# print(name)
#
# # get the index price
# author = soup.find('small', attrs={'class':'author'})
# price = price_box.text
# print(price)
#

page = 1
url = "http://quotes.toscrape.com/page/{page}/"
with requests.Session() as session:
    while True:
        response = session.get(url.format(page=page))
        soup = BeautifulSoup(response.content, "html.parser")

        quotes = soup.find_all('div', attrs={'class':'quote'})

        for quote in quotes:
            print(quote.find('small', attrs={'class':'author'}))
            #print(author)

        print(page)

        if soup.find(class_="next") is None:
            break  # last page

        page += 1

# open a csv file with append, so old data will not be erased
# with open('index.csv', 'a') as csv_file:
#     writer = csv.writer(csv_file)
#     writer.writerow([name, price, datetime.now()])
