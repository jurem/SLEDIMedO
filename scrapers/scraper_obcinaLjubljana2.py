from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
import sys


''' 
    scraper je uporaben za vec projektov

    ta scraper crpa iz strani "ostale novice", obstaja se drug scraper,
    ki crpa iz strani "aktualno"
    
    na tem url-ju so clanki zbrani na samo eni strani!

    nekateri clanki ne vodijo do nove strani, ampak te vodijo na osnovno stran - content not found

    created by markzakelj
'''
SOURCE = 'OBCINA-LJUBLJANA'
firstRunBool = False

base_url = 'https://www.ljubljana.si'
full_url = 'https://www.ljubljana.si/sl/aktualno/ostale-novice-2/'
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
    link = soup.select('div > h2 > a')
    if link:
        return base_url + link[0]['href']
    print('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('div > a > img > span')
    if raw_date:
        return raw_date[0].text.replace(' ', '')
    raw_date2 = soup.select('div > a > span')
    if raw_date2:
        return raw_date2[0].text.replace(' ', '')

    print('date not found, update select() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('div > h2 > a')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='lag-wrapper')
    if content:
        text = content.text
        return text    
    print('content not found, update select() method or get content from excerpt')
    return None


def formatDate(date):
    #format date for consistent database
    return '-'.join(reversed(date.split('.')))


def getArticlesOn_n_pages(num_articles_to_check, session):
    r = session.get(full_url)
    soup = BeautifulSoup(r.text, 'html.parser')
    article = soup.find('ul', class_='list-big-blocks').find('li')
    articles = [article]
    for n in range(1, num_articles_to_check):
        articles.append(articles[n - 1].find_next_sibling())
    return articles


def main():
    num_articles_to_check = 20
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOn_n_pages(num_articles_to_check, session)

        new_articles_tuples = []

        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                if not content:
                    content = x.find('p').text
                num_new_articles += 1
                new_articles_tuples.append((str(datetime.date.today()), title, content, formatDate(date), hash_str, link, base_url))
    
    dbExecutor.insertMany(new_articles_tuples)
    print(num_new_articles, 'new articles found,', num_articles_to_check, 'articles checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
