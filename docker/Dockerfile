FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ \
    tesseract-ocr \
    ffmpeg \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy application
COPY . .

# Build legal database
RUN python scripts/build_legal_database.py

# Expose port (Render passes $PORT at runtime)
EXPOSE 10000

# Start API — PORT env var injected by Render
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
