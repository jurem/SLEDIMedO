from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
''' 
    
'''

base_url = 'http://www.velenjcan.si'
full_urls = ['http://www.velenjcan.si/nb/novice?page=',
             'http://www.velenjcan.si/nb/blog?page='] 
             #kasneje dodas se stevilo strani (1, 2, ...)

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def makeHash(title, date):
    return hashlib.sha1((title+date).encode('utf-8')).hexdigest()


def isArticleNew(hash):
    is_new = False
    try:
        f = open(('article_list.txt'), 'r+')
    except FileNotFoundError:
        f = open(('article_list.txt'), 'a+')

    if hash not in f.read().split():
        is_new = True
        f.write(hash + '\n')
        print('new article found')
    f.close()
    return is_new


def getLink(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    print('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('span.date')
    if raw_date:
        return raw_date[0].text.strip()

    print('date not found, update select() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('div.post-meta > h3 > a')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    print(url)
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='post-container')
    if content:
        return content.text
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
    for url in full_urls:
        for n in range(num_pages_to_check):
            r = session.get(url + str(n+1), timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')
            articles += soup.find_all('div', class_='main-item')
    return articles


def main():
    num_pages_to_check = 1
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
            date = getDate(x)
            hash = makeHash(title, date)

            if isArticleNew(hash):
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
