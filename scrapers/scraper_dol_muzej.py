import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys

"""
    hash je narejen samo iz naslova

    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'DOL-MUZEJ'
firstRunBool = False
num_pages_to_check = 1
base_url = 'http://www.dolenjskimuzej.si'
full_url = 'http://www.dolenjskimuzej.si/si/muzej/novice/?p='
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}

def make_hash(title):
    return hashlib.sha1((title).encode('utf-8')).hexdigest()

def correct_string(content):
    #popravi nepravilne znake
    return content.replace('Ä', 'č').replace('Å¡', 'š').replace('Å¾', 'ž')


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def get_title(soup):
    title = soup.find('a')
    if title:
        return correct_string(title.text.strip())
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('div', class_='col-lg-12').find('p')
    if raw_date:
        raw_date = raw_date.text
        date = raw_date.split()
        date[1] = meseci[date[1]]
        return ''.join(date)
    print('Date not found, update select() method')
    return '1.1.1111'


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='col-lg-12 col-md-12 col-sm-12')
    if content:
        return correct_string(content.text.strip())
    content = soup.find('div', class_='col-lg-4 col-md-4 col-sm-4')
    if content:
        return correct_string(content.text.strip())
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    n = 0
    i = 0
    while n < num_pages_to_check:
        r = session.get(full_url + str(i + 1), timeout=10)
        soup = bs(r.text, 'html.parser')
        articles += soup.find('div', class_='col-lg-12 col-md-12 col-sm-12').find_all('h3')
        if firstRunBool:
            i += 1
            if soup.find('ul', class_='paging').find_all('li')[-1].a.has_attr('name'):
                print('found last page')
                break
        else:
            n += 1
            i += 1
    return articles


def format_date(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def main():
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = get_articles_on_pages(num_pages_to_check,session)
        articles_checked = len(articles)

        new_articles_tuples = []
        for x in articles:
            title = get_title(x)
            hash_str = make_hash(title)

            if is_article_new(hash_str):
                link = get_link(x)
                r = session.get(link, timeout=8)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                date = get_date(soup)
                print(link + '\n')
                new_tup = (str(datetime.date.today()), title, content, format_date(date), hash_str, link, SOURCE)
                new_articles_tuples.append(new_tup)
                num_new_articles += 1

        #add new articles to database
        dbExecutor.insertMany(new_articles_tuples)
        print(num_new_articles, 'new articles found,', articles_checked,'articles checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()