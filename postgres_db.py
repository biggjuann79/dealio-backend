import os
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

def get_connection():
url = os.getenv(“DATABASE_URL”)
if not url:
# Fallback for local development
url = “postgresql://username:password@localhost:5432/dealio_db”
logger.warning(“DATABASE_URL not set, using local fallback”)

```
try:
    # Handle Railway/Heroku style URLs that might need sslmode adjustment
    if "railway" in url or "herokuapp" in url:
        if "sslmode" not in url:
            url += "?sslmode=require"
    
    conn = psycopg2.connect(url)
    logger.info("Database connection successful")
    return conn
except psycopg2.Error as e:
    logger.error(f"Database connection failed: {e}")
    raise Exception(f"Failed to connect to database: {e}")
```

def init_db():
try:
conn = get_connection()
cur = conn.cursor()

```
    # Drop and recreate table to ensure clean schema
    cur.execute("DROP TABLE IF EXISTS listings")
    
    cur.execute("""
        CREATE TABLE listings (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            price REAL DEFAULT 0.0,
            category TEXT DEFAULT 'general',
            deal_score REAL DEFAULT 0.0,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create index for better query performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_deal_score ON listings(deal_score DESC)")
    
    conn.commit()
    logger.info("Database initialized successfully")
    
    # Insert some test data if table is empty
    cur.execute("SELECT COUNT(*) FROM listings")
    count = cur.fetchone()[0]
    
    if count == 0:
        test_data = [
            {
                "id": "test_1",
                "title": "MacBook Pro 2021 - Excellent Condition",
                "price": 1200.0,
                "category": "electronics",
                "deal_score": 85.0,
                "url": "https://craigslist.org/test1"
            },
            {
                "id": "test_2", 
                "title": "iPhone 14 Pro Max Unlocked",
                "price": 800.0,
                "category": "electronics",
                "deal_score": 78.0,
                "url": "https://craigslist.org/test2"
            },
            {
                "id": "test_3",
                "title": "Herman Miller Office Chair",
                "price": 400.0,
                "category": "furniture",
                "deal_score": 92.0,
                "url": "https://craigslist.org/test3"
            }
        ]
        
        for listing in test_data:
            save_listing(listing)
        logger.info("Test data inserted")
    
    cur.close()
    conn.close()
    
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    raise
```

def save_listing(listing):
try:
conn = get_connection()
cur = conn.cursor()

```
    cur.execute("""
        INSERT INTO listings (id, title, price, category, deal_score, url)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            price = EXCLUDED.price,
            category = EXCLUDED.category,
            deal_score = EXCLUDED.deal_score,
            url = EXCLUDED.url,
            updated_at = CURRENT_TIMESTAMP
    """, (
        listing["id"], 
        listing["title"], 
        listing["price"],
        listing["category"], 
        listing["deal_score"], 
        listing["url"]
    ))
    
    conn.commit()
    cur.close()
    conn.close()
    logger.info(f"Saved listing: {listing['id']}")
    
except Exception as e:
    logger.error(f"Failed to save listing {listing.get('id', 'unknown')}: {e}")
    raise
```

def fetch_top_deals(limit=20, min_score=0.0):
try:
conn = get_connection()
cur = conn.cursor(cursor_factory=RealDictCursor)

```
    cur.execute("""
        SELECT id, title, price, category, deal_score, url
        FROM listings
        WHERE deal_score >= %s AND price > 0
        ORDER BY deal_score DESC, price ASC
        LIMIT %s
    """, (min_score, limit))
    
    results = []
    for row in cur.fetchall():
        results.append({
            "id": row["id"],
            "title": row["title"],
            "price": float(row["price"]) if row["price"] else 0.0,
            "category": row["category"] or "general",
            "deal_score": float(row["deal_score"]) if row["deal_score"] else 0.0,
            "url": row["url"]
        })
    
    cur.close()
    conn.close()
    logger.info(f"Fetched {len(results)} deals")
    return results
    
except Exception as e:
    logger.error(f"Failed to fetch deals: {e}")
    raise
```

def test_connection():
“”“Test database connectivity”””
try:
conn = get_connection()
cur = conn.cursor()
cur.execute(“SELECT version()”)
version = cur.fetchone()[0]
cur.close()
conn.close()
logger.info(f”Database test successful. PostgreSQL version: {version}”)
return True
except Exception as e:
logger.error(f”Database test failed: {e}”)
return False