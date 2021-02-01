import re
import ssl
import os
import json
import pprint
from urllib import parse

import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords

from urllib.parse import urlparse, urldefrag, urljoin
from bs4 import BeautifulSoup
from utils import get_logger
from constants import VALID_URLS, BLACKLISTED_URLS, REMOVE_QUERY

import time
import requests

scraper_logger = get_logger("SCRAPER")
crawler_logger = get_logger("CRAWLER")

def reset_link_dict():
    link_dict = {
        'counter': {
            'total_unique_pages': 0,
            'ics.uci.edu_subdomains': {}
        }
    }

    with open('link_dict.json', 'w') as json_file:
        json.dump(link_dict, json_file)

def scraper(url, resp):
    links = extract_next_links(url, resp)
    link_list = filter_links(links)
    
    get_link_dict(link_list)
    scrape_words(url, resp)
    write_report()

    return link_list

def extract_next_links(url, resp):
    next_link = []
    try:
        if 200 <= resp.status <= 399:
            get_permission(url)
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
                    print("Status Code:", resp.status,
                          "\nError Message: href attribute does not exist.")
        else:
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
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid_url = False
        for domain in VALID_URLS:
            if domain in parsed.netloc:
                if 'today.uci.edu' in parsed.netloc and '/department/information_computer_sciences' == parsed.path[:41]:
                    valid_url = True
                else:
                    valid_url = True

        if valid_url == False:
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
            + r"|epub|dll|cnf|tgz|sha1|odc|scm"
            + r"|thmx|mso|arff|rtf|jar|csv|apk"
                + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.query.lower()):
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpg|mpeg|ram|m4v|mkv|ogg|ogv|pdf|bam|sam"
            + r"|ps|eps|tex|ppt|ppsx|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|odc|scm"
            + r"|thmx|mso|arff|rtf|jar|csv|apk"
            + r"|rm|smil|wmv|swf|wma|war|zip|rar|gz|z|zip)$", parsed.path.lower())

    except TypeError:
        print("TypeError for ", parsed)
        raise


def set_up_ssl():
    try:
        _create_unverified_https_context = ssl._create_unverified_context
    except AttributeError:
        pass
    else:
        ssl._create_default_https_context = _create_unverified_https_context


def download_nltk_library():
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
    # Regex tokenizer. Checks for alphanumeric characters.
    re_tokenizer = RegexpTokenizer('[a-zA-Z0-9]+')
    re_tokens = re_tokenizer.tokenize(text.lower())

    # Lemmatizer. Checks for word roots words.
    # Includes root words of verbes, and plural forms.
    lemmatizer = WordNetLemmatizer()
    tokens = [lemmatizer.lemmatize(w, pos="v") for w in re_tokens]

    return tokens


def scrape_words(url, resp):

    download_nltk_library()

    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        text = soup.text
        
        print(url)
        print(tokenize(text))
        # print(stopwords.words('english'))

        time.sleep(20)


    except AttributeError:
        print("Status Code: ", resp.status, "\nError Message:", resp.error)

def get_link_dict(link_list):
    with open('link_dict.json', 'r') as json_file:
        link_dict = json.load(json_file)

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
            link_dict['counter']['total_unique_pages'] += 1     # Increment unique page count
            
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
                link_dict['counter']['total_unique_pages'] += 1     # Increment unique page count
        
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
                            link_dict['counter']['total_unique_pages'] += 1     # Increment unique page count
                
                            # Increment ics.uc.edu subdomain count
                            if domain == 'ics.uci.edu':
                                link_dict['counter']['ics.uci.edu_subdomains'][subdomain] += 1


    # pp = pprint.PrettyPrinter(indent=2)
    # pp.pprint(link_dict)

    with open('link_dict.json', 'w') as json_file:
        json.dump(link_dict, json_file)

def write_report():
    # Open the json file to get data on unique pages and subdomains of ics.uci.edu  
    with open('link_dict.json', 'r') as json_file:
        data1 = json.load(json_file)

    # Open the json file to get data on longest page and 50 most common words
    with open('word_dict.json', 'r') as json_file:
        data2 = json.load(json_file)

    # Open the text file to write the report 
    with open('report.txt', 'w') as report_file: 
        # 1. How many unique pages did you find?
        report_file.write('Total Unique Pages: {}\n\n'.format(data1['counter']['total_unique_pages']))

        # 2. What is the longest page in terms of the number of words?
        for url, count in data2['counter']['URL_with_most_words'].items():
            report_file.write('The longest page in terms of the number of words: {}\n   With the total of {} words\n\n'.format(url, count))

        # 3. What are the 50 most common words in the entire set of pages crawled under these domains?
        i = 1
        report_file.write('The 50 most common words in the entire set of pages crawled under these domains:\n')
        for word, count in data2['counter']['50_most_common_words'].items():
            report_file.write('{}. {}, {}\n'.format(i, word, count))
            i += 1

        # 4. How many subdomains did you find in the ics.uci.edu domain?
        report_file.write('\nTotal ics.uci.edu subdomain, written in [URL, number] format:\n')
        for subdomain, count  in data1['counter']['ics.uci.edu_subdomains'].items():
            report_file.write('http://{}.ics.uci.edu, {}\n'.format(subdomain, count))

def get_permission(url):
    # try:
    #     print("-"*40)
    #     parsed = urlparse(url)
    #     robots = 'https://' + parsed.netloc + '/robots.txt'
    #     page = requests.get(robots)
    #     soup = BeautifulSoup(page.content, 'html.parser')
    #     data = soup.get_text()

    #     start_index = data.find('User-agent: *')
    #     end_index = data.find('User-agent:',start_index) 
    #     pattern = "Disallow:\|(.*?)\|\n"
    #     if start_index != -1:
    #         print(data.find('Disallow:', index))
    #     else:
    #         print('No user-agent: *')


    # except TypeError:
    #     print("TypeError for ", parsed)
    #     raise
    pass

if __name__ == '__main__':
    # tokenizer("this isn't a word what about mother-in-law but this uses the punctuations like , and . !@#$%^&*()-= and.also")
    # tokenizer('fly flew flown, eat eaten, have has had, go goes gone going went')
    # tokenizer('is am are was were been being')
    # tokenize('isn\'t')
    # reset_link_dict()
    pass