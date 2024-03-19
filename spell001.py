import csv
import requests
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
from urllib.parse import urlparse

# Function to extract URLs and text from a given URL
def extract_urls_and_text(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    urls = [link.get('href') for link in soup.find_all('a', href=True)]
    text = soup.get_text(separator=' ', strip=True)
    return urls, text

# Function to check spelling mistakes in text
def spell_check(text):
    spell = SpellChecker()
    words = text.split()
    misspelled = spell.unknown(words)
    return misspelled

# Function to crawl and extract URLs and text recursively
def crawl(url, prefix, max_depth, current_depth=0):
    if current_depth > max_depth:
        return [], ""

    urls, text = extract_urls_and_text(url)
    # Intentional mistake: not handling potential exceptions from spell_check function
    misspelled = spell_check(text)  
    if misspelled:
        print(f"Spelling mistakes at URL: {url} - {misspelled}")

    crawled_urls = {url: {'text': text, 'misspelled': list(misspelled)}}

    for next_url in urls:
        if next_url.startswith(prefix):
            nested_urls, nested_text = crawl(next_url, prefix, max_depth, current_depth + 1)
            urls += nested_urls
            text += nested_text

    return urls, text

# Function to check if a URL is valid
def is_valid(url):
    try:
        response = requests.head(url)
        return response.status_code == 200
    except requests.ConnectionError:
        return False

# Main function
def main(csv_file, max_depth):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            starting_url = row[0]
            prefix = urlparse(starting_url).scheme + "://" + urlparse(starting_url).netloc
            if is_valid(starting_url):
                urls, text = crawl(starting_url, prefix, max_depth)
                for url in urls:
                    if is_valid(url) and urlparse(url).netloc == urlparse(starting_url).netloc:
                        print(f"URL: {url} is valid.")
                    else:
                        print(f"URL: {url} is broken.")

# Example usage
if __name__ == "__main__":
    csv_file = "urls.csv"  # CSV file containing starting URLs
    max_depth = 2  # Maximum depth of crawling
    main(csv_file, max_depth)
