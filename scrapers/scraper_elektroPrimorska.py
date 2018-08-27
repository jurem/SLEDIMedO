import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys

"""
    created by markzakelj
"""

SOURCE = 'ELEKTRO-PRIMORSKA'
firstRunBool = False

base_url = 'http://www.elektro-primorska.si'
full_url = 'http://www.elektro-primorska.si/novice?page=' #dodaj se stevilo strani - prva stran je 0
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.select('h2 > span > a')
    if title:
        return title[0].text.strip()
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('span', class_='field-content')
    if raw_date:
        date = raw_date.text
        date = date[:date.find(' ')]
        return formatDate(date)
    print('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='field field-name-body field-type-text-with-summary field-label-hidden')
    if content:
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n))
        soup = bs(r.text, 'html.parser')
        articles += soup.find_all('div', class_='masonry-item')
    return articles


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def main():
    num_pages_to_check = 2
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
                r = requests.get(link)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                print(link + '\n')
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, base_url)
                new_articles_tuples.append(new_tup)
                num_new_articles += 1

        #add new articles to database
        dbExecutor.insertMany(new_articles_tuples)
        print(num_new_articles, 'new articles found,', articles_checked,'articles checked')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()