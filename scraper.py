import re
import ssl
import os
import json

import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup
from utils import get_logger
from constants import VALID_URLS, BLACKLISTED_URLS, REMOVE_QUERY


scraper_logger = get_logger("SCRAPER")
crawler_logger = get_logger("CRAWLER")


def scraper(url, resp):
    """
    Scrapes URL from the given webpage retrieved from the frontier.
    Apply filter to the scraped URL and sends back to the frontier.
    The webpage is also scraped for contents: words, domain, and subdomain.
    Writes report of the gathered information after each scrape
    """
    # Extract all the links in the webpage
    links = extract_next_links(url, resp)
    # Filter the links with query and trailing slashes
    link_list = filter_links(links)

    # Only scrape information if the webpage returns
    # a status code within 200 to 399.
    if 200 <= resp.status <= 399:
        get_link_dict(link_list)
        scrape_words(url, resp)

    return link_list


def extract_next_links(url, resp):
    """
    Takes a webpage retrieved from the frontier and 
    gathers all of the links in the page. Return the list of 
    the extracted links.
    """
    # Creating an empty list to store urls 
    next_link = []
    try:
        # Check if the input url is valid (status between 200-399)
        # If not valid, ignore the input url and return empty list
        if 200 <= resp.status <= 399:
            # Prepare the input url to construct absolute URLs 
            parsed = urlparse(url)
            host = "https://" + parsed.netloc

            # Extract data from HTML 
            soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
            # Find all urls within the input url 
            for link in soup.findAll('a'):
                try:
                    # constructing absolute URLs from relative URLs and 
                    # add the absolute URLs without the fragment part to next_link list
                    l = urljoin(host, link['href'])
                    next_link.append(urldefrag(l)[0])

                # href attribute does not exist in <a> tag.
                except KeyError:
                    print("Status Code:", resp.status,
                          "\nError Message: href attribute does not exist.")
        else:
            # url is invalid
            print("Status Code:", resp.status, " is not between 200 - 399")

    # Checks for restricted page.
    except AttributeError:
        print("Status Code:", resp.status, "\nError Message:", resp.error)

    return next_link


def filter_links(links):
    """
    Filters links.
    """
    link_list = []
    for link in links:
        if is_valid(link):
            added_link = link

            # Filter queries that lead to same website.
            for rq in REMOVE_QUERY:
                if rq in link and '?' in link:
                    added_link = link[:link.find('?')]
                    scraper_logger.info(f'Got {added_link} from {link}')

            # Filter links with no trailing slash after
            # domain name.
            parsed_url = urlparse(link)
            if parsed_url.path == '':
                added_link += '/'

            link_list.append(added_link)

    return link_list


def is_valid(url):
    """
    Checks if the URL given is a valid URL to crawl.
    This function also checks for web traps through a blacklist
    """
    try:
        parsed = urlparse(url)

        # Check if the input url has http or https
        # If not, returns False
        if parsed.scheme not in set(["http", "https"]):
            return False

        # Check if the input url witthin the valid domain set
        valid_url = False
        for domain in VALID_URLS:
            if domain in parsed.netloc:
                if 'today.uci.edu' in parsed.netloc and '/department/information_computer_sciences' == parsed.path[:41]:
                    valid_url = True
                else:
                    valid_url = True

        if valid_url == False:
            return False

        # Check if the input url is in the Blacklisted url set
        # If yes, returns false 
        for bl in BLACKLISTED_URLS:
            if bl in url:
                return False

        # Check for the input url query that ends with one of these tags 
        if re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpg|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bam|sam"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|odc|scm"
            + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.query.lower()):
            return False

        # Check for the input url path that ends with one of these tags 
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpg|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bam|sam"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|odc|scm"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


def set_up_ssl():
    """
    Sets up connection for NLTK library download.
    """
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


def download_nltk_library():
    """
    Download NLTK libraray.
    Wordnet: Word map that checks for plural / root words
    Stopwords: Default conventional English stop words list
    """
    # Set path for nltk library.
    nltk.data.path.append('./nltk_data/')

    if not os.path.exists('./nltk_data/corpora'):
        # Set up ssl for nltk library download.
        set_up_ssl()
        # Download wordnet from nltk library.
        nltk.download('wordnet', download_dir='./nltk_data/')
        # Download stopwords from nltk library.
        nltk.download('stopwords', download_dir='./nltk_data/')


def tokenize(text):
    """
    Takes a string of text and tokenize it using NLTK library.
    """
    # Regex tokenizer. Checks for alphanumeric characters.
    re_tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    re_tokens = re_tokenizer.tokenize(text.lower())

    # Lemmatizer. Checks for word roots words.
    # Includes root words of verbes, and plural forms.
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(w, pos="v") for w in re_tokens]

    return tokens


def scrape_words(url, resp):
    """
    Parse text inside a webpage. Gather information and store
    in a JSON formatted file for future analysis.
    """
    try:
        # Read the current state of json file and load it to word_dict
        with open('word_dict.json', 'r') as json_file:
            word_dict = json.load(json_file)
        # If the file is empty, set word_dict to an empty dict
    except json.decoder.JSONDecodeError:
        word_dict = {
            'counter': {
                'URL_with_most_words': {},
                '50_most_common_words': {}
            },
            'URL_list': {},
            'word_list': {}
        }

    download_nltk_library()

    try:
        # Open the URL and parse text in the page.
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        text = soup.text

        token_list = tokenize(text)
        stopword_list = stopwords.words('english')
        token_list_without_stopwords = [
            token for token in token_list if token not in stopword_list]

        # Add URL to URL_list with number of words in it
        word_dict['URL_list'][url] = len(token_list)

        try:
            # Find out current most number of words in a website
            current_number_of_words = list(
                word_dict['counter']['URL_with_most_words'].values())[0]
            # If the new website has greater number of words
            # replace the URL_with_most_words of words
            if len(token_list) > current_number_of_words:
                word_dict['counter']['URL_with_most_words'] = {}
                word_dict['counter']['URL_with_most_words'][url] = len(
                    token_list)

            # If the URL_with_most_words is empty, add the new website information
        except IndexError:
            word_dict['counter']['URL_with_most_words'][url] = len(token_list)

        # Populate the word list dictionary
        for token in token_list_without_stopwords:
            # If the word is not in the dictionary, make an entry
            # and set its frequency to 1
            if token not in word_dict['word_list']:
                word_dict['word_list'][token] = 1

            # If the word is already in the dictionary, increment its frequency by 1
            else:
                word_dict['word_list'][token] += 1

        # Dump the python dictionary to JSON format and save for future use
        with open('word_dict.json', 'w') as json_file:
            json.dump(word_dict, json_file)

    except AttributeError:
        print("Status Code: ", resp.status, "\nError Message:", resp.error)


def get_link_dict(link_list):
    """
    Gathers information about domains and subdomains from URL that's given from the frontier.
    Saves information to JSON file format for future uses.
    """
    # Open link_dict.json file
    # Check for empty file Error
    try:
        with open('link_dict.json', 'r') as json_file:
            link_dict = json.load(json_file)
    except json.decoder.JSONDecodeError:
        link_dict = {
            'counter': {
                'total_unique_pages': 0,
                'ics.uci.edu_subdomains': {}
            }
        }

    # For every link in a page, parse the URL and count domains and subdomains
    for link in link_list:
        parsed_url = urlparse(link)

        domain = parsed_url.netloc.split('.', 1)[1]
        subdomain = parsed_url.netloc.split('.', 1)[0]
        path = parsed_url.path

        subdomain_found = False

        # If domain is not in the dictionary
        # Add it along its subdomain and path
        if domain not in link_dict:
            link_dict[domain] = [{subdomain: [path]}]
            # Increment unique page count
            link_dict['counter']['total_unique_pages'] += 1

            # Increment ics.uc.edu subdomain count
            if domain == 'ics.uci.edu':
                link_dict['counter']['ics.uci.edu_subdomains'][subdomain] = 1

        # If the domain is in the dictionary
        else:
            # Check whether subdomain is in the dictionary
            for nested_dict in link_dict[domain]:
                if subdomain in nested_dict:
                    subdomain_found = True

            # If subdomain is not in the dictionary
            # Add the subdomain and its path
            if not subdomain_found:
                link_dict[domain].append({subdomain: [path]})
                # Increment unique page count
                link_dict['counter']['total_unique_pages'] += 1

                # Increment ics.uc.edu subdomain count
                if domain == 'ics.uci.edu':
                    link_dict['counter']['ics.uci.edu_subdomains'][subdomain] = 1

            # If subdomain is in the dictionary
            else:
                for sub in link_dict[domain]:
                    # Check if path is in the dictionary
                    # If it does not, add to the dictionary
                    # to avoid redundancy.
                    if subdomain in sub:
                        if path not in sub[subdomain]:
                            sub[subdomain].append(path)
                            # Increment unique page count
                            link_dict['counter']['total_unique_pages'] += 1

                            # Increment ics.uc.edu subdomain count
                            if domain == 'ics.uci.edu':
                                link_dict['counter']['ics.uci.edu_subdomains'][subdomain] += 1

    with open('link_dict.json', 'w') as json_file:
        json.dump(link_dict, json_file)


def reset_json_files():
    """
    When the crawler starts, JSON files will be cleared.
    """
    link_dict = {
        'counter': {
            'total_unique_pages': 0,
            'ics.uci.edu_subdomains': {}
        }
    }

    word_dict = {
        'counter': {
            'URL_with_most_words': {},
            '50_most_common_words': {}
        },
        'URL_list': {},
        'word_list': {}
    }

    with open('link_dict.json', 'w') as json_file:
        json.dump(link_dict, json_file)

    with open('word_dict.json', 'w') as json_file:
        json.dump(word_dict, json_file)


# Clears JSON files
reset_json_files()
