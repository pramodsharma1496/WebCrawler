import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
import csv

# Exact matches for skipping URLs
SKIP_PATTERNS_SET = {
    # Add any URLs that should be skipped exactly
}

# Substring patterns for skipping URLs
SKIP_PATTERNS_SUBSTRING = [
    # Add any substring patterns for skipping URLs
]

# Function to extract URLs from a given URL (for regular websites)
def extract_urls(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

    soup = BeautifulSoup(response.content, 'lxml')  # Use lxml for faster parsing
    return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]

# Function to fetch URLs from a sitemap.xml (for WordPress and similar websites)
def fetch_sitemap(url):
    sitemap_url = urljoin(url, "/sitemap.xml")
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "lxml-xml")
        return [loc.text for loc in soup.find_all("loc")]
    except requests.RequestException as e:
        print(f"Failed to fetch sitemap: {e}")
        return []
    except Exception as e:
        print(f"Error parsing sitemap: {e}")
        return []

# Function to validate if a URL is reachable
def is_valid(url):
    try:
        response = requests.head(url, timeout=5, allow_redirects=True)
        return handle_status_code(response.status_code, url)
    except requests.RequestException as e:
        print(f"Request exception for URL {url}: {e}")
        return False

# Function to handle different HTTP status codes
def handle_status_code(status_code, url):
    if status_code == 200:
        return True
    elif status_code == 404:
        print(f"URL not found (404): {url}")
    elif status_code == 403:
        print(f"Forbidden (403): {url}")
    elif status_code == 401:
        print(f"Unauthorized (401): {url}")
    elif status_code == 500:
        print(f"Internal Server Error (500): {url}")
    elif status_code == 502:
        print(f"Bad Gateway (502): {url}")
    elif status_code == 503:
        print(f"Service Unavailable (503): {url}")
    elif status_code == 504:
        print(f"Gateway Timeout (504): {url}")
    else:
        print(f"Unhandled status code {status_code} for URL: {url}")
    return False

# Function to check if a URL should be skipped
def should_skip_url(url):
    if url in SKIP_PATTERNS_SET:
        return True
    return any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING)

# Function to check if the URL belongs to the same domain as the starting URL
def is_same_domain(url, base_url):
    base_netloc = urlparse(base_url).netloc
    current_netloc = urlparse(url).netloc
    return base_netloc == current_netloc

# Function to handle crawling for regular websites and WordPress sitemaps
def crawl(url, max_depth, visited, base_url, current_depth=0, broken_urls=None):
    if broken_urls is None:
        broken_urls = []

    if current_depth > max_depth or url in visited or should_skip_url(url):
        return broken_urls

    visited.add(url)
    print(f"Processing URL: {url}")

    if not is_same_domain(url, base_url):
        print(f"Skipping URL outside of base domain: {url}")
        return broken_urls

    if "wordpress" in url.lower():
        sitemap_urls = fetch_sitemap(url)
        for sitemap_url in sitemap_urls:
            if sitemap_url not in visited and not should_skip_url(sitemap_url):
                if not is_valid(sitemap_url):
                    broken_urls.append(sitemap_url)
                else:
                    crawl(sitemap_url, max_depth, visited, base_url, current_depth + 1, broken_urls)
    else:
        child_urls = extract_urls(url)
        for next_url in child_urls:
            next_url = next_url.split('#')[0]
            parsed_url = urlparse(next_url)
            if next_url.startswith(f"{parsed_url.scheme}://{parsed_url.netloc}") and not should_skip_url(next_url):
                if next_url not in visited and is_same_domain(next_url, base_url):
                    if not is_valid(next_url):
                        broken_urls.append(next_url)
                    else:
                        crawl(next_url, max_depth, visited, base_url, current_depth + 1, broken_urls)

    return broken_urls

# Main function to initiate crawling
def main(csv_file, max_depth):
    broken_urls = []
    visited = set()

    try:
        with open(csv_file, 'r') as file:
            reader = csv.reader(file)
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = []
                for row in reader:
                    if not row:
                        continue
                    starting_url = row[0].strip()
                    if starting_url not in visited and not should_skip_url(starting_url):
                        if is_valid(starting_url):
                            print(f"Starting crawl for: {starting_url}")
                            base_url = urlparse(starting_url).scheme + "://" + urlparse(starting_url).netloc
                            future = executor.submit(crawl, starting_url, max_depth, visited, base_url)
                            futures.append(future)
                        else:
                            broken_urls.append(starting_url)
                for future in futures:
                    broken_urls.extend(future.result())
    except FileNotFoundError:
        print(f"Error: The file '{csv_file}' was not found.")
        return

    print("\nBroken URLs List:")
    for url in set(broken_urls):
        print(url)

# Example usage
if __name__ == "__main__":
    csv_file = "urls.csv"
    max_depth = 3
    main(csv_file, max_depth)
