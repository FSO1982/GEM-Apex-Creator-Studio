import types

import pytest

import ai.client as ai_client
from ai.client import AIClient


class DummyResponse:
    def __init__(self, text):
        self.text = text


class DummyChat:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)
        return DummyResponse(f"echo: {message}")


class DummyModel:
    def __init__(self, model_name, system_instruction=None):
        self.model_name = model_name
        self.system_instruction = system_instruction
        self.generate_calls = []

    def generate_content(self, prompt, generation_config=None):
        self.generate_calls.append({"prompt": prompt, "config": generation_config})
        return DummyResponse("generated")

    def start_chat(self, history):
        return DummyChat()


class FakeGenAI:
    def __init__(self):
        self.configured_keys = []
        self.models = []
        self.types = types.SimpleNamespace(GenerationConfig=lambda **kwargs: kwargs)

    def configure(self, api_key):
        self.configured_keys.append(api_key)

    def GenerativeModel(self, model_name, system_instruction=None):
        model = DummyModel(model_name, system_instruction)
        self.models.append(model)
        return model


@pytest.fixture(autouse=True)
def fake_genai(monkeypatch):
    fake = FakeGenAI()
    monkeypatch.setattr(ai_client, "genai", fake)
    return fake


def test_configure_sets_models_and_cleans_key(fake_genai):
    client = AIClient()

    client.configure("  test-key  ")

    assert fake_genai.configured_keys == ["test-key"]
    assert isinstance(client.model, DummyModel)
    assert client.model.model_name == "gemini-2.5-flash"
    assert isinstance(client.vision_model, DummyModel)
    assert client.api_key == "test-key"


def test_test_connection_reports_success(fake_genai):
    client = AIClient()
    client.configure("another-key")

    ok, message = client.test_connection()

    assert ok is True
    assert "erfolg" in message.lower()


def test_generate_text_uses_system_instruction(fake_genai):
    client = AIClient()
    client.configure("key")

    text = client.generate_text("user prompt", system_instruction="system")

    assert text == "generated"
    assert fake_genai.models[0].generate_calls[0]["prompt"].startswith("system")
    assert "user prompt" in fake_genai.models[0].generate_calls[0]["prompt"]


def test_generate_text_without_model_returns_error(fake_genai):
    client = AIClient()

    result = client.generate_text("prompt only")

    assert "nicht konfiguriert" in result.lower()


def test_start_chat_uses_system_instruction(fake_genai):
    client = AIClient()
    client.configure("chat-key")

    chat_session = client.start_chat("system prompt")

    assert isinstance(chat_session, DummyChat)
    assert fake_genai.models[-1].system_instruction == "system prompt"
