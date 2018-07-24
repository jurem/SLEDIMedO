from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import urllib.parse
import hashlib

'''
    ta scraper je uporaben za 3SMART projekt
'''

NUM_OF_PAGES_TO_CHECK = 1

URL = "https://www.e3.si"

meseci = {'januar': '1.', 'februar': '2.', 'marec': '3.', 'april': '4.', 'maj': '5.',
          'junij': '6.', 'julij': '7.', 'avgust': '8.', 'september': '9.',
          'oktober': '10.', 'november': '11.', 'december': '12.'}


def makeHash(title, date):
    return hashlib.sha1((title + date).encode("utf-8")).hexdigest()


def getUrl(next_article):
    # vrne url novice (ce link vsebuje non-ascii characters, bo funkcija quote to popravila)
    link = next_article.find("a", href=True).get("href")
    return URL + urllib.parse.quote(link)


def getDate(article_page):
    # oblika: "nedelja, 10. junij 2018"
    # popravi, dobi ven stevilski datum
    raw_date = article_page.find("span", class_="newsDate").text

    parts = raw_date.split(" ")
    parts[2] = meseci[parts[2]]  # zamenjaj ime meseca z stevilom
    parts.pop(0)  # odstrani ime dneva
    return ''.join(parts)


def getTitle(article_page):
    # vrne naslov novice
    return article_page.find("h1").text


def getContent(article_page):
    # vrne vsebino novice
    main_content = article_page.find("div", class_="site-main-content")
    text = [p.text for p in main_content.find_all("p")]
    return "\n".join(text)


def update_database(title, date, content, hash_code, url):
    with open((hash_code + '.txt'), 'w+', encoding='utf-8') as f:
        f.write(url + '\n' + title + '\n' + content + '\n' + date)


def is_article_new(hash_code):
    # preveri, ce je clanek ze bil "crpan
    try:
        f = open(('article_list.txt'), 'r+')
    except FileNotFoundError:
        f = open(('article_list.txt'), 'w+')

    if hash_code not in f.read().split():
        f.write(hash_code + '\n')
        return True
    return False


def getArticleInfo(article_excerpt):
    url = getUrl(article_excerpt)
    soup = bs(urlopen(url), 'html.parser')

    title = getTitle(soup)
    date = getDate(soup)
    content = getContent(soup)
    hash_code = makeHash(title, date)

    if is_article_new(hash_code):
        update_database(title, date, content, hash_code, url)
        print('new article', hash_code, ' added to database')
        return True
    print('article', hash_code, 'already in database')
    return False


def getArticlesOnPage(page_num):
    num_newArticles = 0

    soup = bs(urlopen(URL + '/o-nas/novice/'), "html.parser")
    soup_articleS = soup.find_all('div', class_='content-max-with')

    for x in soup_articleS:
        num_newArticles += getArticleInfo(x)

    return num_newArticles


def main():
    """
        vse novice so zbrane na eni strani,
        crpanje iz vecih strani ni potrebno
    """
    num_newArticles = getArticlesOnPage(NUM_OF_PAGES_TO_CHECK)

    print(num_newArticles, 'new articles found, 1 page checked')


if __name__ == '__main__':
    main()
