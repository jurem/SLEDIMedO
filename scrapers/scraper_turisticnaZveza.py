# -*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
''' 
    popravi sumnike!!!
'''

SOURCE = 'TURISTICNA-ZVEZA'

base_url = 'http://www.turisticna-zveza.si'
full_url = 'http://www.turisticna-zveza.si/novice.php?stran=' #kasneje dodas se stevilo strani (1, 2, ...)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}



def makeHash(title, date):
    return hashlib.sha1((title+date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def getLink(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    print('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('header > h2')
    if raw_date:
        date = raw_date[0].text
        return date[8:]
    print('date not found, update select() method')
    return '1.1.1111' #1.1.1111 means original date was not found


def getTitle(soup):
    title = soup.select('header > h1')
    if title:
        return title[0].text.strip()
    print('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    print(url)
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='novica-vsebina')
    if content:
        text = content.text
        return ' '.join(text.split())
    print('content not found, update select() method')
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))



def getArticlesOn_n_pages(num_pages_to_check, session):
    articles = []
    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n+1), timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')
        articles += soup.find('section').find_all('article')
    return articles


def main():
    num_pages_to_check = 2
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_pages_to_check, session)
        articles_checked = len(articles)

        dates = []
        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            print(title)
            date = getDate(x)
            hash = makeHash(title, date)

            if is_article_new(hash):
                titles.append(title)
                dates.append(formatDate(date))
                hashes.append(hash)
                links.append(getLink(x))
                num_new_articles += 1

        list_of_tuples = []
        for i in range(len(links)):
            content = getContent(links[i], session)
            tup = (str(datetime.date.today()), titles[i], content, dates[i], hashes[i], links[i], base_url)
            list_of_tuples.append(tup)


        dbExecutor.insertMany(list_of_tuples)

    print(num_new_articles, 'new articles found,', num_pages_to_check,'pages checked -', articles_checked, 'articles checked')

if __name__ == '__main__':
    main()
