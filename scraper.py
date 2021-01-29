import re
from urllib.parse import urlparse, urldefrag, urlsplit, urlunsplit, urljoin
from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}
BLACKLISTED_URLS = {
    'https://today.uci.edu/department/information_computer_sciences/calendar',
    'https://wics.ics.uci.edu/events/',
    'https://evoke.ics.uci.edu/hollowing-i-in-the-authorship-of-letters-a-note-on-flusser-and-surveillance/?',
    'https://evoke.ics.uci.edu/qs-personal-data-landscapes-poster/?',
    'https://swiki.ics.uci.edu/doku.php/start?',
    # 'https://swiki.ics.uci.edu/doku.php/hardware:laptops?',
    'https://swiki.ics.uci.edu/doku.php',
    'https://wics.ics.uci.edu/a/language.php',
    'https://wics.ics.uci.edu/language.php',
    'https://wics.ics.uci.edu/recover/initiate',
    'https://ngs.ics.uci.edu/blog/page',
    'https://ngs.ics.uci.edu/category',
    }

def scraper(url, resp):
    links = extract_next_links(url, resp)



    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    next_link = []
    try:

        # Check if url status is withing 200 - 399
        if 200 <= resp.status <= 399:
            parsed = urlparse(url)
            host = "https://" + parsed.netloc

            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
            for link in soup.findAll('a'):
                try:
                    # transform relative into absolute URLs, avoiding duplicate contents 
                    l = urljoin(host, link['href'])
                    next_link.append(urldefrag(l)[0])
        
                # href attribute does not exist in <a> tag.
                except KeyError:
                    print("Status Code:", resp.status, "\nError Message: href attribute does not exist.")
    
    # Checks for restricted page.
    except AttributeError:
        print("Status Code:", resp.status, "\nError Message:", resp.error)

    return next_link

def is_valid(url):
    try:
        # Check Scheme : url needs to start with http or https
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check Domain : url needs to be in the Valid url set
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

        # # Check Path : filter out urls that don't point to webpage 
        # for path in INVALID_PATH:
        #     if path in parsed.path:
        #         return False
            # print(parsed.path.lower())

        for bl in BLACKLISTED_URLS:
            if bl in url:
                return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|ppsx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
