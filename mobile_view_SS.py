import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.webdriver import WebDriver
import csv
import time

# Constants
MAX_WORKERS = 5
MAX_DEPTH = 2
OUTPUT_DIR = "./screenshots"
CONFIG_FILE = "config.csv"  # External config file

# Device Metrics for Android and iOS devices
DEVICE_METRICS = {
    "iPhone_13": {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True},
    "Galaxy_S10": {"width": 412, "height": 915, "deviceScaleFactor": 3, "mobile": True},
    "iPhone_X": {"width": 375, "height": 812, "deviceScaleFactor": 3, "mobile": True},
    "Pixel_4": {"width": 412, "height": 869, "deviceScaleFactor": 3, "mobile": True},
    "iPhone_12": {"width": 390, "height": 844, "deviceScaleFactor": 3, "mobile": True},
}

# Global variables loaded from config
ALLOWED_DOMAIN = None
STARTING_URLS = []
SKIP_PATTERNS_SET = set()
SKIP_PATTERNS_SUBSTRING = []

# Function to load configuration from CSV
def load_config():
    """Loads configuration settings from a CSV file."""
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
        print(f"Configuration loaded:\n ALLOWED_DOMAIN={ALLOWED_DOMAIN}\n STARTING_URLS={STARTING_URLS}")
    except FileNotFoundError:
        print(f"Error: Config file '{CONFIG_FILE}' not found.")
        exit(1)

# Function to set up a headless mobile Chrome driver for a specific device
def setup_driver(device="iPhone_13") -> WebDriver:
    """Sets up a headless Chrome driver for a specific mobile view."""
    device_metrics = DEVICE_METRICS.get(device, DEVICE_METRICS["Pixel_4"])  # Default to iPhone 13 if device not found
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument(f"--window-size={device_metrics['width']},{device_metrics['height']}")  # Device screen size
    options.add_argument(f"user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/537.36 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/537.36")  # Mobile User-Agent
    # Use DevTools Protocol to simulate mobile devices
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
        'width': device_metrics['width'],
        'height': device_metrics['height'],
        'deviceScaleFactor': device_metrics['deviceScaleFactor'],
        'mobile': device_metrics['mobile'],
    })
    return driver

# Function to capture screenshots of a URL with scrolling in mobile view
def capture_screenshots_with_scroll(url, output_dir):
    """Captures screenshots of the full page with scrolling in mobile view."""
    try:
        driver = setup_driver("iPhone_13")  # Set device here
        driver.get(url)
        time.sleep(3)  # Allow the page to load fully

        # Get the page title and sanitize it for filenames
        page_title = driver.title.replace(' ', '_').replace('/', '_')

        # Scroll and capture screenshots
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll = 0
        part = 1

        while current_scroll < scroll_height:
            screenshot_filename = os.path.join(output_dir, f"{page_title}_part{part}.png")
            driver.save_screenshot(screenshot_filename)
            print(f"Screenshot saved: {screenshot_filename}")
            part += 1

            # Scroll down
            current_scroll += DEVICE_METRICS["iPhone_13"]['height']  # Scroll by the height of mobile screen
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            time.sleep(2)

            scroll_height = driver.execute_script("return document.body.scrollHeight")
    except Exception as e:
        print(f"Error capturing screenshots for {url}: {e}")
    finally:
        driver.quit()

# Function to extract URLs from a given webpage
def extract_urls(url):
    """Extracts all valid URLs from a given webpage."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
    except requests.RequestException as e:
        print(f"Error fetching URL {url}: {e}")
        return []

# Function to check if a URL should be skipped
def should_skip_url(url):
    """Determines if a URL should be skipped."""
    parsed_url = urlparse(url)
    if url in SKIP_PATTERNS_SET:
        print(f"Skipping URL (exact match): {url}")
        return True
    if url.endswith('/download'):
        print(f"Skipping URL (/download): {url}")
        return True
    if url.endswith('.pdf'):  # Skip URLs ending with .pdf
        print(f"Skipping URL (.pdf file): {url}")
        return True

    if any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING):
        print(f"Skipping URL (substring match): {url}")
        return True
    return False

# Function to validate if a URL is reachable
def is_valid(url):
    """Checks if a URL is valid by sending a GET request."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to crawl URLs iteratively
def crawl(url, max_depth, visited, to_visit):
    """Crawl URLs iteratively to a given depth."""
    to_visit.add(url)
    visited.add(url)
    print(f"Starting crawl with: {url}")

    while to_visit:
        current_url = to_visit.pop()
        print(f"Processing URL: {current_url}")
        child_urls = extract_urls(current_url)

        for child_url in child_urls:
            parsed_child_url = urlparse(child_url)
            if (
                parsed_child_url.netloc == ALLOWED_DOMAIN
                and child_url not in visited
                and not should_skip_url(child_url)
                and is_valid(child_url)
            ):
                print(f"Adding URL to visit: {child_url}")
                visited.add(child_url)
                to_visit.add(child_url)

# Main function to initiate crawling and screenshot capture
def main():
    """Main function to initiate crawling and capture screenshots."""
    start_time = time.time()  # Record start time
    load_config()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    visited = set()
    to_visit = set()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for url in STARTING_URLS:
            if url not in visited and not should_skip_url(url) and is_valid(url):
                print(f"Starting crawl for: {url}")
                crawl(url, MAX_DEPTH, visited, to_visit)

        executor.map(lambda url: capture_screenshots_with_scroll(url, OUTPUT_DIR), visited)

    end_time = time.time()  # Record end time
    execution_time = end_time - start_time
    print(f"Finished processing. Screenshots saved in {OUTPUT_DIR}.")
    print(f"Total execution time: {execution_time:.2f} seconds.")  # Print execution time

if __name__ == "__main__":
    main()
