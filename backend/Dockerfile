FROM python:3.12-slim

WORKDIR /app

# gcc/build-essential: some deps (e.g. clevercsv) may need to build from
# source on architectures without a prebuilt wheel (notably arm64/Apple Silicon).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY data/ ./data/

EXPOSE 8000

# No --reload: this is the packaged runtime, not the dev server (dev still
# uses run_backend.py, which keeps its file-watcher for local iteration).
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
