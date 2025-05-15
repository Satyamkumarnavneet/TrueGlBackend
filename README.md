# TruthSearch API

A simple and efficient search engine API that can be easily deployed on Netlify. This API provides web crawling and search capabilities, with support for truth scoring integration.

## Features

- Fast and efficient web crawling with content extraction
- Simple SQLite-based search index
- RESTful API built with FastAPI
- Support for truth scoring integration
- Easy deployment on Netlify
- Asynchronous operations for better performance
- Content extraction with metadata support

## Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd search_api
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your configuration:
```env
# Server Configuration
PORT=8000
HOST=0.0.0.0
ENVIRONMENT=development

# Crawler Configuration
MAX_PAGES=1000
CRAWL_DELAY=1.0
MAX_DEPTH=3
MAX_RETRIES=3
TIMEOUT=30

# Allowed domains for crawling (comma-separated, leave empty to allow all domains)
ALLOWED_DOMAINS=

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

## Running the API

1. Start the API server:
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### Search
- **POST** `/search`
  - Search for documents
  - Request body:
    ```json
    {
        "query": "search terms",
        "page": 1,
        "per_page": 10,
        "filters": {}
    }
    ```

### Crawl
- **POST** `/crawl`
  - Start crawling from a URL
  - Request body:
    ```json
    {
        "url": "https://example.com",
        "max_pages": 1000
    }
    ```

### Update Truth Score
- **POST** `/update-truth-score`
  - Update the truth score for a document
  - Request body:
    ```json
    {
        "url": "https://example.com",
        "truth_score": 0.85
    }
    ```

### Stats
- **GET** `/stats`
  - Get API statistics
  - Returns:
    ```json
    {
        "document_count": 100,
        "last_crawl_time": "2024-01-01T12:00:00Z",
        "database_size": {
            "size_bytes": 1048576,
            "size_human": "1.0 MB"
        }
    }
    ```

### Health Check
- **GET** `/health`
  - Check API health
  - Returns:
    ```json
    {
        "status": "healthy",
        "timestamp": "2024-01-01T12:00:00Z",
        "version": "1.0.0"
    }
    ```

## Database

The search engine uses SQLite for storing and indexing documents. The database file (`search.db`) is created automatically when the API starts. The database schema includes:

- `documents` table: Stores document content and metadata
- `search_index` table: Stores searchable terms and their positions

## Crawler Features

- Asynchronous crawling for better performance
- Content extraction with metadata support
- URL validation and filtering
- Configurable crawl depth and delay
- Domain restrictions
- Automatic content type detection
- Error handling and retries

## Truth Scoring Integration

The API supports integration with truth scoring systems through the `/update-truth-score` endpoint. This allows you to:

1. Crawl and index web pages
2. Process documents with your truth scoring system
3. Update document truth scores
4. Use truth scores in search ranking

## Deployment on Netlify

To deploy on Netlify:

1. Create a `netlify.toml` file:
```toml
[build]
  command = "pip install -r requirements.txt"
  publish = "."

[[redirects]]
  from = "/*"
  to = "/.netlify/functions/api"
  status = 200

[functions]
  directory = "functions"
```

2. Create a serverless function in `functions/api.py`:
```python
from mangum import Mangum
from main import app

handler = Mangum(app)
```

3. Add `mangum` to your requirements:
```
mangum==0.17.0
```

4. Deploy to Netlify:
```bash
netlify deploy
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 