Here's a sample README file for your project. You can copy this into a `README.md` file in your project folder:

```markdown
# Web Screenshot Crawler

This project is designed to crawl specified URLs, capture full-page screenshots, and store them in a designated directory. It uses Selenium for rendering pages and capturing screenshots, requests for extracting URLs from web pages, and BeautifulSoup for parsing HTML content.

## Features
- Crawl websites starting from a set of initial URLs.
- Extract valid URLs from pages, ensuring the domain matches the allowed domain and specific patterns are not skipped.
- Capture full-page screenshots using Selenium in mobile viewports.
- Automatically handle scrolling to capture screenshots of long pages.
- Configurable allowed domain, starting URLs, and skip patterns via a CSV config file.

## Requirements

- Python 3.x
- Selenium
- BeautifulSoup4
- Requests
- ChromeDriver (or equivalent for your browser)
- Optional: Headless browser for running in environments without display servers.

### Installing Dependencies

To install the required Python packages, use pip:

```bash
pip install selenium beautifulsoup4 requests
```

You will also need to install [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/) or the appropriate WebDriver for your browser.

### Setting Up ChromeDriver

1. **Download ChromeDriver** from the official site: [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/)
2. Make sure to download the correct version that matches your installed Chrome browser version.
3. Add the ChromeDriver to your system's `PATH`, or specify the path directly in your script.

## Configuration

The configuration file `config.csv` should be set up with the following structure:

```csv
key,value
allowed_domain,dexvil.com
starting_url,https://www.dexvil.com/
skip_exact,/download
skip_substring,login
```

- **allowed_domain**: The domain to limit URL crawling to.
- **starting_url**: The initial URLs to start crawling from.
- **skip_exact**: URLs to skip if they match exactly.
- **skip_substring**: URLs containing these substrings will be skipped.

### Example config.csv

```csv
key,value
allowed_domain,dexvil.com
starting_url,https://www.dexvil.com/
skip_exact,/download
skip_substring,login
```

### Mobile View Configuration

The script simulates mobile browsing using the latest standard mobile screen sizes. The current setup simulates a mobile viewport with a size of 375 x 812 pixels, which matches many modern smartphones (e.g., iPhone X, iPhone 12).

## Running the Script

1. Ensure that the `config.csv` file is configured properly with valid URLs and domains.
2. Run the script by executing the following:

```bash
python screenshot_crawler.py
```

The script will:

1. Load the configuration from `config.csv`.
2. Start crawling the URLs defined in `starting_url`.
3. Extract all valid links from the crawled pages.
4. Capture full-page screenshots (scrolling to capture long pages).
5. Save the screenshots in the `screenshots` directory.

## Directory Structure

```plaintext
.
├── screenshot_crawler.py         # Main script to crawl and capture screenshots
├── config.csv                    # Configuration file for the crawler
├── screenshots/                  # Folder where screenshots will be saved
└── README.md                     # Project documentation
```

## Notes

- **Max Depth**: The script crawls up to `MAX_DEPTH` levels from the starting URL. This helps limit the depth of the crawl.
- **Mobile Viewport**: Screenshots are taken using a simulated mobile viewport of 375x812 px. This allows the screenshots to resemble what users would see on modern smartphones.
- **Parallel Processing**: The script uses multithreading to process URLs concurrently, speeding up the crawling process.

## Troubleshooting

- **Missing Config File**: Ensure that the `config.csv` file is present and correctly formatted.
- **Chromedriver Issues**: Ensure that ChromeDriver is installed and properly configured on your system.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

For any issues or contributions, please feel free to open an issue or pull request in this repository.
```

This README provides an overview of your project, explains how to set it up, run it, and troubleshoot issues. You can modify and expand it based on the specific needs of your project.
