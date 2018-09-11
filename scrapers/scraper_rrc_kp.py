from bs4 import BeautifulSoup as bs
import requests
import hashlib
import datetime
from database.dbExecutor import dbExecutor
from tqdm import tqdm
'''
    vse novice so zbrane na eni strani

    NE UPORABLJAJ TEGA SCRAPERJA!

    novice se objavljajo tako redko, da se naenkrat crpa samo 3 clanke, ker imajo samo trije clanki zraven datum(dumb thing to do)

    v prihodnosti se lahko ta scraper po potrebi popravi (ce bodo na strani datumi zraven clankov)
'''

SOURCE = 'RRC-KP'
num_pages_to_check = 3
num_errors = 0
base_url = 'https://www.rrc-kp.si'
full_url = 'https://www.rrc-kp.si/sl/novice.html?start=' #kasneje dodas se od katerega clanka naprej gledas
headers = {
    'user-agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 '
        'Safari/537.36'}

def makeHash(title, date):
    return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def find_last_page(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'html.parser')
    num = soup.find('div', class_='t1 fright').find_all('a')[-1].get('href').split('/')[-1]
    return int(num)

def log_error(text):
    global num_errors
    num_errors += 1
    log_file = open('error_log_zakelj.log', 'a+')
    log_file.write(str(datetime.datetime.today()) + '\n')
    log_file.write('scraper_rrc_kp.py' + '\n')
    log_file.write(text + '\n\n')
    log_file.close()

def get_connection(url, session):
    try:
        r = session.get(url, timeout=10)
        return r
    except requests.exceptions.MissingSchema:
        log_error('invalid url: ' + url)
        return session.get(url)

def is_article_new(hash_str):
    if dbExecutor.getByHash(hash_str):
        return False
    return True

def getLink(soup):
    link = soup.select('h4 > a')
    if link:
        return link[0]['href']
    log_error('link not found, update find() method')
    return 'link not found'


def getDate(soup):
    date = soup.find('time')
    if date:
        return ''.join(date.text.split())
    log_error('date not found, update find() method')
    return 'date not found'


def getTitle(soup):
    title = soup.select('h4 > a')
    if title:
        return ' '.join(title[0].text.split())
    log_error('title not found, update find() method')
    return 'title not found'


def getContent(url, session):
    r = get_connection(url, session)
    soup = bs(r.text, 'lxml')

    #znebi se script texta na strani, da ne bo del content-a
    for script in soup(['script']):
        script.decompose()

    content = soup.find('div', class_='news news-single-item')
    if content:
        return ' '.join(content.text.split())
    log_error('content not found, update select() method' + url)
    return 'content not found'


def formatDate(date):
    #format date for consistent database
    return '-'.join(reversed(date.split('.')))


def getArticlesOnPage(num_pages_to_check, session):
    articles = []

    print('\tgathering articles ...')
    for n in range(num_pages_to_check):
        r = get_connection(full_url + str(n*10*2),session)
        soup = bs(r.text, 'lxml')
        articles += soup.find('div', class_='cat-items').find_all('td')
    return articles


def main():
    print('====================')
    print('scraper_rrc_kp.py')
    print('====================')
    
    num_new_articles = 0

    with requests.Session() as session:
        session.headers.update(headers)
        articles = getArticlesOnPage(num_pages_to_check, session)

        print('\tgathering article info ...')
        for x in tqdm(articles):
            title = getTitle(x)
            date = getDate(x)
            hash_str = makeHash(title, date)

            if is_article_new(hash_str):
                link = getLink(x)
                content = getContent(link, session)
                tup = (str(datetime.date.today()), title, content, formatDate(date), hash_str, link, SOURCE)
                num_new_articles += 1
                dbExecutor.insertOne(tup)
    print(num_new_articles, 'new articles found,', num_pages_to_check, 'pages checked')



if __name__ == '__main__':
    main()