import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys

"""
    vse novice so zbrane na eni strani
    
    created by markzakelj
"""

SOURCE = 'E3'
firstRunBool = False
base_url = 'https://www.e3.si'
full_url = 'https://www.e3.si/o-nas/novice/'
             #dodaj se stevilo strani - prva stran je 0
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def get_title(soup):
    title = soup.find('h2')
    if title:
        return title.text.strip()
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('span', class_='date')
    if raw_date:
        raw_date = raw_date.text
        date = raw_date[raw_date.find(' ') + 1:].split()
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
    content = soup.find('div', class_='site-main-content')
    if content:
        content.find('div', class_='main-breadcrumb').decompose()
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(session):
    articles = []
    r = session.get(full_url, timeout=10)
    soup = bs(r.text, 'lxml')
    articles += soup.find('div', class_='site-main-content').find_all('div', class_='content-max-with')
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

        articles = get_articles_on_pages(session)
        articles_checked = len(articles)

        new_articles_tuples = []
        for x in articles:
            title = get_title(x)
            date = format_date(get_date(x))
            hash_str = make_hash(title, date)

            if is_article_new(hash_str):
                link = get_link(x)
                r = session.get(link, timeout=8)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                print(link + '\n')
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                new_articles_tuples.append(new_tup)
                num_new_articles += 1

        #add new articles to database
        dbExecutor.insertMany(new_articles_tuples)
        print(num_new_articles, 'new articles found,', articles_checked,'articles checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()
