import csv
import threading
import time
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
import requests
from bs4 import BeautifulSoup
from spellchecker import SpellChecker
from urllib.parse import urlparse, urljoin
from datetime import datetime

# Configuration for URL skipping
SKIP_EXACT_URLS = {                  # URLs to ignore completely
    # "https://example.com/skip-this-page",
}
SKIP_SUBSTRINGS = [                  # Substrings that, if present in a URL, will cause it to be skipped
    # "logout",
    # "register",
    # "ignore",
    "/ircsjkbranch@gmail.com",
    "pdf",
    "/ircs@indianredcross.org"
]

# Initialize spell checker once
spell = SpellChecker()

# Global list for storing spelling mistakes results
# Each entry is a tuple: (url, comma_separated_misspelled_words)
results = []
results_lock = threading.Lock()

# Global variables for loader
progress = 0
loader_done = False
progress_lock = threading.Lock()


def should_skip_url(url):
    """
    Returns True if the URL should be skipped based on exact matches or contained substrings.
    """
    if url in SKIP_EXACT_URLS:
        return True
    for substring in SKIP_SUBSTRINGS:
        if substring in url:
            return True
    return False


def extract_urls_and_text(session, url):
    """Extract all URLs and text from the given URL using a persistent session."""
    try:
        response = session.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise Exception(f"Request error: {e}") from e

    soup = BeautifulSoup(response.content, 'html.parser')
    # Get absolute URLs from relative links
    urls = [urljoin(url, link.get('href')) for link in soup.find_all('a', href=True)]
    text = soup.get_text(separator=' ', strip=True)
    return urls, text


def spell_check(text):
    """Check for spelling mistakes in text, skipping short words and non-alphabetic words."""
    words = text.split()
    filtered_words = [word for word in words if len(word) > 3 and word.isalpha()]
    return spell.unknown(filtered_words)


def worker(session, queue, visited_lock, visited, max_depth):
    """Worker thread to process URLs from the queue."""
    while True:
        item = queue.get()
        if item is None:  # Termination signal
            queue.task_done()
            break

        url, prefix, current_depth = item

        # Skip processing if beyond max depth
        if current_depth > max_depth:
            queue.task_done()
            continue

        # Skip URL if it matches skip conditions
        if should_skip_url(url):
            queue.task_done()
            continue

        # Thread-safe visited check
        with visited_lock:
            if url in visited:
                queue.task_done()
                continue
            visited.add(url)

        try:
            # Extract content and check spelling
            urls, text = extract_urls_and_text(session, url)
            misspelled = spell_check(text)
            if misspelled:
                # Save result without printing to the command line.
                with results_lock:
                    results.append((url, ', '.join(misspelled)))

            # Enqueue valid child URLs
            next_depth = current_depth + 1
            if next_depth <= max_depth:
                for next_url in urls:
                    # Ensure URL starts with the same prefix and does not match skip conditions
                    if next_url.startswith(prefix) and not should_skip_url(next_url):
                        queue.put((next_url, prefix, next_depth))

        except Exception as e:
            # Errors can be logged here if needed
            pass

        queue.task_done()


def loader():
    """Simulated loader that updates progress from 1% to 100%."""
    global progress, loader_done
    while not loader_done:
        with progress_lock:
            if progress < 99:
                progress += 1
            print(f"\rProgress: {progress}%", end="", flush=True)
        time.sleep(0.1)
    # Once done, ensure progress is set to 100%
    with progress_lock:
        progress = 100
        print(f"\rProgress: {progress}%")


def main(csv_file, max_depth):
    """Main crawling controller with concurrent workers and a loader."""
    visited = set()
    visited_lock = threading.Lock()
    url_queue = Queue()

    # Initialize queue with starting URLs from CSV file
    with open(csv_file, 'r') as file:
        reader = csv.reader(file)
        for row in reader:
            if not row:
                continue
            starting_url = row[0].strip()
            parsed = urlparse(starting_url)
            if not parsed.scheme or not parsed.netloc:
                continue  # Skip invalid URLs
            prefix = f"{parsed.scheme}://{parsed.netloc}"
            # Also apply skip rules to starting URLs
            if should_skip_url(starting_url):
                continue
            url_queue.put((starting_url, prefix, 0))

    num_workers = 15  # Optimal for I/O-bound tasks

    # Start the loader thread
    loader_thread = threading.Thread(target=loader)
    loader_thread.start()

    # Use a ThreadPoolExecutor for worker threads.
    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        # Create a separate session for each worker.
        sessions = [requests.Session() for _ in range(num_workers)]

        # Start worker threads.
        futures = [executor.submit(worker, session, url_queue, visited_lock, visited, max_depth)
                   for session in sessions]

        # Wait until all tasks in the queue are processed.
        url_queue.join()

        # Signal termination to workers.
        for _ in range(num_workers):
            url_queue.put(None)
        executor.shutdown(wait=True)

    # Stop the loader.
    global loader_done
    loader_done = True
    loader_thread.join()

    # Generate a file name based on date and timestamp.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"spelling_mistakes_{timestamp}.csv"

    # Write the spelling mistakes to a CSV file.
    with open(output_filename, "w", newline="", encoding="utf-8") as outfile:
        writer = csv.writer(outfile)
        writer.writerow(["URL", "Misspelled Words"])
        with results_lock:
            for url, misspelled in results:
                writer.writerow([url, misspelled])


if __name__ == "__main__":
    main("urls.csv", max_depth=3)
