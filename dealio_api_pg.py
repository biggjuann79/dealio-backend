from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from postgres_db import fetch_top_deals, init_db, test_connection
import logging
import traceback

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(**name**)

app = FastAPI(
title=“Dealio API”,
description=“API for finding the best deals from Craigslist”,
version=“1.0.0”
)

app.add_middleware(
CORSMiddleware,
allow_origins=[”*”],  # In production, replace with specific domains
allow_credentials=True,
allow_methods=[“GET”, “POST”, “PUT”, “DELETE”],
allow_headers=[”*”],
)

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
logger.error(f”Global exception: {str(exc)}”)
logger.error(f”Traceback: {traceback.format_exc()}”)
return JSONResponse(
status_code=500,
content={“success”: False, “error”: “Internal server error”, “detail”: str(exc)}
)

@app.on_event(“startup”)
async def startup_event():
“”“Initialize database on startup”””
try:
logger.info(“Starting up Dealio API…”)
init_db()
logger.info(“Database initialized successfully”)
except Exception as e:
logger.error(f”Startup failed: {e}”)
# Don’t raise here, let the app start but handle errors in endpoints

@app.get(”/”)
def root():
“”“Root endpoint with API information”””
return {
“message”: “Dealio API is live”,
“version”: “1.0.0”,
“endpoints”: {
“/deals”: “Get filtered deals”,
“/health”: “Health check”,
“/test-db”: “Test database connection”
}
}

@app.get(”/health”)
def health():
“”“Health check endpoint”””
try:
# Test database connection
if test_connection():
return {
“status”: “healthy”,
“database”: “connected”,
“timestamp”: “2025-06-30”
}
else:
raise HTTPException(status_code=503, detail=“Database connection failed”)
except Exception as e:
logger.error(f”Health check failed: {e}”)
raise HTTPException(status_code=503, detail=f”Service unhealthy: {str(e)}”)

@app.get(”/test-db”)
def test_db():
“”“Test database connection endpoint”””
try:
if test_connection():
return {“success”: True, “message”: “Database connection successful”}
else:
return {“success”: False, “message”: “Database connection failed”}
except Exception as e:
logger.error(f”Database test failed: {e}”)
raise HTTPException(status_code=500, detail=str(e))

@app.get(”/deals”)
def get_deals(
limit: int = Query(default=20, ge=1, le=100, description=“Number of deals to return”),
min_score: float = Query(default=0.0, ge=0.0, le=100.0, description=“Minimum deal score”)
):
“””
Get filtered deals from the database

```
- **limit**: Number of deals to return (1-100)
- **min_score**: Minimum deal score (0-100)
"""
try:
    logger.info(f"Fetching deals with limit={limit}, min_score={min_score}")
    results = fetch_top_deals(limit, min_score)
    
    response = {
        "success": True,
        "data": results,
        "count": len(results),
        "filters": {
            "limit": limit,
            "min_score": min_score
        }
    }
    
    logger.info(f"Successfully returned {len(results)} deals")
    return response
    
except Exception as e:
    logger.error(f"Error fetching deals: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise HTTPException(
        status_code=500, 
        detail=f"Failed to fetch deals: {str(e)}"
    )
```

@app.get(”/deals/categories”)
def get_categories():
“”“Get available categories”””
# This could be enhanced to query actual categories from database
return {
“success”: True,
“categories”: [“electronics”, “furniture”, “general”, “automotive”, “clothing”]
}

if **name** == “**main**”:
import uvicorn
uvicorn.run(app, host=“0.0.0.0”, port=8000)