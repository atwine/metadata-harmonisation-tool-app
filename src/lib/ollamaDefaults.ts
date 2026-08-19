// Overridable via VITE_* env vars so the Docker Compose package can point the
// UI's Ollama defaults at the bundled `ollama` service and a smaller default
// model, without changing the defaults for a normal local/manual setup.
export const OLLAMA_BASE_URL =
  (import.meta.env.VITE_OLLAMA_BASE_URL as string | undefined) ?? "http://localhost:11434";
export const OLLAMA_CHAT_MODEL =
  (import.meta.env.VITE_OLLAMA_CHAT_MODEL as string | undefined) ?? "llama3.1:8b";
export const OLLAMA_EMBEDDING_MODEL =
  (import.meta.env.VITE_OLLAMA_EMBEDDING_MODEL as string | undefined) ?? "nomic-embed-text";
