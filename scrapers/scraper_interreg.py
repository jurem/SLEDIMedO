from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
import hashlib

'''
	ta scraper je uporaben za vse projekte
'''

URL = "http://www.interreg-danube.eu"
NUM_PAGES_TO_CHECK = 2

def makeHash(title, date):
	return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def getUrl(article):
	link = article.find('a', class_='btn btn-block').get('href')
	return(URL + link)

def getTitle(soup):
	return soup.find('h1').find('h1').text

def getDate(soup):
	raw_date = soup.find('h1').find('h6').text
	return raw_date.replace('-', '.')

def getContent(soup):
	text_field = soup.find('div', class_='texts').find('div', class_='texts').text
	return text_field

def is_article_new(hash_code):
	try:
		f = open(('article_list.txt'), 'r+')
	except FileNotFoundError:
		f = open(('article_list.txt'), 'w+')

	if hash_code not in f.read().split():
		f.write(hash_code + '\n')
		return True
	return False

def update_database(title, date, content, hash_code, url):
	with open((hash_code + '.txt'), 'w+', encoding='utf-8') as f:
		f.write(url + '\n' + title + '\n' + content + '\n' + date)

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

	soup = bs(urlopen(URL + '/news-and-events/project-news?page=' + str(page_num+1)), "html.parser")
	soup_articleS = soup.find('ul', class_='big-list').find_all('li')

	for x in soup_articleS:
		num_newArticles += getArticleInfo(x)

	return num_newArticles
		



def main():

	num_all_new_articles = 0
	
	for n in range(NUM_PAGES_TO_CHECK):
		num_all_new_articles +=	getArticlesOnPage(n)

	print(num_all_new_articles, 'new articles found, first', NUM_PAGES_TO_CHECK, 'pages checked')


if __name__ == '__main__':
	main()