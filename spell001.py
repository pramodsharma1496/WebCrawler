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

# Function to check spelling mistakes in text, skipping short words and alphanumerics
def spell_check(text):
    spell = SpellChecker()
    words = text.split()
    # Skip words that are 2–3 characters or alphanumeric
    filtered_words = [word for word in words if len(word) > 3 and word.isalpha()]
    misspelled = spell.unknown(filtered_words)
    return misspelled

# Function to crawl and extract URLs and text recursively
def crawl(url, prefix, max_depth, current_depth=0):
    if current_depth > max_depth:
        return []

    try:
        urls, text = extract_urls_and_text(url)
    except Exception as e:
        print(f"Error accessing URL: {url} - {e}")
        return []

    misspelled = spell_check(text)
    if misspelled:
        print(f"Spelling mistakes at URL: {url} - {misspelled}")

    crawled_urls = {url: {'text': text, 'misspelled': list(misspelled)}}

    for next_url in urls:
        # Only follow URLs that start with the same prefix
        if next_url.startswith(prefix):
            crawl(next_url, prefix, max_depth, current_depth + 1)

# Main function
def main(csv_file, max_depth):
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            starting_url = row[0]
            prefix = urlparse(starting_url).scheme + "://" + urlparse(starting_url).netloc
            print(f"Starting crawl at: {starting_url}")
            crawl(starting_url, prefix, max_depth)

# Example usage
if __name__ == "__main__":
    csv_file = "urls.csv"  # CSV file containing starting URLs
    max_depth = 2  # Maximum depth of crawling
    main(csv_file, max_depth)
