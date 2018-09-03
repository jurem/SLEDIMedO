import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys

"""
    firstRunBool used, working

    created by markzakelj
"""

SOURCE = 'AGEN-RS'
firstRunBool = False
num_pages_to_check = 2
base_url = 'https://www.agen-rs.si'
full_url = 'https://www.agen-rs.si/novice?p_p_id=101_INSTANCE_CQYGQHgtBrli&p_p_lifecycle=0&p_p_state=normal&p_p_mode=view&p_p_col_id=column-1&p_p_col_count=1&_101_INSTANCE_CQYGQHgtBrli_delta=20&_101_INSTANCE_CQYGQHgtBrli_keywords=&_101_INSTANCE_CQYGQHgtBrli_advancedSearch=false&_101_INSTANCE_CQYGQHgtBrli_andOperator=true&p_r_p_564233524_resetCur=false&_101_INSTANCE_CQYGQHgtBrli_cur='
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def get_title(soup):
    title = soup.find('a')
    if title:
        return title.text.strip()
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('span', class_='date pull-left')
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
    content = soup.find('div', class_='col-xlg-9 col-lg-8 col-md-12')
    if content:
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    n = 0
    i = 0
    while n < num_pages_to_check:
        r = session.get(full_url + str(i+1), timeout=8)
        soup = bs(r.text, 'html.parser')
        articles += soup.find_all('div', class_='col-xlg-6 col-lg-12')
        if firstRunBool:
            i += 1
            if soup.find('ul', class_='pager lfr-pagination-buttons').find_all('li')[2]['class'][0] == 'disabled':
                print('found last page')
                break
        else:
            n += 1
            i += 1

        if i == 100:
            #v izogib neskoncni zanki
            break
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