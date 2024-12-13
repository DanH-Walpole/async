# SearchApp

A web application that performs intelligent web searches and provides summarized answers using AI.

## Project Structure

```
src/searchapp/
├── api/                    # API controllers and endpoints
│   └── controller.py       # Main input controller
├── core/                   # Core business logic
│   ├── inference/         # AI inference functionality
│   │   └── inference.py   # Inference engine
│   ├── pdf/              # PDF processing
│   │   └── document.py   # PDF document handler
│   └── search/           # Search functionality
│       ├── bing.py       # Bing search implementation
│       └── web.py        # Web search functionality
├── utils/                 # Utility functions and helpers
│   └── caching.py        # Redis caching implementation
└── web/                  # Web interfaces
    ├── dash_app.py       # Dash web interface
    └── flask_app.py      # Flask web interface
```

## Features

- Web search using Bing API
- PDF document processing
- AI-powered answer generation
- Result caching with Redis
- Multiple web interfaces (Flask and Dash)

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```

3. Set up environment variables:
   - `BING_SEARCH_V7_WEB_SEARCH_SUBSCRIPTION_KEY`: Your Bing Search API key
   - `OPENAI_API_KEY`: Your OpenAI API key

## Usage

### Flask Web Interface

```bash
python -m searchapp.web.flask_app
```

### Dash Web Interface

```bash
python -m searchapp.web.dash_app
```

## Development

The project follows a modular structure:

- `api/`: Contains the main controller that handles input processing and orchestrates the search and inference process
- `core/`: Contains the core business logic split into different domains:
  - `inference/`: Handles AI inference using OpenAI's API
  - `pdf/`: Handles PDF document processing with multiple backend options
  - `search/`: Handles web searching using Bing's API
- `utils/`: Contains utility functions, currently focused on Redis caching
- `web/`: Contains web interfaces implemented in both Flask and Dash

## Dependencies

- Flask/Dash for web interfaces
- BeautifulSoup4 for web scraping
- PyPDF2, pdfminer, pdfplumber, pymupdf for PDF processing
- Redis for caching
- aiohttp for async HTTP requests
- OpenAI API for inference
- Bing Web Search API for search