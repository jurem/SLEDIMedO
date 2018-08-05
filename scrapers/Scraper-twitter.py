# -*- coding: utf-8 -*-

import bs4 as bs
import requests
import sys
import time
import datetime
import hashlib
import re
from database.dbExecutor import dbExecutor

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

driver = webdriver.Chrome() 
# driver.set_window_position(-10000,0)    # "hides" the browser
driver.implicitly_wait(15)

ACCOUNT_NAMES = [
                ["hashtag/GeoZS?src=hash", "hashtag/DriDanube?src=hash",
                "hashtag/EcoKarst?src=hash", "hashtag/rralur?src=hash"],
                ["agrigo4cities", "Interreg_Danube", "attractdanubesi", "interreg_danube",
                "Chestnut_EU", "crowd_stream", "danu_bioval", "EcoInnDanube", "ReSTI_project",
                "foresda_eu_dtp", "InnoHPC", "INSiGHTS_Danube", "ironagedanube", "made_in_danube",
                "moveco_interreg", "networldproject", "project_senses", "smartfactoryhub",
                "transdanubep", "LjTehnoloski", "ZrcSazu", "MO_Velenje", "urbaninstitut",
                "statslovenija", "mzi_rs", "ulfggljubljana", "skupnost_obcin", "ZRSBistra",
                "SrceSlovenije", "poligonsi", "CEDSlovenia", "RAZUMsi", "visitidrija", "mizs_rs",
                "Skupnost_obcin", "112_sos", "zrcsazu", "mddszRS", "notranjskipark", "planinskazveza",
                "KSSENA_VELENJE", "MIZS_RS", "GZSnovice", "FFLjubljana", "ZVKDS", "dolenjskimuzej",
                "turizemslovenia", "gzsnovice", "poklicno", "bsckranjsi", "univerzam", "zvkds",
                "FundacijaPRIZMA", "obcinaruse", "PomurjeTP", "pomurjer", "mra_po"]]

SOURCE_ID = "TWITTER"          # source identifier
NUM_JUMPS_TO_END_TO_MAKE = 400 # how many pages will we check on first run - get every page
BASE_URL = "https://twitter.com"
DEBUG = True

firstRunBool = False           # import all the articles that exist if true; overrides NUM_JUMPS_TO_END_TO_MAKE

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
    tweetsSaved = 0

    sqlBase = dbExecutor()  # creates a sql database handler class
    todayDateStr = datetime.datetime.now().strftime("%Y-%m-%d") # today date in the uniform format
    yearInt = datetime.datetime.now().year
    errorList = list()

    numJumpsToMake = NUM_JUMPS_TO_END_TO_MAKE
    if not firstRunBool:
        numJumpsToMake = 2

    for pageId, pageType in enumerate(ACCOUNT_NAMES):
        for accountName in pageType:
            try:
                sourceId = SOURCE_ID+"-"+accountName.upper()    # field "SOURCE" in the database
                if "hashtag/" in accountName[:9]:
                    sourceId = SOURCE_ID+"-#"+accountName[8:-9].upper()    # field "SOURCE" in the database
                    # print (sourceId)

                print("Scraping for:", accountName)
                link = BASE_URL+"/"+accountName
                driver.get(link)

                # scroll to the end of page numJumpsToMake times
                scrollHeightBefore = 0
                scrollHeightNow = 0
                numTimesHeightEqual = 0
                for jump in range(1, numJumpsToMake+1):
                    elem = driver.find_element_by_tag_name('a')
                    elem.send_keys(Keys.END)
                    print (str(jump)+"/"+str(numJumpsToMake), "jumps to the end of the page completed.")

                    # if the scroll height is not changed for 3 consecutive times
                    # that means that there are not any more tweets to load
                    scrollHeightNow = int(driver.execute_script("return document.body.scrollHeight"))
                    if (scrollHeightBefore == scrollHeightNow):
                        numTimesHeightEqual += 1
                        if numTimesHeightEqual >= 3:
                            print ("All tweets loaded or so it seams.")
                            break
                    scrollHeightBefore = scrollHeightNow
                    time.sleep(2)

                # print (driver.page_source.encode("utf-8"))
                time.sleep(3)

                # pageId part is a coincidence
                soup = bs.BeautifulSoup(driver.find_elements_by_tag_name('ol')[pageId].get_attribute('innerHTML'),'html.parser')

                for tweet in extractTweetTags(soup):
                    title = tweet.find("span", class_="FullNameGroup").text
                    description = tweet.find("div", class_="js-tweet-text-container").text
                    link = BASE_URL+tweet.find("small", class_="time").find("a")["href"]

                    timeStamp = tweet.find("small", class_="time").find("a").find("span")["data-time-ms"]
                    date_created = datetime.datetime.fromtimestamp(int(timeStamp)/1000).strftime('%Y-%m-%d')
                    hashStr = makeHash(title, date_created)

                    date_downloaded = todayDateStr  # date when the article was downloaded
                    
                    # print ("CONTENT:", description)
                    # print ("TITLE:", title)
                    # print ("URL:", link)
                    # print ("DATE:", dateStr)
                    
                    tweetsDownloaded += 1

                    # printBool = False
                    # if article is not yet saved in the database we add it
                    if sqlBase.getByHash(hashStr) is None:
                        # (date_created: string, caption: string, contents: string, date: string, hash: string, url: string, source: string)
                        entry = (date_created, title, description, date_downloaded, hashStr, link, sourceId)
                        sqlBase.insertOne(entry, True)   # insert the article in the database
                        tweetsSaved += 1
                        # printBool = True

                    if DEBUG and tweetsDownloaded % 10 == 0 and tweetsDownloaded != 0:
                        print ("Downloaded:", tweetsDownloaded, " tweets. Saved:", tweetsSaved, "new tweets.")
            except Exception as e:
                print (e)
                errorList.append(e)
                errorList.append(("Downloaded:", tweetsDownloaded, " tweets. Saved:", tweetsSaved, "new tweets."))
            # finally:
            #     if driver:
            #         driver.quit()

    print ("Downloaded:", tweetsDownloaded, "new tweets.")
    driver.quit()
    print ("ERROR LIST:", errorList)

if __name__ == '__main__':
    # checks if the second argument is provided and is equal to "-F" - means first run
    if len(sys.argv) == 2:
        if sys.argv[1] == "-F":
            firstRunBool = True
        else:
            firstRunBool = False

    print ("Add -F as the command line argument to execute first run\ncommand - downloads the whole history of articles from the page.\nWARNING: -F option will take a lot of time\n")

    main()