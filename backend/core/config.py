"""
AI provider config — exact client construction preserved from the original Streamlit app.
"""
from __future__ import annotations
import re
from enum import Enum
from typing import Optional


class AIProvider(Enum):
    OLLAMA       = "ollama"
    OPENAI       = "openai"
    ANTHROPIC    = "anthropic"
    AZURE_OPENAI = "azure_openai"


class ModelConfig:
    def __init__(
        self,
        provider: AIProvider,
        chat_model: str,
        embedding_model: str = "",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        request_timeout: int = 30,
        azure_api_version: Optional[str] = None,
        azure_deployment: Optional[str] = None,
    ):
        self.provider          = provider
        self.chat_model        = chat_model
        self.embedding_model   = embedding_model
        self.api_key           = api_key
        self.base_url          = base_url or ("http://localhost:11434" if provider == AIProvider.OLLAMA else None)
        self.request_timeout   = request_timeout
        self.azure_api_version = azure_api_version or "2024-02-01"
        self.azure_deployment  = azure_deployment

    @classmethod
    def from_ai_config(cls, config) -> ModelConfig:
        provider_map = {
            "ollama":       AIProvider.OLLAMA,
            "openai":       AIProvider.OPENAI,
            "anthropic":    AIProvider.ANTHROPIC,
            "azure_openai": AIProvider.AZURE_OPENAI,
        }
        return cls(
            provider=provider_map[config.provider],
            chat_model=config.chat_model,
            embedding_model=config.embedding_model or "",
            api_key=config.api_key,
            base_url=config.base_url,
            request_timeout=config.request_timeout,
            azure_api_version=config.azure_api_version,
            azure_deployment=config.azure_deployment,
        )

    def get_client(self):
        if self.provider == AIProvider.OLLAMA:
            import ollama
            client = ollama.Client(host=self.base_url)
            client.list()  # liveness check — raises if Ollama not running
            return client

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
