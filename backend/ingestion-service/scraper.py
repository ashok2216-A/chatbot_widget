import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("Scraper")

from urllib.parse import urljoin, urlparse

def find_internal_links(soup, base_url):
    domain = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"])
        # Only crawl internal links (same domain) and avoid anchors (#)
        if urlparse(url).netloc == domain and "#" not in url:
            links.add(url.split("?")[0].rstrip("/")) # Normalize
    return list(links)

def scrape(url):
    logger.info(f"Elite Scraping: {url}")
    try:
        res = requests.get(url, timeout=15)
        res.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to scrape {url}: {e}")
        return {"text": "", "title": "Error", "links": []}

    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Boilerplate Removal
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # 2. Extract Data
    title = soup.title.string.strip() if soup.title else "Untitled Page"
    
    # Target main content containers
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    text = main_content.get_text(" ") if main_content else ""
    clean_text = " ".join(text.split())

    # 3. Find Discovery Links
    links = find_internal_links(soup, url)
    
    logger.debug(f"Found {len(links)} internal links on '{title}'")
    return {"text": clean_text, "title": title, "links": links}
