import requests
from bs4 import BeautifulSoup
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from logger import get_logger

logger = get_logger("Scraper")

def scrape(url):
    logger.info(f"Extracting HTML structure from: {url}")
    res = requests.get(url, timeout=10)
    soup = BeautifulSoup(res.text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    text = soup.get_text(" ")
    return " ".join(text.split())
