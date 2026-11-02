# Dockerfile for Chat With Documents Frontend

FROM python:3.11-slim

LABEL maintainer="Chat With Documents"
LABEL description="Streamlit frontend for RAG system"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend
COPY ../backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 streamlit && chown -R streamlit:streamlit /app
USER streamlit

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Expose port
EXPOSE 8501

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_SERVER_RUN_ON_SAVE=false
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Run Streamlit
CMD ["streamlit", "run", "app.py"]
