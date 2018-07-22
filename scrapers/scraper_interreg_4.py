import requests
from bs4 import BeautifulSoup as bs
import hashlib
from multiprocessing import Pool
import time

TIMEOUT = 8
PAGES_TO_CHECK = 2
base_url = "http://www.interreg-danube.eu"
full_url = "http://www.interreg-danube.eu/news-and-events/project-news?page=" #kasneje dodas se stevilko strani
session = requests.Session()
headers = {'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/53.0.2785.143 Safari/537.36'}
session.headers.update(headers)

def getArticleList():
	try:
		f = open(('article_list.txt'), 'r+')
	except FileNotFoundError:
		f = open(('article_list.txt'), 'w+')
	return f

def makeHash(title, date):
	return hashlib.sha1((title + date).encode('utf-8')).hexdigest()

def getTitle(soup):
	#return in compact form(use join and split methods)
	title = soup.select('header > h5')
	if title:
		return ' '.join(title[0].text.split())

	print('Title not found, update select() method!')
	return 'Title not found'	

def getDate(soup):
	#return date in form: dd.mm.yyyy
	raw_date = soup.select('header > small')
	if raw_date:
		return raw_date[0].text[2:].replace('-', '.')

	print('Date not found, update select() method')
	return 'Date not found'

def getUrl(soup):
	link = soup.select('div > a')
	if link:
		return (base_url + link[0]['href'])

	print('Link to article not found, update select() method!')
	return None

def getContent(url):
	article_soup = bs(session.get(url, timeout=TIMEOUT).text, 'html.parser')
	content = article_soup.select('div.texts > div.texts')
	if content:
		return ' '.join(content[0].text.split())

	print('Content not found, update select() method!')
	return 'content not found'
	
def makeNewFile(url, title, date, content, hash_code):
	with open(hash_code + '.txt', 'w+', encoding='utf-8') as info_file:
		info_file.write(url + '\n' + title +'\n' + date + '\n' + content)		
	
def find_new_articles(hashes):
	f = getArticleList() #file with hashes of scraped articles
	article_list = f.read().split() 
	ind = [hashes.index(x) for x in hashes if x not in article_list]
	f.close()
	return ind

def getArticlesOnPage(url, session):
	num_newArticles = 0
	r = session.get(url, timeout=TIMEOUT)
	soup = bs(r.text, "html.parser")
	soup_articleS = soup.find('ul', class_='big-list').find_all('li')

	
	titles = [getTitle(x) for x in soup_articleS]
	dates = [getDate(x) for x in soup_articleS]
	hashes = [makeHash(x,y) for (x,y) in zip(titles, dates)]
	ind = find_new_articles(hashes) #index of every new articles


	if not ind:
		return 0

	new_links = [getUrl(soup_articleS[i]) for i in ind]

	with Pool(10) as p:
		new_contents = p.map(getContent, new_links)

	for i in range(len(ind)):
		makeNewFile(new_links[i], titles[ind[i]], new_contents[i], dates[ind[i]], hashes[ind[i]])

	#vrne stevilo novih clankov
	return len(new_links)

def main():
	num_new_articles = 0
	
	for n in range(PAGES_TO_CHECK):
		num_new_articles += getArticlesOnPage(full_url + str(n + 1), session)

	print(num_new_articles, 'new articles found on', PAGES_TO_CHECK, 'pages')

if __name__ == '__main__':
	start = time.time()
	main()
	end = time.time()
	print(end - start)