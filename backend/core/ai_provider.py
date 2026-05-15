"""
AIProviderWrapper — thin adapter over Ollama/OpenAI/Anthropic/Azure.
Rate limiting: 60 req/min sliding window.
Retry: exponential backoff, 3 attempts.
Embedding cache: module-level dict (reset on process restart).
"""
from __future__ import annotations
import time
import threading
from collections import deque
from typing import Optional

from core.config import ModelConfig, AIProvider


class AIProviderError(Exception):
    pass


class AIProviderWrapper:
    # Module-level cache — shared across all instances in the same process.
    _EMBED_CACHE: dict[str, list[float]] = {}

    def __init__(self, config):
        """config is an AIConfig Pydantic model."""
        self.model_config    = ModelConfig.from_ai_config(config)
        self.request_timeout = config.request_timeout
        self._rate_limit_window = 60
        self._rate_limit_max    = 60
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        self.max_retries  = 3
        self.retry_delay  = 1.0
        self._client      = None

    # ── client ──────────────────────────────────────────────────────────────

    def _get_client(self):
        if self._client is None:
            self._client = self.model_config.get_client()
        return self._client

    # ── rate limiting ────────────────────────────────────────────────────────

    def _check_rate_limit(self):
        with self._lock:
            now = time.time()
            while self._timestamps and self._timestamps[0] < now - self._rate_limit_window:
                self._timestamps.popleft()
            if len(self._timestamps) >= self._rate_limit_max:
                raise AIProviderError("Rate limit exceeded (60 req/min)")
            self._timestamps.append(now)

    def _retry(self, fn, *args, **kwargs):
        self._check_rate_limit()
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                return fn(*args, **kwargs)
            except AIProviderError:
                raise
            except Exception as e:
                last_exc = e
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        raise AIProviderError(f"Failed after {self.max_retries} attempts: {last_exc}")

    # ── chat ─────────────────────────────────────────────────────────────────

    def generate_chat_response(self, messages: list[dict]) -> str:
        return self._retry(self._do_chat, messages)

    def _do_chat(self, messages: list[dict]) -> str:
        client   = self._get_client()
        provider = self.model_config.provider

        if provider == AIProvider.OLLAMA:
            response = client.chat(
                model=self.model_config.chat_model,
                messages=messages,
                options={"num_predict": 200},
            )
            return response["message"]["content"].strip()

        elif provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI):
            model = (
                self.model_config.azure_deployment
                if provider == AIProvider.AZURE_OPENAI and self.model_config.azure_deployment
                else self.model_config.chat_model
            )
            response = client.chat.completions.create(
                model=model, messages=messages, max_tokens=200
            )
            return response.choices[0].message.content.strip()

        elif provider == AIProvider.ANTHROPIC:
            system = next(
                (m["content"] for m in messages if m["role"] == "system"), None
            )
            user_messages = [m for m in messages if m["role"] != "system"]
            kwargs: dict = {
                "model": self.model_config.chat_model,
                "max_tokens": 200,
                "messages": user_messages,
            }
            if system:
                kwargs["system"] = system
            response = client.messages.create(**kwargs)
            return response.content[0].text.strip()

        raise AIProviderError(f"Chat not supported for provider: {provider}")

    # ── embeddings ───────────────────────────────────────────────────────────

    def generate_embedding(self, text: str) -> list[float]:
        if text in self._EMBED_CACHE:
            return self._EMBED_CACHE[text]
        result = self._retry(self._do_embed_single, text)
        self._EMBED_CACHE[text] = result
        return result

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Single API call for OpenAI/Azure; per-item loop for Ollama."""
        uncached = [t for t in texts if t not in self._EMBED_CACHE]
        if uncached:
            provider = self.model_config.provider
            if provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI):
                embeddings = self._retry(self._do_embed_batch_openai, uncached)
                for t, emb in zip(uncached, embeddings):
                    self._EMBED_CACHE[t] = emb
            else:
                for t in uncached:
                    self._EMBED_CACHE[t] = self._retry(self._do_embed_single, t)
        return [self._EMBED_CACHE[t] for t in texts]

    def _do_embed_single(self, text: str) -> list[float]:
        client   = self._get_client()
        provider = self.model_config.provider

        if provider == AIProvider.OLLAMA:
            response = client.embeddings(
                model=self.model_config.embedding_model, prompt=text
            )
            return response["embedding"]

        elif provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI):
            response = client.embeddings.create(
                model=self.model_config.embedding_model, input=[text]
            )
            return response.data[0].embedding

        elif provider == AIProvider.ANTHROPIC:
            raise NotImplementedError(
                "Anthropic does not have an embeddings API. "
                "Configure a separate OpenAI or Ollama provider for embeddings."
            )

        raise AIProviderError(f"Embeddings not supported for provider: {provider}")

    def _do_embed_batch_openai(self, texts: list[str]) -> list[list[float]]:
        client   = self._get_client()
        response = client.embeddings.create(
            model=self.model_config.embedding_model, input=texts
        )
        return [e.embedding for e in response.data]

    # ── connection validation ────────────────────────────────────────────────

    def validate_connection(self) -> tuple[bool, str]:
        try:
            client   = self._get_client()
            provider = self.model_config.provider

            if provider == AIProvider.OLLAMA:
                models_resp = client.list()
                items = models_resp.get("models") if isinstance(models_resp, dict) else getattr(models_resp, "models", None) or []
                available: list[str] = []
                for m in (items or []):
                    n = (m.get("model") or m.get("name")) if isinstance(m, dict) else (getattr(m, "model", None) or getattr(m, "name", None))
                    if n:
                        available.append(str(n))
                return True, f"Connected to Ollama. {len(available)} model(s) available."

            elif provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI):
                self._do_embed_single("test")
                name = "OpenAI" if provider == AIProvider.OPENAI else "Azure OpenAI"
                return True, (
                    f"Connected to {name}. "
                    f"Chat model: {self.model_config.chat_model}. "
                    f"Embedding model: {self.model_config.embedding_model}."
                )

            elif provider == AIProvider.ANTHROPIC:
                self._do_chat([{"role": "user", "content": "Hi"}])
                return True, (
                    f"Connected to Anthropic. "
                    f"Chat model: {self.model_config.chat_model}."
                )

        except Exception as e:
            return False, f"Connection failed: {e}"

        return False, "Unknown error during connection test"
