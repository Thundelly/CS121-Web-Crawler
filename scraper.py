import re
from urllib.parse import urlparse, urldefrag, urlsplit, urlunsplit, urljoin
from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    next_link = []
    try:

        # Check if url status is withing 200 - 202 
        # -------------------------------------------------------------------------------------------------------
        # 200 = OK - request has succeeded
        # 201 = Created - request has been fulfilled and resulted in a new resource being created
        # 202 = Accepted - request has been accepted for processing, but the processing has not been completed
        # -------------------------------------------------------------------------------------------------------
        if 200 <= resp.status <= 202 and check_traps(url):
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
    
    # Checks for restricted page.
    except AttributeError:
        print("Status Code:", resp.status, "\nError Message:", resp.error)

    return next_link

def check_traps(url):
    parsed = urlparse(url)

    # Blacklist
    if parsed.netloc == "today.uci.edu":
        return False

    if parsed.netloc == "wics.ics.uci.edu":
        return False
    
    if parsed.netloc == "evoke.ics.uci.edu":
        return False

    return True

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
