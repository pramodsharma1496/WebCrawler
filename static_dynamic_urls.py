import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def extract_urls(url):
    """Extract URLs from a given webpage."""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
    except requests.RequestException as e:
        print(f"Error accessing URL {url}: {e}")
        return []

def crawl_and_filter_urls(start_url, static_domains, ignore_urls, writer, visited, processed_urls, max_depth, current_depth=0):
    """Crawl URLs and log only those with non-matching static domains, excluding ignored or duplicate URLs."""
    if current_depth > max_depth or start_url in visited:
        return

    visited.add(start_url)
    print(f"Crawling: {start_url}")

    try:
        child_urls = extract_urls(start_url)
        for child_url in child_urls:
            if child_url in processed_urls:
                continue
            processed_urls.add(child_url)  # Mark URL as processed

            if any(ignore_url in child_url for ignore_url in ignore_urls):
                continue
            if not any(static_domain in child_url for static_domain in static_domains):
                writer.writerow([start_url, child_url])
            if child_url not in visited:
                crawl_and_filter_urls(child_url, static_domains, ignore_urls, writer, visited, processed_urls, max_depth, current_depth + 1)
    except Exception as e:
        print(f"Error processing URL {start_url}: {e}")

def main(input_csv, output_csv, static_domains, ignore_urls, max_depth):
    """Main function to start the crawling and filtering process."""
    visited = set()
    processed_urls = set()

    try:
        with open(input_csv, 'r') as infile, open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            reader = csv.reader(infile)
            writer = csv.writer(outfile)
            writer.writerow(["Web Page URL", "Detected URL"])  # Write CSV headers

            for row in reader:
                start_url = row[0].strip()
                print(f"Starting crawl from: {start_url}")
                crawl_and_filter_urls(start_url, static_domains, ignore_urls, writer, visited, processed_urls, max_depth)
    except FileNotFoundError:
        print(f"Error: File '{input_csv}' not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    input_csv = "urls.csv"  # Input file with starting URLs
    output_csv = "filtered_urls.csv"  # Output file for filtered URLs
    static_domains = ["https://dev-admin-panel.azurewebsites.net"]  # List of static domains to exclude
    ignore_urls = ["https://example.com/ignore"]  # List of URLs to ignore
    max_depth = 2  # Maximum crawl depth

    main(input_csv, output_csv, static_domains, ignore_urls, max_depth)
