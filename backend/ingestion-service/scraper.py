import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("Scraper")

def scrape(url):
    logger.info(f"Surgically extracting content from: {url}")
    res = requests.get(url, timeout=15)
    soup = BeautifulSoup(res.text, "html.parser")

    # 1. Data Cleaning: Decompose noise/boilerplate
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
        tag.decompose()

    # 2. Metadata Extraction: Get Title
    title = soup.title.string.strip() if soup.title else "Untitled Page"

    # 3. Content Targeting: Fallback from main -> article -> body
    main_content = soup.find("main") or soup.find("article") or soup.find("body")
    
    if not main_content:
        return {"text": "", "title": title}

    text = main_content.get_text(" ")
    clean_text = " ".join(text.split())
    
    logger.debug(f"Successfully scraped '{title}' ({len(clean_text)} chars)")
    return {"text": clean_text, "title": title}
