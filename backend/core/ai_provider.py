"""
AIProviderWrapper — thin adapter over Ollama/vLLM/OpenAI/Anthropic/Azure.
Chat and embeddings are independent slots: each can point at a different
provider and server (e.g. chat via vLLM, embeddings via Ollama).
Rate limiting: 60 req/min sliding window.
Retry: exponential backoff, 3 attempts.
Embedding cache: module-level dict (reset on process restart).
"""
from __future__ import annotations
import time
import threading
from collections import deque
from typing import NamedTuple, Optional

from core.config import ModelConfig, AIProvider


class AIProviderError(Exception):
    pass


class SlotResult(NamedTuple):
    connected: bool
    message: str


class AIProviderWrapper:
    # Module-level cache — shared across all instances in the same process.
    _EMBED_CACHE: dict[str, list[float]] = {}

    def __init__(self, config):
        """config is an AIConfig Pydantic model with `.chat` and optional `.embedding` slots."""
        self.chat_config = ModelConfig.from_slot(config.chat, config.request_timeout)
        self.embedding_config = (
            ModelConfig.from_slot(config.embedding, config.request_timeout)
            if config.embedding is not None
            else None
        )
        self.request_timeout = config.request_timeout
        self._rate_limit_window = 60
        self._rate_limit_max    = 60
        self._timestamps: deque = deque()
        self._lock = threading.Lock()
        self.max_retries  = 3
        self.retry_delay  = 1.0
        self._chat_client  = None
        self._embed_client = None

    # ── clients ─────────────────────────────────────────────────────────────

    def _get_chat_client(self):
        if self._chat_client is None:
            self._chat_client = self.chat_config.get_client()
        return self._chat_client

    def _get_embed_client(self):
        if self.embedding_config is None:
            raise AIProviderError("No embedding model configured")
        if self._embed_client is None:
            self._embed_client = self.embedding_config.get_client()
        return self._embed_client

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
        client   = self._get_chat_client()
        provider = self.chat_config.provider

        if provider == AIProvider.OLLAMA:
            response = client.chat(
                model=self.chat_config.model,
                messages=messages,
                options={"num_predict": 200},
            )
            return response["message"]["content"].strip()

        elif provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI, AIProvider.VLLM):
            model = (
                self.chat_config.azure_deployment
                if provider == AIProvider.AZURE_OPENAI and self.chat_config.azure_deployment
                else self.chat_config.model
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
                "model": self.chat_config.model,
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
        """Single API call for OpenAI/Azure/vLLM; per-item loop for Ollama."""
        uncached = [t for t in texts if t not in self._EMBED_CACHE]
        if uncached:
            provider = self.embedding_config.provider if self.embedding_config else None
            if provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI, AIProvider.VLLM):
                embeddings = self._retry(self._do_embed_batch_openai, uncached)
                for t, emb in zip(uncached, embeddings):
                    self._EMBED_CACHE[t] = emb
            else:
                for t in uncached:
                    self._EMBED_CACHE[t] = self._retry(self._do_embed_single, t)
        return [self._EMBED_CACHE[t] for t in texts]

    def _do_embed_single(self, text: str) -> list[float]:
        client   = self._get_embed_client()
        provider = self.embedding_config.provider

        if provider == AIProvider.OLLAMA:
            response = client.embeddings(
                model=self.embedding_config.model, prompt=text
            )
            return response["embedding"]

        elif provider in (AIProvider.OPENAI, AIProvider.AZURE_OPENAI, AIProvider.VLLM):
            response = client.embeddings.create(
                model=self.embedding_config.model, input=[text]
            )
            return response.data[0].embedding

        elif provider == AIProvider.ANTHROPIC:
            raise NotImplementedError(
                "Anthropic does not have an embeddings API. "
                "Configure a separate provider for embeddings."
            )

        raise AIProviderError(f"Embeddings not supported for provider: {provider}")

    def _do_embed_batch_openai(self, texts: list[str]) -> list[list[float]]:
        client   = self._get_embed_client()
        response = client.embeddings.create(
            model=self.embedding_config.model, input=texts
        )
        return [e.embedding for e in response.data]

    # ── connection validation ────────────────────────────────────────────────

    def validate_connection(self) -> dict[str, Optional[SlotResult]]:
        """Independently tests the chat slot and (if configured) the embedding slot."""
        chat_result = self._validate_slot(self.chat_config, self._get_chat_client)
        embed_result = (
            self._validate_slot(self.embedding_config, self._get_embed_client)
            if self.embedding_config is not None
            else None
        )
        return {"chat": chat_result, "embedding": embed_result}

    def _validate_slot(self, model_config: ModelConfig, get_client_fn) -> SlotResult:
        try:
            client   = get_client_fn()
            provider = model_config.provider

            if provider == AIProvider.OLLAMA:
                resp  = client.list()
                items = resp.get("models") if isinstance(resp, dict) else getattr(resp, "models", None) or []
                names = _extract_ollama_names(items)
                if not any(n == model_config.model or n.startswith(model_config.model) for n in names):
                    return SlotResult(False, f"Model '{model_config.model}' not found on Ollama ({len(names)} available).")
                return SlotResult(True, f"Connected to Ollama ({model_config.model}).")

            elif provider == AIProvider.VLLM:
                resp = client.models.list()
                ids  = [m.id for m in resp.data]
                if model_config.model not in ids:
                    available = ", ".join(ids[:5]) or "none"
                    return SlotResult(False, f"Model '{model_config.model}' not served by vLLM. Available: {available}.")
                return SlotResult(True, f"Connected to vLLM ({model_config.model}).")

            elif provider == AIProvider.OPENAI:
                resp = client.models.list()
                ids  = [m.id for m in resp.data]
                if model_config.model not in ids:
                    return SlotResult(False, f"Model '{model_config.model}' not found on OpenAI ({len(ids)} available).")
                return SlotResult(True, f"Connected to OpenAI ({model_config.model}).")

            elif provider == AIProvider.AZURE_OPENAI:
                # Azure deployment names are account-specific and generally don't
                # appear in models.list() (which lists base models, not deployments),
                # so a membership check here would false-negative on valid configs.
                # This confirms the endpoint + key work, not that the deployment exists.
                client.models.list()
                return SlotResult(
                    True,
                    f"Connected to Azure OpenAI — endpoint and key are valid. "
                    f"Deployment '{model_config.azure_deployment or model_config.model}' is not verified here; "
                    f"it will only be confirmed on first use.",
                )

            elif provider == AIProvider.ANTHROPIC:
                resp = client.models.list()
                ids  = [m.id for m in resp.data]
                if model_config.model not in ids:
                    return SlotResult(False, f"Model '{model_config.model}' not found on Anthropic ({len(ids)} available).")
                return SlotResult(True, f"Connected to Anthropic ({model_config.model}).")

            return SlotResult(False, f"Unsupported provider: {provider}")

        except Exception as e:
            return SlotResult(False, str(e))


def _extract_ollama_names(items) -> list[str]:
    names: list[str] = []
    for m in (items or []):
        n = (
            (m.get("model") or m.get("name"))
            if isinstance(m, dict)
            else (getattr(m, "model", None) or getattr(m, "name", None))
        )
        if n:
            names.append(str(n))
    return names
