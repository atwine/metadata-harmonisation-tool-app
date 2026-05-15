from fastapi import APIRouter, Query

from models.schemas import AIConfig, AITestResponse, OllamaModelsResponse, ProviderInfo

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
            "Use with OpenAI embeddings via Azure or a separate embedding model."
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
        connected, message = wrapper.validate_connection()
        return AITestResponse(connected=connected, message=message)
    except Exception as e:
        return AITestResponse(connected=False, message=str(e))


@router.get("/ollama-models", response_model=OllamaModelsResponse)
async def get_ollama_models(base_url: str = Query("http://localhost:11434")):
    try:
        import ollama
        client = ollama.Client(host=base_url)
        resp   = client.list()
        models = [m["name"] for m in (resp.get("models") or [])]
        return OllamaModelsResponse(models=models)
    except Exception:
        return OllamaModelsResponse(models=[])
