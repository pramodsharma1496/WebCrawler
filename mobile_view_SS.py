import os
import requests
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

# Constants
MAX_WORKERS = 5
MAX_DEPTH = 2
OUTPUT_DIR = "./screenshots"
ALLOWED_DOMAIN = "devircsapp.azurewebsites.net"

# Set of exact and substring patterns for skipping URLs
SKIP_PATTERNS_SET = {
    "https://www.eraktkosh.in/HISUtilities/dashboard/dashBoardACTION.cnt",
    "https://www.linkedin.com/company/ircsnewdelhi/",
    "/ircs@indianredcross.org",
    "https://dev-ircs-admin-panel.azurewebsites.net/donation-form",
    "https://devircsapp.azurewebsites.net/tenders/",
    "https://devircsapp.azurewebsites.net/careers/",
    "https://devircsapp.azurewebsites.net/important-forms/",
    "https://devircsapp.azurewebsites.net/rti/",
    "https://devircsapp.azurewebsites.net/monthly-expenditure/",
    "https://devircsapp.azurewebsites.net/our-partners-2/",
    "https://ifrc.csod.com/client/ifrc/default.aspx",
    "https://devircsapp.azurewebsites.net/st-john-ambulance/",
    "https://twitter.com/search?q=%40IndianRedCross&amp%3Bsrc=typd",
    "https://www.facebook.com/ircsofficial",
    "https://www.youtube.com/channel/UC3Zf4Kg9OUE4VN5NYivo99A",
    "https://www.instagram.com/indianredcross1/",
    "https://www.linkedin.com/company/ircsnewdelhi/"
}

SKIP_PATTERNS_SUBSTRING = [
    "dashboard/dashBoardACTION.cnt",
    "ircs@indianredcross.org"
]

# Function to set up headless Chrome driver
def setup_driver():
    """Sets up a headless Chrome driver with mobile emulation."""
    options = Options()
    options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)

# Function to capture screenshots of a URL with scrolling
def capture_screenshots_with_scroll(url, output_dir):
    """Captures screenshots of the full page with scrolling in mobile view."""
    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(3)  # Allow the page to load fully

        # Get the page title
        page_title = driver.title.replace(' ', '_').replace('/', '_')

        # Scroll and capture screenshots
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        current_scroll = 0
        part = 1

        while current_scroll < scroll_height:
            driver.set_window_size(375, 1000)
            screenshot_filename = os.path.join(output_dir, f"{page_title}_part{part}.png")
            driver.save_screenshot(screenshot_filename)
            print(f"Screenshot saved: {screenshot_filename}")
            part += 1

            # Scroll down
            current_scroll += 1000
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

# Function to validate if a URL is reachable
def is_valid(url):
    """Checks if a URL is valid by sending a GET request."""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except requests.RequestException:
        return False

# Function to check if a URL should be skipped
def should_skip_url(url):
    """Determines if a URL should be skipped based on exact, substring matches, or domain."""
    parsed_url = urlparse(url)
    if parsed_url.netloc != ALLOWED_DOMAIN:
        return True
    if url in SKIP_PATTERNS_SET:
        return True
    if url.endswith('.pdf'):  # Skip URLs ending with .pdf
        return True
    return any(pattern in url for pattern in SKIP_PATTERNS_SUBSTRING)

# Function to crawl URLs iteratively
def crawl(url, max_depth, visited, to_visit):
    """Crawl URLs iteratively to a given depth."""
    to_visit.add(url)
    visited.add(url)

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
                visited.add(child_url)
                to_visit.add(child_url)

# Main function to initiate crawling and screenshot capture
def main():
    """Main function to initiate crawling and capture screenshots."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    starting_urls = ["https://devircsapp.azurewebsites.net/"]

    visited = set()
    to_visit = set()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        for url in starting_urls:
            if url not in visited and not should_skip_url(url) and is_valid(url):
                print(f"Starting crawl for: {url}")
                crawl(url, MAX_DEPTH, visited, to_visit)

        executor.map(lambda url: capture_screenshots_with_scroll(url, OUTPUT_DIR), visited)

if __name__ == "__main__":
    main()
