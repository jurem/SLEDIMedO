from bs4 import BeautifulSoup
import requests
import hashlib

'''
    vse novice so zbrane na eni strani

    za dostop do datuma je potrebno odpreti link do clanka - hash_code je sestavljen samo iz naslova
'''


base_url = 'https://siol.net'
full_url = 'https://siol.net/novice'
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title):
    return hashlib.sha1((title).encode('utf-8')).hexdigest()


def isArticleNew(hash_code):
    is_new = False
    try:
        f = open('article_list.txt', 'r+')
    except FileNotFoundError:
        f = open('article_list.txt', 'a+')

    if hash_code not in f.read().split():
        is_new = True
        f.write(hash_code + '\n')
        print('new article found')
    f.close()
    return is_new

def getLink(soup):
    link = soup.find('a')
    if link:
        return base_url + link.get('href')
    print('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('span', class_='article__publish_date--date')
    if date:
        return ''.join(date.text.split()).strip(';')
    print('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.find('a').get('title')
    if title:
        return title
    print('title not found, update find() method')
    return 'title not found'


def getContent(soup):
    
    content = soup.find('div', class_='article__body--content js_articleBodyContent')
    if content:
        return ' '.join(content.text.split())
    print('content not found, update select() method')
    return 'content not found'


def makeNewFile(link, title, date, content, hash_code):
    with open(hash_code + '.txt', 'w+', encoding='utf-8') as info_file:
        info_file.write(link + '\n' + title + '\n' + date + '\n' + content)


def getArticlesOnPage(num_articles_to_check, session):
    r = session.get(full_url, timeout=5)
    soup = BeautifulSoup(r.text, 'lxml')

    articles = soup.find_all('article')
    return articles[1:num_articles_to_check]


def main():
    num_articles_to_check = 20
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_articles_to_check, session)

        titles = []
        hashes = []
        links = []

        for x in articles:
            title = getTitle(x)
            hash_code = makeHash(title)

            if isArticleNew(hash_code):
                titles.append(title)
                hashes.append(hash_code)
                links.append(getLink(x))
                num_new_articles += 1

        for i in range(len(links)):
            #tukaj popravi, da vneses v bazo

            #this soup will be used for content and date
            r = session.get(links[i], timeout=5)
            soup = BeautifulSoup(r.text, 'lxml')

            content = getContent(soup)
            date = getDate(soup)

            print(links[i])
            print(titles[i])
            print(date)
            print(content + '\n\n')
    

    print(num_new_articles, 'new articles found,', num_articles_to_check, 'articles checked')



if __name__ == '__main__':
    main()