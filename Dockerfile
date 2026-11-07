FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Tesseract with Russian reads scans locally: nothing leaves the server
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The embedding model is baked into the image: no download at start, no outside calls at run time
COPY scripts/download_model.py scripts/
RUN python scripts/download_model.py

COPY app app
COPY knowledge knowledge
COPY examples examples
COPY web web

# Files stay root's and read-only: the app writes nothing to disk, uploads and reports live in memory
RUN useradd --system --uid 1000 app
USER app

EXPOSE 8000
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
