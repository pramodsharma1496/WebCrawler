import os
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import csv
import time
import functools

# Constants
MAX_WORKERS = 5  # Reduced to prevent overload
MAX_DEPTH = 3
OUTPUT_DIR = "./screenshots"
CONFIG_FILE = "config.csv"

# Device Metrics for Android and iOS devices
DEVICE_METRICS = {
    "iPhone_13": {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True},
}

# Global variables loaded from config
ALLOWED_DOMAIN = None
STARTING_URLS = []
SKIP_PATTERNS_SET = set()
SKIP_PATTERNS_SUBSTRING = []

# Setup logging
logging.basicConfig(filename="screenshot_errors.log", level=logging.ERROR)

# Retry decorator for error handling
def retry_on_exception(retries=3, delay=5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    logging.error(f"Attempt {attempt + 1} failed: {e}")
                    time.sleep(delay)
            raise Exception(f"Failed after {retries} attempts")
        return wrapper
    return decorator

def load_config():
    """Load configuration from CSV."""
    global ALLOWED_DOMAIN, STARTING_URLS, SKIP_PATTERNS_SET, SKIP_PATTERNS_SUBSTRING
    try:
        with open(CONFIG_FILE, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                key, value = row["key"], row["value"]
                if key == "allowed_domain":
                    ALLOWED_DOMAIN = value
                elif key == "starting_url":
                    STARTING_URLS.append(value)
                elif key == "skip_exact":
                    SKIP_PATTERNS_SET.add(value)
                elif key == "skip_substring":
                    SKIP_PATTERNS_SUBSTRING.append(value)
        print("Configuration loaded successfully.")
    except FileNotFoundError:
        print(f"Error: Config file '{CONFIG_FILE}' not found.")
        exit(1)

def setup_driver(device="iPhone_13"):
    """Set up a headless mobile Chrome driver."""
    device_metrics = DEVICE_METRICS[device]
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={device_metrics['width']},{device_metrics['height']}")
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(60)
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', device_metrics)
    return driver

@retry_on_exception()
def capture_screenshots_with_scroll(url, driver, output_dir):
    """Capture screenshots of a webpage with scrolling."""
    try:
        driver.get(url)
        # Wait for the page to load completely
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        page_title = driver.title.replace(' ', '_').replace('/', '_')
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll = 0
        part = 1

        while current_scroll < scroll_height:
            screenshot_filename = os.path.join(output_dir, f"{page_title}_part{part}.png")
            driver.save_screenshot(screenshot_filename)
            print(f"Screenshot saved: {screenshot_filename}")
            current_scroll += DEVICE_METRICS["iPhone_13"]['height']
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            time.sleep(1)
            scroll_height = driver.execute_script("return document.body.scrollHeight")
            part += 1
    except Exception as e:
        logging.error(f"Error capturing screenshots for {url}: {e}")
        print(f"Error capturing screenshots for {url}. Details logged.")

def extract_urls(url):
    """Extract valid URLs from a webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        urls = [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
        return [u for u in urls if not should_skip_url(u)]
    except requests.RequestException as e:
        logging.error(f"Error fetching URL {url}: {e}")
        return []

def should_skip_url(url):
    """Check if a URL should be skipped."""
    if url in SKIP_PATTERNS_SET or any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING):
        return True
    if url.endswith(('.pdf', '/download')):
        return True
    return False

def crawl_urls(start_url, max_depth):
    """Crawl URLs up to a given depth."""
    visited = set()
    to_visit = {start_url}

    for _ in range(max_depth):
        next_to_visit = set()
        for url in to_visit:
            if url not in visited:
                visited.add(url)
                child_urls = extract_urls(url)
                next_to_visit.update(
                    u for u in child_urls if urlparse(u).netloc == ALLOWED_DOMAIN
                )
        to_visit = next_to_visit
    return visited

def process_urls(urls):
    """Process URLs and take screenshots."""
    driver = setup_driver()
    for url in urls:
        try:
            capture_screenshots_with_scroll(url, driver, OUTPUT_DIR)
        except Exception as e:
            logging.error(f"Error processing URL {url}: {e}")
            print(f"Error processing URL {url}. Details logged.")
    driver.quit()

def main():
    start_time = time.time()
    load_config()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_urls = set()
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(crawl_urls, url, MAX_DEPTH): url for url in STARTING_URLS}
        for future in as_completed(futures):
            try:
                all_urls.update(future.result())
            except Exception as e:
                logging.error(f"Error during crawling: {e}")

    print(f"Discovered {len(all_urls)} URLs.")
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        executor.submit(process_urls, all_urls)

    end_time = time.time()
    print(f"Total execution time: {end_time - start_time:.2f} seconds.")

if __name__ == "__main__":
    main()
