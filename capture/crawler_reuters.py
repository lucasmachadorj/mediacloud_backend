import logging
import pymongo
import settings
import requests

from goose import Goose
from bs4 import BeautifulSoup
from logging.handlers import RotatingFileHandler


logger = logging.getLogger("Reuters")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('/tmp/mediacloud_reuters.log',
                          maxBytes=5e6,
                          backupCount=3)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to stream_handler
stream_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add stream_handler to logger
logger.addHandler(stream_handler)  # uncomment for console output of messages
logger.addHandler(file_handler)


client = pymongo.MongoClient(settings.MONGOHOST, 27017)
mcdb = client.MCDB
ARTICLES = mcdb.articles
ARTICLES.ensure_index("source")

CATEGORIES = {u'mundo': u'worldNews', u'negocios': u'businessNews', u'esportes': u'sportsNews', u'cultura': u'entertainmentNews',u'brasil': u'domesticNews', u'internet': u'internetNews'}


def find_article(category):

    if category not in CATEGORIES:
        raise ValueError("Category value not accepted.")
    INDEX_URL = "http://br.reuters.com/news/archive/{0}?date=today".format(CATEGORIES[category])

    index = requests.get(INDEX_URL).content
    soup = BeautifulSoup(index)
    news_index = soup.find("div", {"class": "module"})
    urls = [a['href'] for a in news_index.findAll("a")]
    news_urls = ["http://br.reuters.com{0}".format(url) for url in urls]
    return news_urls

if __name__ ==  "__main__":
    find_article(u'mundo')