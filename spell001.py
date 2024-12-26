import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Exact matches for skipping URLs
SKIP_PATTERNS_SET = {
    "https://www.eraktkosh.in/HISUtilities/dashboard/dashBoardACTION.cnt",
    "https://www.linkedin.com/company/ircsnewdelhi/",
    "/ircs@indianredcross.org"
}

# Substring patterns for skipping URLs
SKIP_PATTERNS_SUBSTRING = [
    "dashboard/dashBoardACTION.cnt",
    "ircs@indianredcross.org"
]

# Function to extract URLs from a given URL
def extract_urls(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'html.parser')
    return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]

# Function to validate if a URL is reachable
def is_valid(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        if response.status_code != 200:
            response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to check if a URL should be skipped
def should_skip_url(url):
    # Check for exact matches
    if url in SKIP_PATTERNS_SET:
        return True
    # Check for substring matches
    return any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING)

# Function to crawl URLs recursively
def crawl(url, max_depth, visited, current_depth=0, broken_urls=None):
    if broken_urls is None:
        broken_urls = []

    if current_depth > max_depth or url in visited or should_skip_url(url):
        return broken_urls

    visited.add(url)
    print(f"Processing URL: {url}")

    child_urls = extract_urls(url)
    for next_url in child_urls:
        next_url = next_url.split('#')[0]
        parsed_url = urlparse(next_url)
        if next_url.startswith(f"{parsed_url.scheme}://{parsed_url.netloc}") and not should_skip_url(next_url):
            if next_url not in visited:
                if not is_valid(next_url):
                    print(f"Broken URL detected: {next_url}")
                    broken_urls.append(next_url)
                else:
                    crawl(next_url, max_depth, visited, current_depth + 1, broken_urls)

    return broken_urls

# Main function to initiate crawling
def main(csv_file, max_depth):
    broken_urls = []
    visited = set()

    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                if not row:
                    continue
                starting_url = row[0].strip()
                if starting_url not in visited and not should_skip_url(starting_url):
                    if is_valid(starting_url):
                        print(f"Starting crawl for: {starting_url}")
                        broken_urls.extend(crawl(starting_url, max_depth, visited))
                    else:
                        print(f"Invalid starting URL: {starting_url}")
                        broken_urls.append(starting_url)
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    print("\nBroken URLs List:")
    for url in set(broken_urls):
        print(url)

# Example usage
if __name__ == "__main__":
    csv_file = "urls.csv"
    max_depth = 2
    main(csv_file, max_depth)
