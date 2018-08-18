from bs4 import BeautifulSoup
import requests
import hashlib
import re
from database.dbExecutor import dbExecutor

'''
    ps, vse novice se crpajo iz ene strani
'''

SOURCE = 'OBCINA-MARIBOR'

base_url = 'http://www.maribor.si/'
full_url = 'http://www.maribor.si/podrocje.aspx?id=291'
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()


def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    print('new article found')
    return True

def getLink(soup):
    link = soup.find('a', class_='povezava')
    if link:
        link = link.get('href')
        if re.search(base_url, link):
            return link
        return base_url + link
    print('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('span', class_='DatumVstavljanja1')
    if date:
        return date.text
    print('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.find('a', class_='povezava')
    if title:
        return title.text
    print('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = session.get(url, timeout=5)
    print(r.status_code)
    soup = BeautifulSoup(r.text, 'lxml')
    content = soup.find('div', id='vsebina')
    if content:
        return content.text
    print('content not found, update select() method', url)
    return 'content not found'


def makeNewFile(link, title, date, content, hash):
    with open(hash + '.txt', 'w+', encoding='utf-8') as info_file:
        info_file.write(link + '\n' + title + '\n' + date + '\n' + content)


def getArticlesOnPage(num_articles_to_check, session):
    r = session.get(full_url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')

    articles = soup.find('div', id='vsebina').findChildren(recursive=False)[1].find_all('tr')
    return articles[:num_articles_to_check] #zadnji link odstranimo, ker je link do arhiva novic(zaenkrat ga ne rabimo)


def main():
    num_articles_to_check = 20
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_articles_to_check, session)

        dates = []
        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            date = getDate(x)
            hash = makeHash(title, date)

            if is_article_new(hash):
                titles.append(title)
                dates.append(date)
                hashes.append(hash)
                links.append(getLink(x))
                num_new_articles += 1

        for i in range(len(links)):
            content = ' '.join(getContent(links[i], session).split())
            print(titles[i])
            print(dates[i])
            print(content + '\n\n')
    

    print(num_new_articles, 'new articles found,', num_articles_to_check, 'articles checked')



if __name__ == '__main__':
    main()