import bs4 as bs
import requests
import re
import hashlib
import os.path

DEBUG = True
BASE_URL = "http://www.rralur.si"
	
def makeHash(articleTitle, dateStr):
	hash_object = hashlib.sha1(str(articleTitle)+str(dateStr))
	return hash_object.hexdigest()

def parseDate(toParse):
	regexStr = "\\s+?(\\d{2}\\.\\s\\d{2}\\.\\s\\d{4}).*?"
	result = re.search(regexStr, toParse, re.M|re.U|re.I)
	if result is None:
		if DEBUG: print (("Date not specified/page is different"))
		return None
	return result.group(1)

def parseLink(toParse):
	regexStr = "=\\s'(.*?)'"
	result = re.search(regexStr, toParse, re.M|re.U|re.I)
	if result is None:
		if DEBUG: print (("Page is different"))
		return None
	return BASE_URL+result.group(1)

def parseTitle(toParse):
	regexStr = "^\\s+(.*?)\\s+$"
	result = re.search(regexStr, toParse, re.M|re.U|re.I)
	if result is None:
		if DEBUG: print ("Page is different")
		return None
	return result.group(1)

# navigates to the given link and extracts the article description
def getArticleDescr(session, link):
	resp = session.get(link)
	soup = bs.BeautifulSoup(resp.text, "html.parser")
	return soup.find("div", class_="field-item even").text


def main():
	listOfPages = list()	# contains all info about articles [title, link, dateStr]
	articlesChecked = 0

	with requests.Session() as s:
		pageStart = 0
		resp = s.get(BASE_URL+"/sl/news")
		soup = bs.BeautifulSoup(resp.text, "html.parser")

		# print (resp.text)
		# find all ~15 articles on current page
		articles = soup.find_all("div", class_="grid-item")

		for article in articles:
			articlesChecked += 1


			title = parseTitle(article.find("h3", class_="title").text)
			print title
			link = parseLink(article["onclick"])
			print link

			dateStr = parseDate(article.find("div", class_="news-date").text)
			print dateStr
			hashStr = makeHash(title.encode("utf-8"), dateStr.encode("utf-8"))


			# if file does not yet exitst or filesize is == 0 we create it
			if not os.path.isfile(hashStr+".txt") or os.path.isfile(hashStr+".txt") and os.stat(hashStr+".txt").st_size == 0:
				description = getArticleDescr(s, link)


				# print (title)
				# print (link)
				# print (dateStr)
				# print (hashStr )
				listOfPages.append([title, description, link, dateStr, hashStr])

				#print (title+"\n"+link+"\n"+description+"\n"+dateStr+"\n")
				with open(hashStr+".txt", "w") as f:
					f.write((link+"\n"+title+"\n"+description+"\n"+dateStr+"\n").encode("utf-8"))

				# TODO: upload data to the database (sqlite)

			if DEBUG and articlesChecked % 5 == 0:
				print ("Checked:", articlesChecked, "articles.")



	print ("NOVI CLANKI:")
	for article in listOfPages:
		print (article)

if __name__ == '__main__':
	main()