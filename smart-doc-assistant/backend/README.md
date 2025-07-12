# Smart Document Assistant Backend

## Setup
1. Copy `.env.example` to `.env`
2. Add your Gemini API key to `.env`
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python main.py`

## Endpoints
- POST /upload - Upload PDF/Excel file
- POST /ask - Ask questions about uploaded document
- GET /health - Health check
