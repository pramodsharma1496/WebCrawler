import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Function to extract URLs from a given URL
def extract_urls(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    # Extract absolute URLs
    return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]

# Function to crawl URLs recursively
def crawl(url, max_depth, visited=None, current_depth=0, broken_urls=None):
    if visited is None:
        visited = set()
    if broken_urls is None:
        broken_urls = []

    if current_depth > max_depth or url in visited:
        return broken_urls

    visited.add(url)
    print(f"Processing URL: {url}")  # Log progress

    # Extract URLs and validate them
    child_urls = extract_urls(url)
    for next_url in child_urls:
        next_url = next_url.split('#')[0]  # Remove fragments (e.g., #section)
        if next_url not in visited and next_url.startswith(urlparse(url).scheme + "://" + urlparse(url).netloc):
            if not is_valid(next_url):
                print(f"Broken URL detected: {next_url}")  # Log broken URL
                broken_urls.append(next_url)
            else:
                crawl(next_url, max_depth, visited, current_depth + 1, broken_urls)

    return broken_urls

# Function to check if a URL is valid
def is_valid(url):
    try:
        # Use requests.get as a fallback for better reliability
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code != 200:
            response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Main function
def main(csv_file, max_depth):
    broken_urls = []
    visited = set()  # Track all visited URLs to avoid duplicates

    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            starting_url = row[0]
            if is_valid(starting_url):
                print(f"Starting crawl for: {starting_url}")
                broken_urls.extend(crawl(starting_url, max_depth, visited))
            else:
                print(f"Invalid starting URL: {starting_url}")
                broken_urls.append(starting_url)

    print("\nBroken URLs List:")
    for url in set(broken_urls):  # Remove duplicates
        print(url)

# Example usage
if __name__ == "__main__":
    csv_file = "urls.csv"  # CSV file containing starting URLs
    max_depth = 2  # Maximum depth of crawling
    main(csv_file, max_depth)
