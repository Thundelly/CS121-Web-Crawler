import collections
import json


def sort_word_dict():
    with open('word_dict.json') as json_file:
        word_dict = json.load(json_file)

        # Sort the word list by value (non-ascending), and then by key (alphabetical)
        sorted_word_list = sorted(
            word_dict['word_list'].items(), key=lambda item: (-item[1], item[0]))
        # Put the dictionary into an OrderedDict to conserve its order
        sorted_word_list = collections.OrderedDict(sorted_word_list)
        # Copy the dictionary to get top 50 words with most frequency
        top_50 = sorted_word_list.copy()

        # Remove all entries that are beyond the first 50 entries
        while len(top_50) > 50:
            top_50.popitem()

        # Add the words list dictionary and top 50 frequent word dictionary
        # to the original dictionary
        word_dict['word_list'] = sorted_word_list
        word_dict['counter']['50_most_common_words'] = top_50

        # Dump the python dictionary to JSON format and save for future use
        with open('word_dict.json', 'w') as json_file:
            json.dump(word_dict, json_file)

def generate_report():

    sort_word_dict()

    # Open the json file to get data on unique pages and subdomains of ics.uci.edu
    with open('link_dict.json', 'r') as json_file:
        data1 = json.load(json_file)

    # Open the json file to get data on longest page and 50 most common words
    with open('word_dict.json', 'r') as json_file:
        data2 = json.load(json_file)

    # Open the text file to write the report
    with open('report.txt', 'w') as report_file:
        # 1. How many unique pages did you find?
        report_file.write('Total Unique Pages: {}\n\n'.format(
            data1['counter']['total_unique_pages']))

        # 2. What is the longest page in terms of the number of words?
        for url, count in data2['counter']['URL_with_most_words'].items():
            report_file.write(
                'The longest page in terms of the number of words: {}\n   With the total of {} words\n\n'.format(url, count))

        # 3. What are the 50 most common words in the entire set of pages crawled under these domains?
        i = 1
        report_file.write(
            'The 50 most common words in the entire set of pages crawled under these domains:\n')
        for word, count in data2['counter']['50_most_common_words'].items():
            report_file.write('{}. {}, {}\n'.format(i, word, count))
            i += 1

        # 4. How many subdomains did you find in the ics.uci.edu domain?
        report_file.write(
            '\nTotal ics.uci.edu subdomain, written in [URL, number] format:\n')
        for subdomain, count in sorted(data1['counter']['ics.uci.edu_subdomains'].items(), key=lambda item: item[0].lower()):
            report_file.write(
                'http://{}.ics.uci.edu, {}\n'.format(subdomain, count))