"""The AI provider API key travels in a header, never in the URL (item 7a)."""

import sys
from pathlib import Path
from types import SimpleNamespace

import openai
import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

import main  # noqa: E402

KEY = "sk-test-key-not-real-0123456789"


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    async def no_refresh():
        return None

    monkeypatch.setattr(main, "refresh_ontology", no_refresh)
    with TestClient(main.app, base_url="http://localhost:8000") as c:
        yield c


@pytest.fixture
def seen(monkeypatch):
    captured = {}

    class FakeOpenAI:
        def __init__(self, api_key, base_url):
            captured["api_key"] = api_key
            self.models = SimpleNamespace(list=lambda: SimpleNamespace(data=[SimpleNamespace(id="m1")]))

    monkeypatch.setattr(openai, "OpenAI", FakeOpenAI)
    return captured


PARAMS = {"provider": "vllm", "base_url": "http://vllm.example:8000"}


def test_key_in_header_reaches_the_provider(client, seen):
    r = client.get("/api/ai-config/models", params=PARAMS, headers={"X-Api-Key": KEY})
    assert r.json() == {"models": ["m1"]}
    assert seen["api_key"] == KEY


def test_key_in_url_is_ignored(client, seen):
    client.get("/api/ai-config/models", params={**PARAMS, "api_key": KEY})
    assert seen["api_key"] == "not-needed"


def test_no_key_still_works(client, seen):
    assert client.get("/api/ai-config/models", params=PARAMS).json() == {"models": ["m1"]}
    assert seen["api_key"] == "not-needed"
