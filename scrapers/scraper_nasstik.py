import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
from tqdm import tqdm
import re
import sys

"""
    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'NASSTIK'
firstRunBool = False
num_pages_to_check = 5
base_url = 'http://www.nas-stik.si'
full_url = 'http://www.nas-stik.si/1/Novice/tabid/67/lapg-254/'
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def find_last_page(session):
    r = session.get(full_url)
    soup = bs(r.text, 'html.parser')
    link = soup.find('table', class_='PagingTable').find_all('a')[-1].get('href').replace('/Default.aspx', '')
    num = re.search(r'\d+$', link).group()
    return int(num)

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.find('a')
    if title:
        return title.text.strip()
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('span', class_='Datum')
    if raw_date:
        return formatDate(raw_date.text.replace(' ', ''))
    print('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='NovicaVsebina')
    if content:
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    if firstRunBool:
        num_pages_to_check = find_last_page(session)
    print('gathering articles')
    for n in tqdm(range(num_pages_to_check)):
        r = session.get(full_url + str(n + 1), timeout=8)
        soup = bs(r.text, 'html.parser')
        articles += soup.find_all('div', class_='NoviceVstopna grey')
    return articles


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def main():

    print('===================')
    print('scraper_nasstik.py')
    print('===================')
    
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = get_articles_on_pages(num_pages_to_check,session)
        articles_checked = len(articles)

        print('gathering article info')
        new_articles_tuples = []
        for x in tqdm(articles):
            title = get_title(x)
            date = get_date(x)
            hash_str = make_hash(title, date)

            if is_article_new(hash_str):
                link = get_link(x)
                r = session.get(link, timeout=8)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                new_articles_tuples.append(new_tup)
                num_new_articles += 1

        #add new articles to database
        dbExecutor.insertMany(new_articles_tuples)
        print('\n', num_new_articles, 'new articles found,', articles_checked,'articles checked\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()