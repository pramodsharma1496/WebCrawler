import os
import time
import base64
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# Constants
OUTPUT_DIR = "./screenshots"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "screenshot.png")  # Ensure a valid directory path
MOBILE_METRICS = {
    "width": 375,
    "height": 812,
    "deviceScaleFactor": 3,
    "mobile": True
}
URL = "https://devircsapp.azurewebsites.net/"  # Replace with your target URL

# Create output directory if it doesn't exist
os.makedirs(OUTPUT_DIR, exist_ok=True)


def setup_driver():
    """Set up the Chrome WebDriver with DevTools protocol and mobile emulation."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")

    # Initialize the Chrome driver
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def capture_full_page_screenshot(driver, output_file):
    """Capture a full-page screenshot using Chrome DevTools protocol."""
    try:
        # Set device metrics
        driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", MOBILE_METRICS)

        # Navigate to the target URL
        driver.get(URL)
        time.sleep(3)  # Allow the page to fully load

        # Capture screenshot
        screenshot = driver.execute_cdp_cmd("Page.captureScreenshot", {"format": "png", "fromSurface": True})

        # Decode Base64 data and save as PNG
        with open(output_file, "wb") as f:
            f.write(base64.b64decode(screenshot["data"]))

        print(f"Screenshot saved: {output_file}")
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
    finally:
        driver.quit()


def main():
    """Main function to capture a screenshot of the specified webpage."""
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Screenshot will be saved as: {OUTPUT_FILE}")

    driver = setup_driver()
    capture_full_page_screenshot(driver, OUTPUT_FILE)
    print("Screenshot process completed.")


if __name__ == "__main__":
    main()
