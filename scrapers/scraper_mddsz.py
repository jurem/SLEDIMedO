from bs4 import BeautifulSoup
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor

'''
    vse novice so zbrane na eni strani
'''

SOURCE = 'MDDSZ'

base_url = 'http://www.mddsz.gov.si'
full_url = 'http://www.mddsz.gov.si/si/medijsko_sredisce/sporocila_za_medije/page/' #kasneje dodas se cifro strani
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
    link = soup.select('h4 > a')
    if link:
        return link[0]['href']
    print('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('time')
    if date:
        return ''.join(date.text.split())
    print('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('h4 > a')
    if title:
        return ' '.join(title[0].text.split())
    print('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    print(url)

    r = session.get(url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')

    #znebi se script texta na strani, da ne bo del content-a
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='news news-single-item')
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
        r = session.get(full_url + str(n+1), timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        articles_on_page = soup.find('div', class_='news').find_all('table')
        articles = articles + articles_on_page
    return articles


def main():
    num_pages_to_check = 3
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
            #tukaj popravi, da vneses v bazo
            content = ' '.join(getContent(links[i], session).split())
            tup = (str(datetime.date.today()), titles[i], content, formatDate(dates[i]), hashes[i], links[i], base_url)
            new_articles_tuples.append(tup)

        dbExecutor.insertMany(new_articles_tuples)

    print(num_new_articles, 'new articles found,', num_pages_to_check, 'pages checked')



if __name__ == '__main__':
    main()