import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys
from tqdm import tqdm

"""
    firstRunBool used - working

    created by markzakelj
"""

SOURCE = 'NOVA-GORICA'
firstRunBool = False
num_pages_to_check = 2
base_url = 'https://www.nova-gorica.si'
full_urls = ['https://www.nova-gorica.si/sporocila-za-javnost/2008022610252747_2011092214234718/pub/30/',
             'https://www.nova-gorica.si/zadnje-objave/2010011815383155_20080904135365_2008022610223363_2011062815421202_20080904165101_20080904135935_2010033008272522_20080904151623_2008022610243144_20080904135919_20080904145875_2008072211315459_2008022610244772_2009121809310937_20080904161168_2008022610250196_2008072211342397_2008022610251440_20080904155591_20080904133711_2011120115055388_2011120115055388_20080904133711/pub/30/']
             #dodaj se stevilo strani - prva stran je 1

#full_urls = ['https://www.primorske.si/primorska/istra?page='] use this variable when testing - it's faster ;)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def correct_string(content):
    #popravi nepravilne znake
    return content.replace('Ä', 'č').replace('Å¡', 'š').replace('Å¾', 'ž').strip()

def log_error(text):
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_novaGorica.py' + '\n')
    log_file.write(text + '\n\n')
    log_file.close()

def get_connection(url, session):
    try:
        r = session.get(url, timeout=10)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(url)

def find_last_page(session, url):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    num = soup.find('table', id='gids-paging').find_all('td')[-2].find('a').text.strip()
    return int(num)

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True


def get_title(soup):
    title = soup.find('a')
    if title:
        return correct_string(title.text)
    log_error('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    date = soup.find('td')
    if date:
        return formatDate(date.text)
    log_error('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    log_error('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', id='article-body')
    if content:
        return correct_string(content.text)
    log_error('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    for url in full_urls:
        if firstRunBool:
            num_pages_to_check = find_last_page(session, url)
        print('\tgathering articles ...')
        for n in tqdm(range(num_pages_to_check)):
            r = get_connection(url + str(n + 1), session)
            soup = bs(r.text, 'html.parser')
            articles += soup.find('table', id='gids-list').find_all('tr')[1:] #prvega spusti, ker ni clanek
    return articles


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def main():

    print('=====================')
    print('scraper_novaGorica.py')
    print('=====================')
    
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)

        articles = get_articles_on_pages(num_pages_to_check,session)
        articles_checked = len(articles)

        new_articles_tuples = []
        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = get_title(x)
            date = get_date(x)
            hash_str = make_hash(title, date)

            if is_article_new(hash_str):
                link = get_link(x)
                r = get_connection(link, session)
                soup = bs(r.text, 'html.parser')
                content = get_content(soup)
                new_tup = (str(datetime.date.today()), title, content, date, hash_str, link, SOURCE)
                new_articles_tuples.append(new_tup)
                num_new_articles += 1

        #add new articles to database
        dbExecutor.insertMany(new_articles_tuples)
        print(num_new_articles, 'new articles found,', articles_checked,'articles checked\n')


if __name__ == '__main__':
    if len(sys.argv) == 2 and sys.argv[1] == "-F":
        firstRunBool = True
    main()