from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
from concurrent.futures import ThreadPoolExecutor


def setup_driver():
    """Sets up a headless Chrome driver with mobile emulation."""
    options = Options()
    options.add_experimental_option("mobileEmulation", {"deviceName": "iPhone X"})
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)


def capture_screenshot(url, output_dir):
    """Captures a full-page screenshot in mobile view."""
    try:
        driver = setup_driver()
        driver.get(url)
        time.sleep(3)  # Allow the page to load fully

        # Scroll to capture full page
        scroll_height = driver.execute_script("return document.body.scrollHeight")
        driver.set_window_size(375, scroll_height)

        # Generate filename based on URL
        filename = os.path.join(output_dir, f"{url.replace('://', '_').replace('/', '_')}.png")
        driver.save_screenshot(filename)
        print(f"Screenshot saved: {filename}")
    except Exception as e:
        print(f"Error capturing screenshot for {url}: {e}")
    finally:
        driver.quit()


def main():
    """Main function to capture screenshots for multiple URLs."""
    urls = [
        "https://devircsapp.azurewebsites.net"
    ]

    output_dir = "./screenshots"
    os.makedirs(output_dir, exist_ok=True)

    # Use ThreadPoolExecutor for concurrent processing
    with ThreadPoolExecutor(max_workers=4) as executor:
        executor.map(lambda url: capture_screenshot(url, output_dir), urls)


if __name__ == "__main__":
    main()
