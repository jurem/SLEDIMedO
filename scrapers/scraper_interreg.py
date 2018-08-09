import requests
from bs4 import BeautifulSoup as bs
import hashlib
from database.dbExecutor import dbExecutor
import datetime
import sys

SOURCE = 'INTERREG'
base_url = 'http://www.interreg-danube.eu'
full_url = 'http://www.interreg-danube.eu/news-and-events/project-news?page='
             #dodaj se stevilo strani - prva stran je 1
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

firstRunBool = False

def make_hash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True


def get_title(soup):
    title = soup.select('header > h5')
    if title:
        return ' '.join(title[0].text.split())
    print('title not found, update select() method')
    return 'title not found'


def get_date(soup):
    raw_date = soup.select('header > small')
    if raw_date:
        return formatDate(raw_date[0].text[2:].replace('-', '.'))
    print('Date not found, update select() method')
    return '1.1.1111'


def get_link(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found')
    return base_url #return base url to avoid exceptions


def get_content(soup):
    content = soup.select('div.texts > div.texts')
    if content:
        return content[0].text.strip()
    print('content not found, update select() method')
    return 'content not found'


def get_articles_on_pages(num_pages_to_check, session):
    articles = []
    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n+1), timeout=10)
        soup = bs(r.text, 'lxml')
        articles_on_page = soup.find('ul', class_='big-list').find_all('li')
        articles = articles + articles_on_page
    return articles


def getMaxPageNum(session):
    r = session.get(full_url+"1", timeout=10)
    maxPageNum = bs(r.text, 'lxml').find("nav", class_="pagination").find_all("li")[-2].find("a").text
    return int(maxPageNum)


def formatDate(date):
    #format date for consistent database
    date = date.split('.')
    for i in range(2):
        if len(date[i]) == 1:
            date[i] = '0'+date[i]
    return '-'.join(reversed(date))


def main():
    num_pages_to_check = 1
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)
        
        if firstRunBool:
            maxPageNum = getMaxPageNum(session)
            print ("Checking {} pages".format(maxPageNum))
            num_pages_to_check = maxPageNum

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