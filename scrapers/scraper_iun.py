import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import re
import sys

"""
    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'IUN'
firstRunBool = False
num_pages_to_check = 2
base_url = 'https://www.iun.si'
full_url = 'https://www.iun.si/publikacije/?page='
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}

def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def date_finder(raw_text):
    dates = []
    for k,v in meseci.items():
        raw_text = raw_text.replace(k,v)
    dates.append(re.search(r'\d{2}.\d{2}.\d{4}', raw_text))
    dates.append(re.search(r'\d{1}.\d{2}.\d{4}', raw_text))
    dates.append(re.search(r'\d{2}.\d{1}.\d{4}', raw_text))
    dates.append(re.search(r'\d{1}.\d{1}.\d{4}', raw_text))
    dates.append(re.search(r'\d{2}.\d{2} \d{4}', raw_text))
    dates.append(re.search(r'\d{1}.\d{2} \d{4}', raw_text))
    dates.append(re.search(r'\d{2}.\d{1} \d{4}', raw_text))
    dates.append(re.search(r'\d{1}.\d{1} \d{4}', raw_text))
    for date in dates:
        if date:
            return date.group()
    return '1.1.1111'


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def get_title(soup):
    title = soup.find('div', class_='title').find('a')
    if title:
        return title.text.strip()
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('div', class_='datestamp')
    if raw_date:
        date = date_finder(raw_date.text.replace(' ', '')) #od prvega space-a naprej
        return formatDate(date)
    print('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='iun_article').find('div', class_='content')
    if content:
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    i = 0
    n = 0
    while i < num_pages_to_check:
        r = session.get(full_url + str(n + 1), timeout=8)
        soup = bs(r.text, 'html.parser')
        articles += soup.find_all('div', class_='col-xl-4 col-lg-4 col-md-4 col-sm-6 col-xs-12')
        if firstRunBool and n < 100:
            n += 1
            if not soup.find('nav', class_='pagination').find('a', class_='next page-numbers'):
                print('found last page\n')
                break
        else:
            i += 1
            n += 1 
    return articles


def formatDate(date):
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
            date = get_date(x)
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