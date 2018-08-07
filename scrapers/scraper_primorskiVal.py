import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime


base_url = 'http://www.primorskival.si/'
full_url = 'http://www.primorskival.si/snovice.php?page=' #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}


def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash):
    is_new = False
    try:
        f = open('article_list.txt', 'r+')
    except FileNotFoundError:
        f = open('article_list.txt', 'a+')
    if hash not in f.read().split():
        is_new = True
        f.write(hash + '\n')
        print('new article found')
    f.close()
    return is_new


def get_title(soup):
    title = soup.find('h2')
    if title:
        return title.text
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.find('span', class_='datum')
    if raw_date:
        date = raw_date.text
        date = date.split()
        date[2] = meseci[date[2]]
        return formatDate(''.join(date[1:]))
    print('date not found')
    return '1.1.1111' #code for date not found


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.find('div', class_='maincontent')    
    if content:
        for script in content(['script']):
            script.decompose()
        return content.text.strip()
    print('content not found')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n+1))
        soup = bs(r.text, 'html.parser')
        articles += soup.find('div', class_='maincontent').find_all('div', style='float: right; width:470px; padding: 2px;')
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
    main()