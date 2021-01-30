import re
import requests
import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from urllib.parse import urlparse, urldefrag, urlsplit, urlunsplit, urljoin
from bs4 import BeautifulSoup
from utils import get_logger

import time

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}

BLACKLISTED_URLS = {
    'https://today.uci.edu/department/information_computer_sciences/calendar',
    'https://wics.ics.uci.edu/events/',
    'https://wics.ics.uci.edu/a/language.php',
    'https://wics.ics.uci.edu/language.php',
    'https://wics.ics.uci.edu/recover/initiate',
    'https://ngs.ics.uci.edu/blog/page',
    'https://ngs.ics.uci.edu/category',
    'https://ngs.ics.uci.edu/tag/',
    'https://ngs.ics.uci.edu/author/',
    'https://isg.ics.uci.edu/events',
    'https://www.ics.uci.edu/publications',
    'https://www.ics.uci.edu/?',
    'https://www.ics.uci.edu?',
    'https://www.informatics.uci.edu/page',
    'https://www.cs.uci.edu/events',
    'https://www.informatics.uci.edu/very-top-footer-menu-items/news/page',
    'https://cbcl.ics.uci.edu/wgEncodeBroadHistone'
}

REMOVE_QUERY = {
    'https://swiki.ics.uci.edu/doku.php',
    'https://evoke.ics.uci.edu/',
    'https://grape.ics.uci.edu/',
    'https://wics.ics.uci.edu/',
    'https://www.ics.uci.edu/doku.php',
    'https://intranet.ics.uci.edu/doku.php',
    'https://cbcl.ics.uci.edu/doku.php'
}

logger = get_logger("SCRAPER")

def tokenizer(text):
    nltk.data.path.append('./nltk_data/')

    retokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    tokens = retokenizer.tokenize(text)

    print("Raw words:", tokens, "\n")

    lm = WordNetLemmatizer()
    tokens = [lm.lemmatize(w, pos="v") for w in tokens]

    print("Word roots:", tokens, "\n")

    print("WAITING NOW")
    time.sleep(20)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    link_list = filter_links(links)

    return link_list

def filter_links(links):
    link_list = []
    # return [link for link in links if is_valid(link)]
    for link in links:
        if is_valid(link):
            added_link = link
            for rq in REMOVE_QUERY:
                if rq in link and '?' in link:
                    added_link = link[:link.find('?')]
                    logger.info(f'Got {added_link} from {link}')
            link_list.append(added_link)

    return link_list

def extract_next_links(url, resp):
    next_link = []
    try:
        if 200 <= resp.status <= 399:
            parsed = urlparse(url)
            host = "https://" + parsed.netloc

            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
            print(soup.prettify())
            for link in soup.findAll('a'):
                try:
                    # constructing absolute URLs, avoiding duplicate contents 
                    l = urljoin(host, link['href'])
                    next_link.append(urldefrag(l)[0])
        
                # href attribute does not exist in <a> tag.
                except KeyError:
                    print("Status Code:", resp.status, "\nError Message: href attribute does not exist.")
        else:
            print("Status Code:", resp.status, " is not between 200 - 399")
    
    # Checks for restricted page.
    except AttributeError:
        print("Status Code:", resp.status, "\nError Message:", resp.error)

    return next_link

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid_domain = False
        for domain in VALID_URLS:
            if domain in parsed.netloc:
                if 'today.uci.edu' in parsed.netloc and '/department/information_computer_sciences' == parsed.path[:41]:
                        valid_domain = True
                else:
                    valid_domain = True

        if valid_domain == False:
            return False
        
        for bl in BLACKLISTED_URLS:
            if bl in url:
                return False

        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpg|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bam|sam"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.query.lower()):
            return False


        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpg|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bam|sam"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise

if __name__ == '__main__':
    # tokenizer("this isn't a word what about mother-in-law but this uses the punctuations like , and . !@#$%^&*()-= and.also")
    # tokenizer('fly flew flown, eat eaten, have has had, go goes gone going went')
    # tokenizer('is am are was were been being')
    tokenizer('fish fishes book books church churches')