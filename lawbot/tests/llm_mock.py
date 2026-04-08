"""
Shared OpenAI-compatible client mocks so API tests run without network or API keys.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch

from lawbot.config import settings as lawbot_settings


@contextmanager
def patched_openai_chat_completion(content: str = "Mock paragraph for tests."):
    """Patch shared OpenAI-compatible client so chat completions return deterministic text."""

    async def fake_create(**kwargs):
        if kwargs.get("stream"):

            async def agen():
                text = content
                step = max(1, len(text) // 4) or 1
                for i in range(0, len(text), step):
                    piece = text[i : i + step]
                    m = MagicMock()
                    m.usage = None
                    m.choices = [MagicMock(delta=MagicMock(content=piece))]
                    yield m

            return agen()

        return MagicMock(choices=[MagicMock(message=MagicMock(content=content))])

    mock_client = MagicMock()
    mock_client.chat.completions.create = AsyncMock(side_effect=fake_create)

    with patch("lawbot.chat_service.get_openai_compatible_client", return_value=mock_client):
        with patch.object(lawbot_settings, "nvidia_api_key", "sk-mock-test"):
            with patch.object(lawbot_settings, "anthropic_api_key", ""):
                with patch.object(lawbot_settings, "lawbot_embedding_model", ""):
                    yield
