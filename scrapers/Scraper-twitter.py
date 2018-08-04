# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import sys
import time
import datetime
import hashlib
from database.dbExecutor import dbExecutor

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

driver = webdriver.Chrome() 
driver.set_window_position(-10000,0)    # hides the browser
driver.implicitly_wait(15)

ACCOUNT_NAMES = ["LjTehnoloski", "ZrcSazu", "MO_Velenje", "urbaninstitut",
                "statslovenija", "mzi_rs", "ulfggljubljana", "MO_Velenje",
                "skupnost_obcin", "ZRSBistra", "SrceSlovenije", "poligonsi",
                "CEDSlovenia", "SrceSlovenije", "RAZUMsi", "visitidrija",
                "mizs_rs", "mzi_rs", "Skupnost_obcin", "112_sos", "zrcsazu",
                "mddszRS", "notranjskipark", "planinskazveza", "KSSENA_VELENJE",
                "MIZS_RS", "MO_Velenje", "GZSnovice", "SrceSlovenije",
                "FFLjubljana", "ZVKDS", "dolenjskimuzej", "turizemslovenia",
                "gzsnovice", "poklicno", "bsckranjsi", "mzi_rs", "univerzam",
                "gzsnovice", "turizemslovenia", "zrcsazu", "zvkds",
                "FundacijaPRIZMA", "univerzam", "obcinaruse", "bsckranjsi",
                "PomurjeTP", "pomurjer", "mzi_rs", "mra_po"]

SOURCE_ID = "TWITTER"        # source identifier
NUM_JUMPS_TO_END_TO_MAKE = 50 # how many pages will we check evey day for new articles
BASE_URL = "https://twitter.com"
DEBUG = True

firstRunBool = False         # import all the articles that exist if true; overrides NUM_JUMPS_TO_END_TO_MAKE

# makes a sha1 hash out of title and date strings
# returns string hash
def makeHash(articleTitle, dateStr):
    hash_object = hashlib.sha1((articleTitle+dateStr).encode("utf-8"))
    return hash_object.hexdigest()

def extractTweetTags(soup):
    rez = list()
    for tag in soup.find_all('li'):
        # print (tag.encode("utf-8"))
        if 'data-item-type' in tag.attrs and tag.attrs['data-item-type'] == 'tweet':
            rez.append(tag.find("div", class_="content"))
    return rez

def main():
    tweetsDownloaded = 0  # number of downloaded articles

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format
    yearInt = datetime.datetime.now().year

    numJumpsToMake = NUM_JUMPS_TO_END_TO_MAKE
    if not firstRunBool:
        numJumpsToMake = 2
    
    for accountName in ACCOUNT_NAMES:
        sourceId = SOURCE_ID+"-"+accountName.upper()    # field "SOURCE" in the database

        print("Scraping for:", accountName)
        link = BASE_URL+"/"+accountName
        driver.get(link)

        # scroll to the end of page numJumpsToMake times
        for jump in range(1, numJumpsToMake+1):
            elem = driver.find_element_by_tag_name('a')
            elem.send_keys(Keys.END)
            print (str(jump)+"/"+str(numJumpsToMake), "jumps to the end of the page completed.")
            time.sleep(2)

        # print (driver.page_source.encode("utf-8"))

        soup = bs.BeautifulSoup(driver.find_elements_by_tag_name('ol')[1].get_attribute('innerHTML'),'html.parser')

        for tweet in extractTweetTags(soup):
            title = tweet.find("span", class_="FullNameGroup").text
            description = tweet.find("div", class_="js-tweet-text-container").text
            link = BASE_URL+tweet.find("small", class_="time").find("a")["href"]

            timeStamp = tweet.find("small", class_="time").find("a").find("span")["data-time-ms"]
            date_created = datetime.datetime.fromtimestamp(int(timeStamp)/1000).strftime('%Y-%m-%d')
            hashStr = makeHash(title, date_created)

            date_downloaded = todayDateStr  # date when the article was downloaded
            
            # print("CONTENT:", description)
            # print ("TITLE:", title)
            # print ("URL:", link)
            # print ("DATE:", dateStr)

            # if article is not yet saved in the database we add it
            if sqlBase.getByHash(hashStr) is None:
                # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                entry = (date_created, title, description, date_downloaded, hashStr, link, sourceId)
                sqlBase.insertOne(entry)   # insert the article in the database
                tweetsDownloaded += 1

                if DEBUG and tweetsDownloaded % 5 == 0 and tweetsDownloaded != 0:
                    print ("Downloaded:", tweetsDownloaded, "new tweets.")

    print ("Downloaded:", tweetsDownloaded, "new tweets.")
    driver.quit()

if __name__ == '__main__':
    main()