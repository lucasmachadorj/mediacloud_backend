import re
import logging
import pymongo
import settings
import requests

from datetime import datetime

from goose import Goose
from bs4 import BeautifulSoup
from downloader import compress_content, detect_language
from logging.handlers import RotatingFileHandler


logger = logging.getLogger("Reuters")
logger.setLevel(logging.DEBUG)

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.DEBUG)
file_handler = RotatingFileHandler('/tmp/mediacloud_reuters.log',
                                   maxBytes=5e6,
                                   backupCount=3)

formatter = logging.Formatter('%(asctime)s - %(name)s -\
                              %(levelname)s - %(message)s')

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

CATEGORIES = {u'mundo': u'worldNews', u'negocios': u'businessNews',
              u'esportes': u'sportsNews', u'cultura': u'entertainmentNews',
              u'brasil': u'domesticNews', u'internet': u'internetNews'}


def find_articles(category, date):

    if category not in CATEGORIES:
        raise ValueError("Category value not accepted.")
    INDEX_URL = "http://br.reuters.com/news/archive/{0}?date={1}".format(CATEGORIES[category], date)

    index = requests.get(INDEX_URL).content
    soup = BeautifulSoup(index)
    news_index = soup.find("div", {"class": "module"})
    urls = [a['href'] for a in news_index.findAll("a")]
    news_urls = ["http://br.reuters.com{0}".format(url) for url in urls]
    return news_urls


def extract_title(article):

    try:
        title = article.title
    except Exception as ex:
        template = "An exception of type {0} occured during extraction of news\
                    title. Arguments:\n{1!r}"
        message = template.format(type(ex).__name__, ex.args)
        logger.exception(message)
        return None
    if title is None:
        logger.error("The news title is None")
    return title


def extract_published_time(soup):
    MONTHS = {u"janeiro": u"Jan", u"fevereiro": u"Fev", u"mar\xe7o": u"Mar",
              u"abril": u"Apr", u"maio": u"May", u"junho": u"Jun", u"julho":
              u"Jul", u"agosto": u"Aug", u"setembro": u"Sep", u"outubro":
              u"Oct", u"novembro": u"Nov", u"dezembro": u"Dec"}
    time_tag = soup.find("div", {"class": "timestampHeader"}).text
    time_pattern = re.compile("(.*), (\d{1,2}) de (.*) de (\d{4}) (.*) BRT")
    groups = time_pattern.search(time_tag).groups()
    day, month, year, time = [groups[i] for i in range(1, 5)]
    date_str = "{0} {1} {2} {3}".format(day, MONTHS[month], year, time)
    date = datetime.strptime(date_str, '%d %b %Y %H:%M')
    return date


def extract_content(article):

        try:
            body_content = article.cleaned_text
        except Exception as ex:
            template = "An exception of type {0} occured during extraction of news\
                        content. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            logger.exception(message)
            return None
        if body_content is None:
            logger.error("The news content is None")
        return body_content


def download_article(url):

    article = {'link': url, 'source': 'crawler_reuters'}
    logger.info("Downloading article: {0}".format(url))

    try:
        response = requests.get(url, timeout=30)
    except Exception as ex:
        logger.exception("Failed to fetch {0} due to exception {1}".format(url,
                         type(ex).__name__))
        return None

    extractor = Goose({'use_meta_language': False, 'target_language': 'pt'})
    news = extractor.extract(url=url)
    soup = BeautifulSoup(response.content)

    article['link_content'] = compress_content(response.text)
    article['compressed'] = True
    article['language'] = detect_language(response.text)
    article['title'] = extract_title(news)
    article['published_time'] = extract_published_time(soup)
    article['body_content'] = extract_content(news)

    return article
