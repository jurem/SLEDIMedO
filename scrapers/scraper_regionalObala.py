from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys
''' 
    created by markzakelj
'''

SOURCE = 'REGIONAL-OBALA'
firstRunBool = False

base_url = 'http://www.regionalobala.si'
full_urls = ['http://www.regionalobala.si/obalne-zgodbe/',
             'http://www.regionalobala.si/vesti/',
             'http://www.regionalobala.si/trendi/',
             'http://www.regionalobala.si/zanimivo'] 
             #kasneje dodas se stevilo strani (1, 2, ...)

headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def makeHash(title):
    return hashlib.sha1((title).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def getLink(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.find('div', class_='newsDate')
    if raw_date:
        date = raw_date.text
        return date[:date.find(' ')] #odrezi pri prvem presledku - .text je oblike 'dd.mm.yyyy ob hh:mm'

    print('date not found, update select() method')
    return 'date not found'


def getTitle(soup):
    title = soup.find('a')
    if title:
        return title.text
    print('title not found, update select() method')
    return 'title not found'


def getContent(soup):

    #odstrani vse 'script' elemente, da se ne pojavijo v 'content'
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='p1 block_news no-min-height')
    if content:
        return ' '.join(content.text.split())
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
            articles += soup.find_all('div', class_='w2 h2 x1 y1 block ')
            articles += soup.find_all('div', class_='grid_4 block_news_small block_news_style')
    return articles


def main():
    num_pages_to_check = 1
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_pages_to_check, session)
        articles_checked = len(articles)

        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            
            hash_str = makeHash(title)

            if is_article_new(hash_str):
                titles.append(title)
                hashes.append(hash_str)
                links.append(getLink(x))
                num_new_articles += 1

        list_of_tuples = []
        for i in range(len(links)):
            print(links[i])
            r = session.get(links[i], timeout=10)
            soup = BeautifulSoup(r.text, 'html.parser')

            content = getContent(soup)
            date = getDate(soup)
            
            tup = (str(datetime.date.today()), titles[i], content, formatDate(date), hashes[i], links[i], SOURCE)
            list_of_tuples.append(tup)

        dbExecutor.insertMany(list_of_tuples)

    print(num_new_articles, 'new articles found,', num_pages_to_check,'pages checked -', articles_checked, 'articles checked')

if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
