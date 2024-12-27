import csv
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Define the target keywords
KEYWORDS = {
    'inventore', 'biophilia', 'ircs', 'enim', 'beatae', 'quaed', 'dolorem',
    'aelltes', 'veritatis', 'architecto', 'wharehouses', 'finibus', 'activties',
    'gilla', 'quis', 'turpis', 'quia', 'thalassemia', 'neque', 'centre', 'amet',
    'lacus', 'counselling', 'ipsum', 'lorem', 'programme', 'sunt', 'porro',
    'efficitur'
}

# Function to extract URLs from a page
def extract_urls(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        return [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)], soup.get_text()
    except requests.RequestException as e:
        print(f"Error accessing URL {url}: {e}")
        return [], ""

# Function to check if the text contains any of the target keywords
def contains_keywords(text):
    words = set(text.lower().split())
    return not KEYWORDS.isdisjoint(words)

# Function to recursively crawl and log URLs
def crawl_and_log(url, visited, writer, max_depth, current_depth=0):
    if current_depth > max_depth or url in visited:
        return

    visited.add(url)
    print(f"Crawling: {url}")

    try:
        child_urls, page_text = extract_urls(url)
        if contains_keywords(page_text):  # Check if the page text contains keywords
            for child_url in child_urls:
                child_url = child_url.split('#')[0]  # Remove fragments
                parsed_url = urlparse(child_url)
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
    output_csv = "filtered_urls.csv"  # Output CSV file to save results
    max_depth = 2  # Maximum crawl depth
    main(input_csv, output_csv, max_depth)
