from fastapi import APIRouter, Query

from models.schemas import AIConfig, AITestResponse, OllamaModelsResponse, ProviderInfo, SlotTestResult

router = APIRouter()

PROVIDERS: list[ProviderInfo] = [
    ProviderInfo(
        id="ollama",
        name="Ollama (Local)",
        requires_api_key=False,
        requires_base_url=True,
        default_base_url="http://localhost:11434",
        supports_embeddings=True,
        default_chat_model="llama3.1:8b",
        default_embedding_model="nomic-embed-text",
    ),
    ProviderInfo(
        id="vllm",
        name="vLLM (Self-hosted)",
        requires_api_key=False,
        requires_base_url=True,
        supports_embeddings=True,
        note="OpenAI-compatible server. Point at the host, e.g. http://10.35.50.41:8000 — /v1 is added automatically.",
    ),
    ProviderInfo(
        id="openai",
        name="OpenAI",
        requires_api_key=True,
        api_key_pattern="sk-[A-Za-z0-9]{20,}",
        supports_embeddings=True,
        default_chat_model="gpt-4o-mini",
        default_embedding_model="text-embedding-3-small",
    ),
    ProviderInfo(
        id="anthropic",
        name="Anthropic",
        requires_api_key=True,
        api_key_pattern="sk-ant-[A-Za-z0-9_-]{20,}",
        supports_embeddings=False,
        note=(
            "Anthropic does not have an embeddings API. "
            "Use a different provider for the embedding model."
        ),
    ),
    ProviderInfo(
        id="azure_openai",
        name="Azure OpenAI",
        requires_api_key=True,
        requires_base_url=True,
        requires_deployment=True,
        supports_embeddings=True,
    ),
]


@router.get("/providers", response_model=list[ProviderInfo])
async def get_providers():
    return PROVIDERS


@router.post("/test", response_model=AITestResponse)
async def test_connection(config: AIConfig):
    from core.ai_provider import AIProviderWrapper
    try:
        wrapper = AIProviderWrapper(config)
        result = wrapper.validate_connection()
    except Exception as e:
        return AITestResponse(
            connected=False,
            chat=SlotTestResult(connected=False, message=str(e)),
            embedding=None,
        )

    chat = result["chat"]
    embedding = result["embedding"]
    overall = chat.connected and (embedding is None or embedding.connected)
    return AITestResponse(
        connected=overall,
        chat=SlotTestResult(connected=chat.connected, message=chat.message),
        embedding=(
            SlotTestResult(connected=embedding.connected, message=embedding.message)
            if embedding is not None
            else None
        ),
    )


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


@router.get("/models", response_model=OllamaModelsResponse)
async def list_models(
    provider: str = Query(...),
    base_url: str = Query(""),
    api_key: str = Query(""),
):
    """Lists available models for a live-fetchable provider (Ollama, vLLM)."""
    try:
        if provider == "ollama":
            import ollama
            client = ollama.Client(host=base_url or "http://localhost:11434")
            resp   = client.list()
            items  = resp.get("models") if isinstance(resp, dict) else getattr(resp, "models", None) or []
            return OllamaModelsResponse(models=sorted(_extract_ollama_names(items)))

        elif provider == "vllm":
            from core.config import normalise_openai_compat_base_url
            import openai
            if not base_url.strip():
                return OllamaModelsResponse(models=[])
            client = openai.OpenAI(
                api_key=api_key or "not-needed",
                base_url=normalise_openai_compat_base_url(base_url),
            )
            resp = client.models.list()
            return OllamaModelsResponse(models=sorted(m.id for m in resp.data))

        return OllamaModelsResponse(models=[])
    except Exception:
        return OllamaModelsResponse(models=[])
