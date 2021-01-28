import re
from urllib.parse import urlparse, urldefrag
from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}
INVALID_PATH = {'pdf', 'ppt', 'css', 'js'}

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    next_link = []

    if 200 <= resp.status <= 599:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for link in soup.find_all('a'):
            l = link.get('href')
            if l != '#' and is_valid(l):
                # print(l)

                # Check for web error message : for debug purposes 
                # try:
                #     response = requests.get(l)

                #     # If the response was successful, no Exception will be raised
                #     response.raise_for_status()
                # except HTTPError as http_err:
                #     print(f'HTTP error occurred: {http_err}')  # Python 3.6
                # except Exception as err:
                #     print(f'Other error occurred: {err}')  # Python 3.6
                #     print(url)
                # else:
                #     print('Success!')

                # Only append unique url : strip url fragment 
                next_link.append(urldefrag(l)[0])
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

        # Check Path : filter out urls that don't point to webpage 
        for path in INVALID_PATH:
            if path in parsed.path:
                return False
            # print(parsed.path.lower())

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
