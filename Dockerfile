FROM python:3.11-slim

WORKDIR /app
# One thread for Tesseract: on one CPU it is faster (5 s for the scan instead of 8) and peaks at
# 160 MB instead of 220
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_THREAD_LIMIT=1

# Tesseract with Russian reads scans locally: nothing leaves the server
RUN apt-get update \
    && apt-get install -y --no-install-recommends tesseract-ocr tesseract-ocr-rus \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app app
COPY certs certs
COPY knowledge knowledge
COPY examples examples
COPY web web

# The examples are checked here, once: the service reads the results at start, so it starts at
# once and never loads the PDF, OCR and report libraries until a visitor sends a file
RUN python -m app.precompute --strict

# Files stay root's and read-only: the app writes nothing to disk, uploads and reports live in memory
RUN useradd --system --uid 1000 app
USER app

EXPOSE 8000
# One uvicorn process; each check runs in a child that exits after it (app/worker.py)
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--workers", "1"]
