from bs4 import BeautifulSoup
import requests
import hashlib
''' 
    scraper je uporaben za vec projektov
    
    ta scraper crpa iz strani "aktualno", obstaja se drug scraper,
    ki crpa iz strani "ostale novice"
'''

base_url = 'https://www.ljubljana.si'
full_url = 'https://www.ljubljana.si/sl/aktualno/?start=' #kasneje dodas se stevilo zacetka (10, 20, ...)
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}

def makeHash(title, date):
    return hashlib.sha1((title+date).encode('utf-8')).hexdigest()

def isArticleNew(hash):
    is_new = False
    try:
        f = open(('article_list.txt'), 'r+')
    except FileNotFoundError:
        f = open(('article_list.txt'), 'a+')

    if hash not in f.read().split():
        is_new = True
        f.write(hash + '\n')
        print('new article found')
    f.close()
    return is_new

def getLink(soup):
    link = soup.select('div > h2 > a')
    if link:
        return base_url + link[0]['href']
    print('link not found, update select() method')
    return 'link not found'


def getDate(soup):
    raw_date = soup.select('div > a > img > span')
    if raw_date:
        return raw_date[0].text.replace(' ', '')
    raw_date2 = soup.select('div > a > span')
    if raw_date2:
        return raw_date2[0].text.replace(' ', '')

    print('date not found, update select() method')
    return 'date not found'

def getTitle(soup):
    title = soup.select('div > h2 > a')
    if title:
        return title[0].text
    print('title not found, update select() method')
    return 'title not found'

def getContent(url, session):
    r = session.get(url, timeout=10)
    soup = BeautifulSoup(r.text, 'html.parser')

    content = soup.find('div', class_='lag-wrapper')
    if content:
        text = content.text
        return text
    print('content not found, update select() method')
    return 'content not found'

def makeNewFile(link, title, date, content, hash):
    with open(hash + '.txt', 'w+', encoding='utf-8') as info_file:
        info_file.write(link + '\n' + title + '\n' + date + '\n' + content)

def getArticlesOn_n_pages(num_pages_to_check, session):

    articles = []

    for n in range(num_pages_to_check):
        r = session.get(full_url + str(n * 10))
        soup = BeautifulSoup(r.text, 'html.parser')
        articles_on_page = soup.find('ul', class_='list-big-blocks').find_all('li')
        articles = articles + articles_on_page

    return articles

def main():
    num_pages_to_check = 1
    num_new_articles = 0
    articles_checked = 0

    with requests.Session() as session:
        session.headers.update(headers)
        r = session.get(full_url + str(0), timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        articles = getArticlesOn_n_pages(num_pages_to_check, session)
        articles_checked = len(articles)

        dates = []
        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash = makeHash(title, date)

            if isArticleNew(hash):
                titles.append(title)
                dates.append(date)
                hashes.append(hash)
                links.append(getLink(x))
                num_new_articles += 1

        for i in range(len(links)):
            content = getContent(links[i], session)
            makeNewFile(links[i], titles[i], dates[i], content, hashes[i])

    print(num_new_articles, 'new articles found,', num_pages_to_check,'pages checked -', articles_checked, 'articles checked')

if __name__ == '__main__':
    main()
