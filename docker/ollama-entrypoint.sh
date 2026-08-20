#!/bin/sh
# Starts the real Ollama server, waits until it's responding, then pulls the
# chat + embedding models if they aren't already in the (persisted) model
# cache. First `docker compose up` pays this cost once; every run after that
# is a no-op pull check against an already-populated volume.
set -e

CHAT_MODEL="${OLLAMA_DEFAULT_CHAT_MODEL:-llama3.2:3b}"
EMBEDDING_MODEL="${OLLAMA_DEFAULT_EMBEDDING_MODEL:-nomic-embed-text}"

ollama serve &
SERVE_PID=$!

echo "[ollama-entrypoint] waiting for ollama to become ready..."
until ollama list >/dev/null 2>&1; do
  sleep 1
done
echo "[ollama-entrypoint] ollama is ready."

echo "[ollama-entrypoint] pulling chat model: $CHAT_MODEL"
ollama pull "$CHAT_MODEL"

echo "[ollama-entrypoint] pulling embedding model: $EMBEDDING_MODEL"
ollama pull "$EMBEDDING_MODEL"

echo "[ollama-entrypoint] models ready — serving."
wait "$SERVE_PID"
