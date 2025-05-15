from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging
import os
from datetime import datetime
from dotenv import load_dotenv
from search_service import BraveSearchService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Search API",
    description="A search engine API powered by Brave Search",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "https://truegl.netlify.app/"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search service
try:
    search_service = BraveSearchService()
    logger.info("Search service initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize search service: {str(e)}")
    raise

# Pydantic models
class SearchQuery(BaseModel):
    query: str
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=10, ge=1, le=50)
    filters: Optional[Dict[str, Any]] = None

class SearchResult(BaseModel):
    url: str
    title: str
    snippet: str
    score: float
    domain: str
    language: str
    metadata: Dict[str, Any]
    last_updated: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    per_page: int
    total_pages: int

class SuggestionsResponse(BaseModel):
    suggestions: List[str]

class ErrorResponse(BaseModel):
    error: str
    message: str
    detail: Optional[Dict[str, Any]] = None

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for all unhandled exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": str(exc),
            "detail": {"type": type(exc).__name__}
        }
    )

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Search API",
        "version": "1.0.0",
        "description": "A search engine API powered by Brave Search",
        "status": "operational",
        "endpoints": {
            "/search": "Search for documents",
            "/suggest": "Get search suggestions",
            "/health": "Check API health"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Test the search service with a simple query
        await search_service.search("test", page=1, per_page=1)
        return {
            "status": "healthy",
            "search_service": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Service unhealthy",
                "message": str(e),
                "component": "search_service"
            }
        )

@app.post("/search", response_model=SearchResponse, responses={500: {"model": ErrorResponse}})
async def search(query: SearchQuery):
    """Search endpoint using Brave Search API."""
    try:
        logger.info(f"Received search request: {query.query} (page {query.page})")
        
        if not query.query.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid query",
                    "message": "Search query cannot be empty"
                }
            )

        results = await search_service.search(
            query.query,
            page=query.page,
            per_page=query.per_page,
            filters=query.filters
        )
        
        logger.info(f"Search successful: found {results['total']} results")
        return SearchResponse(**results)
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Search error: {error_msg}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Search failed",
                "message": error_msg,
                "query": query.query
            }
        )

@app.get("/suggest", response_model=SuggestionsResponse, responses={500: {"model": ErrorResponse}})
async def get_suggestions(q: str = Query(..., min_length=2)):
    """Get search suggestions from Brave Search API."""
    try:
        suggestions = await search_service.get_suggestions(q)
        return SuggestionsResponse(suggestions=suggestions)
    except Exception as e:
        logger.error(f"Suggestions error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Suggestions failed",
                "message": str(e),
                "query": q
            }
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 8000)),
        reload=True,
        log_level="info"
    )