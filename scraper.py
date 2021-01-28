import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import lxml

from utils import get_logger

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    next_link = []
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for link in soup.findAll('a'):
            try:
                next_link.append(link['href'])
    
            # href attribute does not exist in <a> tag.
            except KeyError:
                print("Status Code:", resp.status, "\nError Message: href attribute does not exist.")
    
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

        # Check Domain : url needs to be in the Valid url set
        for domain in VALID_URLS:
            if domain in parsed.netloc:
                if parsed.netloc == 'today.uci.edu' and parsed.path[:41] == '/department/information_computer_sciences':
                    valid_domain = True
                else:
                    valid_domain = False

        if valid_domain == False:
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise