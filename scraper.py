import re
from urllib.parse import urlparse, urldefrag, urlsplit, urlunsplit, urljoin
from bs4 import BeautifulSoup
import lxml
import requests
from simhash import Simhash

from utils import get_logger

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
    'https://isg.ics.uci.edu/events'
}

REMOVE_QUERY = {
    'https://swiki.ics.uci.edu/doku.php/',
    'https://evoke.ics.uci.edu/',
    'https://grape.ics.uci.edu/',
    'https://wics.ics.uci.edu/',
    'https://www.ics.uci.edu/doku.php/start'
}

logger = get_logger("SCRAPER")

def scraper(url, resp):
    links = extract_next_links(url, resp)
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
                if 'today.uci.edu' in parsed.netloc:
                    if '/department/information_computer_sciences' == parsed.path[:41]:
                        valid_domain = True
                else:
                    valid_domain = True
        if valid_domain == False:
            return False
        
        for bl in BLACKLISTED_URLS:
            if bl in url:
                return False
            

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|z|zip)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise