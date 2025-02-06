import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
import csv
import queue
from threading import Lock
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Configuration
SKIP_PATTERNS_SET = set()           # Already defined skip patterns
SKIP_PATTERNS_SUBSTRING = []         # Substring patterns to skip if contained anywhere in the URL

# New configuration options for skipping URLs
SKIP_EXACT_URLS = {                 # Exact URLs to skip
    # e.g., "https://example.com/skip-this-page"
}
SKIP_URL_SUFFIXES = [               # URL suffixes to skip
    # e.g., ".pdf", ".jpg", "/ignore"
    "/ircs@indianredcross.org","pdf"
]

MAX_WORKERS = 20
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3
STATUS_FORCELIST = [500, 502, 503, 504]

# Thread-safe globals
visited = set()
visited_lock = Lock()
broken_urls = []
broken_lock = Lock()

def requests_retry_session():
    session = requests.Session()
    retries = Retry(
        total=MAX_RETRIES,
        backoff_factor=1,
        status_forcelist=STATUS_FORCELIST,
    )
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))
    return session

def should_skip_url(url):
    # Skip if URL is in a pre-defined set
    if url in SKIP_PATTERNS_SET:
        return True

    # Skip if URL exactly matches one in SKIP_EXACT_URLS
    if url in SKIP_EXACT_URLS:
        return True

    # Skip if URL ends with any of the defined suffixes
    for suffix in SKIP_URL_SUFFIXES:
        if url.endswith(suffix):
            return True

    # Skip if any substring pattern is found in the URL
    if any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING):
        return True

    return False

def is_same_domain(url, base_netloc):
    return urlparse(url).netloc == base_netloc

def process_url(url_info, base_netloc, max_depth, q, session):
    url, depth = url_info
    if depth > max_depth:
        return

    with visited_lock:
        if url in visited or should_skip_url(url):
            return
        visited.add(url)

    if not is_same_domain(url, base_netloc):
        return

    try:
        # Validate URL
        response = session.head(url, timeout=5, allow_redirects=True)
        if not handle_status_code(response.status_code, url):
            with broken_lock:
                broken_urls.append(url)
            return
    except requests.RequestException as e:
        with broken_lock:
            broken_urls.append(url)
        return

    print(f"Processing: {url} (Depth {depth})")

    # Extract URLs
    try:
        if "wordpress" in url.lower():
            urls = fetch_sitemap(url, session)
        else:
            urls = extract_urls(url, session)
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return

    # Add child URLs to queue
    for new_url in urls:
        # Remove any fragment and make the URL absolute
        new_url = urljoin(url, new_url.split('#')[0])
        parsed_url = urlparse(new_url)
        clean_url = parsed_url.geturl()

        if (depth + 1 <= max_depth and
            not should_skip_url(clean_url) and
            is_same_domain(clean_url, base_netloc)):
            with visited_lock:
                if clean_url not in visited:
                    q.put((clean_url, depth + 1))

def extract_urls(url, session):
    try:
        response = session.get(url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')
        return [link.get('href') for link in soup.find_all('a', href=True)]
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return []

def fetch_sitemap(url, session):
    try:
        sitemap_url = urljoin(url, "/sitemap.xml")
        response = session.get(sitemap_url, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(response.content, "lxml-xml")
        return [loc.text for loc in soup.find_all("loc")]
    except requests.RequestException:
        return []

def handle_status_code(status_code, url):
    if status_code == 200:
        return True
    print(f"HTTP {status_code} for {url}")
    return False

def worker(base_netloc, max_depth, q):
    session = requests_retry_session()
    while True:
        try:
            url_info = q.get(timeout=5)
            process_url(url_info, base_netloc, max_depth, q, session)
            q.task_done()
        except queue.Empty:
            break
        except Exception as e:
            print(f"Worker error: {e}")
    session.close()

def main(csv_file, max_depth):
    starting_urls = []
    try:
        with open(csv_file) as f:
            starting_urls = [row[0].strip() for row in csv.reader(f) if row]
    except FileNotFoundError:
        print(f"File {csv_file} not found")
        return

    q = queue.Queue()
    for url in starting_urls:
        parsed = urlparse(url)
        base_netloc = parsed.netloc
        if not should_skip_url(url) and is_same_domain(url, base_netloc):
            q.put((url, 0))

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for _ in range(MAX_WORKERS):
            executor.submit(worker, base_netloc, max_depth, q)

    q.join()
    print("\nBroken URLs:")
    for url in set(broken_urls):
        print(url)

if __name__ == "__main__":
    main("urls.csv", 3)
