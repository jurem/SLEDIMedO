from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor

'''

'''

SOURCE = 'ZDRUZENJE-OBCIN'

base_url = 'http://www.zdruzenjeobcin.si/'
full_url = 'http://www.zdruzenjeobcin.si/novice/arhiv/stran/' #kasneje dodas se stevilko strani (0 je prva)
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True

def getLink(soup):
    link = soup.select('h5 > a')
    if link:
        return base_url + link[0]['href']
    print('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('span', class_='news-list-date')
    if date:
        return date.text
    print('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('h5 > a')
    if title:
        return ' '.join(title[0].text.split())
    print('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    print(url)

    r = session.get(url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div', class_='news-single-item')
    if content:
        return ' '.join(content.text.split())
    print('content not found, update select() method', url)
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    return '-'.join(reversed(date.split('.')))


def getArticlesOnPage(num_pages_to_check, session):
    articles = []

    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n), timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find_all('div', class_='news-list-item')
        articles = articles + articles_on_page
    return articles


def main():
    num_pages_to_check = 1
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_pages_to_check, session)

        dates = []
        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash = makeHash(title, date)

            if is_article_new(hash):
                titles.append(title)
                dates.append(date)
                hashes.append(hash)
                links.append(getLink(x))
                num_new_articles += 1

        new_articles_tuples = []
        for i in range(len(links)):
            content = getContent(links[i], session)
            tup = (str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], base_url)
            new_articles_tuples.append(tup)

        dbExecutor.insertMany(new_articles_tuples)

    print(num_new_articles, 'new articles found,', num_pages_to_check, 'pages checked')



if __name__ == '__main__':
    main()