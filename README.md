# Web Crawler for Extracting Visible Text and Checking Spelling

This Python script is designed to crawl web pages, extract the visible text displayed on the frontend, and check for spelling mistakes in the extracted text. It can be useful for various purposes such as web content analysis, spell checking, or quality assurance testing.

## Features

- Extracts visible text from web pages.
- Checks spelling mistakes in the extracted text.
- Handles relative and absolute URLs.
- Limits the depth of crawling to prevent infinite loops.
- Detects and reports broken URLs.

## Dependencies

The following dependencies are required to run the script:

- requests
- BeautifulSoup4
- pyspellchecker

You can install these dependencies using pip:

pip install requests beautifulsoup4 pyspellchecker


## Usage

1. Clone the repository or download the Python script (`web_crawler.py`) to your local machine.

2. Ensure you have Python installed on your system. The script is compatible with Python 3.

3. Create a CSV file (`urls.csv`) containing the starting URLs you want to crawl. Each URL should be on a separate line.

4. Adjust the `MAX_DEPTH` and `MAX_REQUESTS` variables in the script according to your requirements. `MAX_DEPTH` specifies the maximum depth of crawling, and `MAX_REQUESTS` specifies the maximum number of requests allowed.

5. Run the script by executing the following command in your terminal or command prompt:

6. The script will start crawling the web pages, extracting visible text, checking for spelling mistakes, and reporting broken URLs.

## Example

Suppose you want to crawl a website `example.com`:

1. Create a CSV file `urls.csv` with the following content:

2. Run the script, and it will start crawling the website, extracting visible text, and checking for spelling mistakes.

## Limitations

- The script extracts visible text only. It may not capture dynamically loaded content or text embedded within JavaScript.

- The spell checker may not catch all spelling mistakes, especially for words with unusual capitalization or formatting.

- Crawling large websites may consume significant resources and time. Use caution when setting the `MAX_DEPTH` and `MAX_REQUESTS` parameters.

## Contributions

Contributions to the project are welcome! Feel free to fork the repository, make improvements, and submit pull requests.

If you encounter any issues or have suggestions for improvement, please open an issue on GitHub.

