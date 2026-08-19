"""
AI provider config — exact client construction preserved from the original Streamlit app,
extended with vLLM (OpenAI-compatible self-hosted) support and per-role (chat/embedding)
provider slots so chat and embeddings can each point at a different provider/server.
"""
from __future__ import annotations
import re
from enum import Enum
from typing import Optional


class AIProvider(Enum):
    OLLAMA       = "ollama"
    VLLM         = "vllm"
    OPENAI       = "openai"
    ANTHROPIC    = "anthropic"
    AZURE_OPENAI = "azure_openai"


_PROVIDER_MAP = {
    "ollama":       AIProvider.OLLAMA,
    "vllm":         AIProvider.VLLM,
    "openai":       AIProvider.OPENAI,
    "anthropic":    AIProvider.ANTHROPIC,
    "azure_openai": AIProvider.AZURE_OPENAI,
}


def normalise_openai_compat_base_url(base_url: str) -> str:
    """vLLM (and other OpenAI-compatible servers) serve under /v1 — accept either
    'http://host:8000' or 'http://host:8000/v1' from the user."""
    base = (base_url or "").rstrip("/")
    if not base:
        raise ValueError("Base URL is required")
    if not base.endswith("/v1"):
        base += "/v1"
    return base


class ModelConfig:
    """A single provider+model configuration for one role (chat or embedding)."""

    def __init__(
        self,
        provider: AIProvider,
        model: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        request_timeout: int = 30,
        azure_api_version: Optional[str] = None,
        azure_deployment: Optional[str] = None,
    ):
        self.provider          = provider
        self.model              = model
        self.api_key           = api_key
        self.base_url          = base_url or ("http://localhost:11434" if provider == AIProvider.OLLAMA else None)
        self.request_timeout   = request_timeout
        self.azure_api_version = azure_api_version or "2024-02-01"
        self.azure_deployment  = azure_deployment

    @classmethod
    def from_slot(cls, slot, request_timeout: int) -> "ModelConfig":
        """slot is a ProviderSlot Pydantic model."""
        return cls(
            provider=_PROVIDER_MAP[slot.provider],
            model=slot.model,
            api_key=slot.api_key,
            base_url=slot.base_url,
            request_timeout=request_timeout,
            azure_api_version=slot.azure_api_version,
            azure_deployment=slot.azure_deployment,
        )

    def get_client(self):
        if self.provider == AIProvider.OLLAMA:
            import ollama
            client = ollama.Client(host=self.base_url)
            client.list()  # liveness check — raises if Ollama not running
            return client

        elif self.provider == AIProvider.VLLM:
            import openai
            base = normalise_openai_compat_base_url(self.base_url or "")
            # vLLM does not require auth unless launched with --api-key.
            return openai.OpenAI(api_key=self.api_key or "not-needed", base_url=base)

        elif self.provider == AIProvider.OPENAI:
            import openai
            if not re.match(r"^sk-[A-Za-z0-9]{20,}$", self.api_key or ""):
                raise ValueError("Invalid OpenAI API key format")
            return openai.OpenAI(api_key=self.api_key, base_url=self.base_url)

        elif self.provider == AIProvider.ANTHROPIC:
            import anthropic
            if not re.match(r"^sk-ant-[A-Za-z0-9_-]{20,}$", self.api_key or ""):
                raise ValueError("Invalid Anthropic API key format")
            return anthropic.Anthropic(api_key=self.api_key, base_url=self.base_url)

        elif self.provider == AIProvider.AZURE_OPENAI:
            import openai
            if not re.match(r"^[a-fA-F0-9]{32}$", self.api_key or ""):
                raise ValueError("Invalid Azure OpenAI API key format")
            return openai.AzureOpenAI(
                api_key=self.api_key,
                azure_endpoint=self.base_url,
                api_version=self.azure_api_version or "2024-02-01",
            )

        raise ValueError(f"Unknown provider: {self.provider}")
