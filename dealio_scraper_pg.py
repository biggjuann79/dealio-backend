import requests
from bs4 import BeautifulSoup
from postgres_db import save_listing, init_db
import time
import random
import logging

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

HEADERS = {
“User-Agent”: “Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36”
}

CITIES = [
“newyork”, “losangeles”, “chicago”, “houston”, “phoenix”,
“philadelphia”, “sanantonio”, “sandiego”, “dallas”, “sanjose”
]

# Categories to search

CATEGORIES = {
“electronics”: “ela”,
“furniture”: “fua”,
“general”: “sss”,
“automotive”: “cta”
}

def calculate_deal_score(title, price):
“””
Calculate a deal score based on title keywords and price
This is a simple heuristic - you can make it more sophisticated
“””
score = 50.0  # Base score

```
# Keywords that indicate good deals
good_keywords = ["new", "mint", "excellent", "perfect", "unused", "sealed", "original"]
bad_keywords = ["broken", "damaged", "parts", "repair", "cracked"]

title_lower = title.lower()

# Boost score for good condition keywords
for keyword in good_keywords:
    if keyword in title_lower:
        score += 10

# Reduce score for bad condition keywords
for keyword in bad_keywords:
    if keyword in title_lower:
        score -= 20

# Price-based scoring (lower prices get higher scores within reason)
if price > 0:
    if price < 50:
        score += 20
    elif price < 200:
        score += 15
    elif price < 500:
        score += 10
    elif price > 2000:
        score -= 10

# Electronics boost
if any(term in title_lower for term in ["iphone", "macbook", "laptop", "phone", "computer"]):
    score += 15

# Ensure score is within bounds
return max(0.0, min(100.0, score))
```

def scrape_search_page(city, category=“sss”):
“”“Scrape a Craigslist search page for a given city and category”””
try:
base_url = f”https://{city}.craigslist.org/search/{category}”
logger.info(f”Scraping {city} - {category}: {base_url}”)

```
    response = requests.get(base_url, headers=HEADERS, timeout=15)
    response.raise_for_status()
    
    # Add delay to be respectful to Craigslist
    time.sleep(random.uniform(1, 3))
    
    return response.text
    
except requests.exceptions.RequestException as e:
    logger.error(f"Failed to scrape {city}/{category}: {e}")
    return None
```

def parse_and_save(city, category, html):
“”“Parse HTML and save listings to database”””
if not html:
return

```
soup = BeautifulSoup(html, "html.parser")

# Try different selectors for different Craigslist layouts
items = soup.select(".result-info") or soup.select("li.result-row")

if not items:
    logger.warning(f"No items found for {city}/{category}")
    return

saved_count = 0

for item in items:
    try:
        # Extract title
        title_elem = item.select_one(".result-title") or item.select_one("a.result-title-link")
        if not title_elem:
            continue
            
        title = title_elem.get_text(strip=True)
        if not title:
            continue
        
        # Extract price
        price_elem = item.select_one(".result-price")
        price = 0.0
        if price_elem:
            price_text = price_elem.get_text(strip=True).replace("$", "").replace(",", "")
            try:
                price = float(price_text)
            except ValueError:
                price = 0.0
        
        # Extract URL
        url = title_elem.get("href", "")
        if url and not url.startswith("http"):
            url = f"https://{city}.craigslist.org{url}"
        
        # Get post ID
        post_id = item.get("data-pid") or item.parent.get("data-pid", "no-id")
        if post_id == "no-id":
            # Try to extract from URL
            if "/d/" in url:
                post_id = url.split("/")[-1].split(".")[0]
            else:
                post_id = f"unknown_{hash(title + str(price))}"
        
        # Calculate deal score
        deal_score = calculate_deal_score(title, price)
        
        listing = {
            "id": f"{city}_{category}_{post_id}",
            "title": title[:255],  # Truncate if too long
            "price": price,
            "category": category,
            "deal_score": deal_score,
            "url": url
        }
        
        save_listing(listing)
        saved_count += 1
        
    except Exception as e:
        logger.error(f"Error parsing item in {city}/{category}: {e}")
        continue

logger.info(f"Saved {saved_count} listings from {city}/{category}")
```

def run_scraper():
“”“Main scraper function”””
logger.info(“Starting Dealio scraper…”)

```
try:
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    total_scraped = 0
    
    for city in CITIES:
        for category_name, category_code in CATEGORIES.items():
            logger.info(f"Scraping {city} - {category_name}")
            
            html = scrape_search_page(city, category_code)
            if html:
                parse_and_save(city, category_name, html)
                total_scraped += 1
            
            # Be respectful with delays
            time.sleep(random.uniform(2, 5))
    
    logger.info(f"Scraping completed. Processed {total_scraped} city/category combinations")
    
except Exception as e:
    logger.error(f"Scraper failed: {e}")
    raise
```

if **name** == “**main**”:
run_scraper()