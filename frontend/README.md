# Chat With Documents – Frontend (Streamlit)

A modern, user-friendly web interface for the RAG system built with Streamlit.

## Features

### 💬 Chat Interface
- Ask natural language questions about indexed documents
- Real-time AI-powered responses using local LLMs
- View source citations with document names and page numbers
- Chat history for quick access to previous questions

### 📤 Document Upload
- Drag-and-drop PDF upload
- File size and format validation
- Real-time upload progress
- Automatic text extraction and indexing

### 📋 Document Management
- View all indexed documents and statistics
- Delete documents with confirmation
- Track chunk count and page numbers
- Monitor total indexed content

### ⚙️ System Settings
- API configuration and health status
- LLM model and embedding information
- System resource metrics
- Service status indicators

### 📊 Analytics (Phase 7+)
- Query statistics and trends
- Document upload history
- Performance metrics
- Response time tracking

### 🎯 Demo & Examples
- Interactive tutorials
- Example queries
- Best practices guide
- FAQ section

## Installation

### Prerequisites

- Python 3.11+ (tested on 3.13.9)
- Backend API running (Phase 5)
- Backend dependencies installed

### Setup

1. **Install frontend dependencies:**

```bash
pip install streamlit httpx
```

Or use the full requirements:

```bash
pip install -r ../requirements.txt
```

2. **Configure environment (optional):**

```bash
cp .env.example .env
# Edit .env to customize API_URL if needed
```

3. **Run the frontend:**

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

## Usage

### Uploading Documents

1. Navigate to the **Upload** tab
2. Click "Choose a PDF file" or drag-and-drop
3. Select a PDF document (max 10MB, 100 pages)
4. Click "Upload & Index"
5. Wait for processing to complete

**The system will:**
- Extract text from the PDF
- Split into chunks for semantic search
- Generate embeddings
- Index in the vector store

### Asking Questions

1. Go to the **Chat** tab
2. Enter your question in the text area
3. Click "Ask" or press Ctrl+Enter
4. Review the generated answer
5. Check source references for accuracy

**Best practices:**
- Ask specific questions
- Use relevant keywords from documents
- Ask follow-up questions to refine results
- Always verify sources

### Managing Documents

1. Navigate to the **Documents** tab
2. View indexed documents and statistics
3. Click 🗑️ to delete a document
4. Confirm deletion in the dialog
5. Refresh to see updated list

### Checking System Status

1. Go to the **Settings** tab
2. Review API configuration
3. Check service health indicators
4. View system settings and limits
5. Monitor resource usage

## Architecture

```
Streamlit Frontend (Port 8501)
    ↓
APIClient (httpx)
    ↓
FastAPI Backend (Port 8000)
    ↓
RAG Services (Phase 1-4)
```

## File Structure

```
frontend/
├── app.py                 # Main Streamlit application
├── api_client.py          # API communication client
├── utils.py               # Utility functions
├── __init__.py            # Package marker
├── .streamlit/
│   └── config.toml        # Streamlit configuration
├── pages/
│   ├── demo.py            # Demo and tutorials
│   └── analytics.py       # Analytics dashboard
├── .env.example           # Environment template
└── README.md              # This file
```

## Configuration

### Environment Variables

```bash
# Backend API URL
API_URL=http://localhost:8000

# Streamlit settings
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
STREAMLIT_SERVER_RUN_ON_SAVE=true

# Disable telemetry (optional)
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
```

### Streamlit Config

Edit `.streamlit/config.toml` to customize:

```toml
[theme]
primaryColor = "#1f77b4"       # Primary accent color
backgroundColor = "#ffffff"    # Main background
secondaryBackgroundColor = "#f0f2f6"  # Secondary background
textColor = "#262730"          # Text color
font = "sans serif"            # Font family

[client]
showErrorDetails = true        # Show full error messages

[server]
port = 8501                    # Port to run on
maxUploadSize = 10             # Max upload in MB
```

## API Integration

The frontend communicates with the backend API using the `APIClient` class.

### Key Endpoints Used

```python
# Document Management
POST   /api/v1/documents/upload          # Upload PDF
GET    /api/v1/documents                 # List documents
DELETE /api/v1/documents/{document_id}   # Delete document

# Chat/QA
POST   /api/v1/chat                      # Ask question

# Health
GET    /api/v1/health                    # Check system status
```

### Example API Calls

```python
from api_client import APIClient

client = APIClient("http://localhost:8000")

# Upload document
response = client.upload_document(file_obj)
print(response)  # {'document_id': '...', 'filename': '...', ...}

# Ask question
response = client.ask_question("What is machine learning?")
print(response)  # {'query': '...', 'answer': '...', 'sources': [...]}

# List documents
response = client.list_documents()
print(response)  # {'documents': [...], 'count': 150}

# Check health
response = client.check_health()
print(response)  # {'status': 'healthy', 'services': {...}}
```

## Error Handling

The frontend gracefully handles common errors:

- **Connection errors** - Shows "Could not connect to API" message
- **Upload errors** - Displays specific validation errors
- **Query errors** - Shows error messages with helpful suggestions
- **Timeout errors** - Indicates LLM may be processing

### Debugging

Enable debug mode:

```bash
streamlit run app.py --logger.level=debug
```

Check Streamlit logs:

```bash
# Terminal output shows debug information
# Look for [datetime] [thread_name] [streamlit_module.py:line] [level] Message
```

## Performance Tips

1. **Optimize document uploads**
   - Use smaller PDFs when possible
   - Remove unnecessary images/fonts
   - Keep documents focused on single topics

2. **Improve query speed**
   - Use specific keywords
   - Ask clear, focused questions
   - Avoid very broad queries

3. **System optimization**
   - Run backend and frontend on same machine
   - Use GPU for embeddings if available
   - Allocate sufficient RAM (16GB+ recommended)

## Troubleshooting

### "Could not connect to API"
```bash
# Check if backend is running
curl http://localhost:8000/

# If not running, start it:
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### "LLM model not found"
```bash
# Ensure Ollama is running and model is available
ollama serve
ollama pull qwen2.5:3b
```

### Slow upload
- Check file size (max 10MB)
- Verify internet connection
- Try smaller PDF file
- Check backend logs for errors

### Incorrect answers
- Verify source documents are relevant
- Check if context is sufficient (⚠️ indicator)
- Try more specific questions
- Review source references for accuracy

## Development

### Adding New Features

1. **Add new page:**
```bash
# Create pages/feature.py
st.set_page_config(page_title="Feature", page_icon="🎯")
# ... page code
```

2. **Add new API endpoint:**
```python
# In api_client.py
def new_endpoint(self) -> dict:
    return self._make_request("GET", "/api/v1/endpoint")
```

3. **Update UI:**
- Edit `app.py` for main interface changes
- Update `.streamlit/config.toml` for theme changes

### Testing

```bash
# Test API connectivity
python -c "from api_client import APIClient; c = APIClient(); print(c.check_health())"

# Run with verbose logging
streamlit run app.py --logger.level=debug --client.showErrorDetails=true
```

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY frontend .

EXPOSE 8501

CMD ["streamlit", "run", "app.py"]
```

### Docker Compose

```yaml
services:
  frontend:
    build: ./frontend
    ports:
      - "8501:8501"
    environment:
      API_URL: http://backend:8000
    depends_on:
      - backend
```

## Performance Characteristics

### Response Times
- **Document Upload**: 1-30s (depends on file size)
- **Semantic Search**: ~200ms (retrieval)
- **LLM Generation**: 2-5s (depends on model)
- **Total Q&A Time**: 2-5s average

### Resource Usage
- **Memory**: ~100-200MB (Streamlit process)
- **CPU**: Variable (depends on concurrent users)
- **Storage**: Minimal (no local storage)

## Known Limitations

- Phase 6 limitations:
  - Single-session storage (no persistence)
  - No user authentication
  - No rate limiting
  - Chat history not saved between sessions
  - Analytics are session-only

- Future phases (7-8):
  - Phase 7: Database integration for persistence
  - Phase 8: Multi-user support with authentication

## License

Same as main project

## Support

- 📚 [Documentation](README.md)
- 💬 [Discussions](https://github.com/yourusername/chat-with-documents)
- 🐛 [Report Issues](https://github.com/yourusername/chat-with-documents/issues)

## Version

Phase 6 Frontend - v0.1.0

**Last Updated:** November 2026
