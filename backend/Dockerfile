FROM python:3.12-slim

WORKDIR /app

# gcc/build-essential: some deps (e.g. clevercsv) may need to build from
# source on architectures without a prebuilt wheel (notably arm64/Apple Silicon).
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential gosu \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY data/ ./data/

# The container starts as root only to fix the ownership of the data folders,
# then docker/backend-entrypoint.sh runs the app as an ordinary user (gosu).
# sed strips Windows line endings, which would stop the script from running.
COPY docker/backend-entrypoint.sh /usr/local/bin/backend-entrypoint.sh
RUN sed -i 's/\r$//' /usr/local/bin/backend-entrypoint.sh \
    && chmod +x /usr/local/bin/backend-entrypoint.sh

EXPOSE 8000

# No --reload: this is the packaged runtime, not the dev server (dev still
# uses run_backend.py, which keeps its file-watcher for local iteration).
ENTRYPOINT ["/usr/local/bin/backend-entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
