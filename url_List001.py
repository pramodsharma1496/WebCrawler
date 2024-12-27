import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Function to extract URLs from a given page
def extract_urls(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Extract and normalize URLs
        return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
    except requests.RequestException as e:
        print(f"Error accessing URL {url}: {e}")
        return []

# Function to recursively crawl and log URLs
def crawl_and_log(url, visited, writer, max_depth, current_depth=0):
    if current_depth > max_depth or url in visited:
        return

    visited.add(url)
    print(f"Crawling: {url}")

    try:
        child_urls = extract_urls(url)
        for child_url in child_urls:
            child_url = child_url.split('#')[0]  # Remove fragments
            parsed_url = urlparse(child_url)
            # Only process URLs from the same domain
            if child_url.startswith(f"{parsed_url.scheme}://{parsed_url.netloc}") and child_url not in visited:
                writer.writerow([url, child_url])  # Log parent-child relationship
                crawl_and_log(child_url, visited, writer, max_depth, current_depth + 1)
    except Exception as e:
        print(f"Error processing URL {url}: {e}")

# Main function
def main(input_csv, output_csv, max_depth):
    visited = set()

    try:
        with open(input_csv, 'r') as file, open(output_csv, 'w', newline='', encoding='utf-8') as outfile:
            reader = csv.reader(file)
            writer = csv.writer(outfile)
            writer.writerow(["URL", "Sub URL"])  # Write CSV headers

            for row in reader:
                starting_url = row[0].strip()
                print(f"Starting crawl from: {starting_url}")
                crawl_and_log(starting_url, visited, writer, max_depth)
    except FileNotFoundError:
        print(f"Error: File '{input_csv}' not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

# Example usage
if __name__ == "__main__":
    input_csv = "urls.csv"  # Input CSV file containing starting URLs
    output_csv = "output_urls.csv"  # Output CSV file to save results
    max_depth = 2  # Maximum crawl depth
    main(input_csv, output_csv, max_depth)
