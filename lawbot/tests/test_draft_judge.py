"""draft_judge — OpenAI-compatible vs Anthropic paths (mocked APIs)."""

from __future__ import annotations

import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from lawbot.config import settings
from lawbot.draft_judge import run_draft_judge_rubric


class TestDraftJudge(unittest.IsolatedAsyncioTestCase):
    async def test_prefers_openai_when_both_configured(self):
        mock_msg = MagicMock()
        mock_msg.choices = [MagicMock(message=MagicMock(content='{"clarity":4,"structure":3,"one_line":"ok"}'))]
        client_inst = MagicMock()
        client_inst.chat.completions.create = AsyncMock(return_value=mock_msg)
        with (
            patch.object(settings, "nvidia_api_key", "nv-key"),
            patch.object(settings, "openai_compatible_api_key", ""),
            patch.object(settings, "anthropic_api_key", "ant-key"),
            patch.object(settings, "chat_model", "PRIMARY"),
            patch.object(settings, "chat_model_fast", "FAST"),
            patch.object(settings, "lawbot_auxiliary_model_tier", "fast"),
            patch("lawbot.draft_judge.get_openai_compatible_client", return_value=client_inst),
        ):
            out = await run_draft_judge_rubric("Some draft text.")
        self.assertTrue(out.get("parse_ok"))
        self.assertEqual(out.get("judge_model"), "FAST")

    async def test_anthropic_when_no_openai_compatible(self):
        mock_msg = MagicMock()
        mock_msg.content = [MagicMock(type="text", text='{"clarity":3,"structure":4,"one_line":"fine"}')]
        client_inst = MagicMock()
        client_inst.messages.create = AsyncMock(return_value=mock_msg)
        with (
            patch.object(settings, "nvidia_api_key", ""),
            patch.object(settings, "openai_compatible_api_key", ""),
            patch.object(settings, "anthropic_api_key", "sk-ant-api03"),
            patch.object(settings, "anthropic_model", "claude-judge-test"),
            patch("lawbot.draft_judge.get_openai_compatible_client"),
            patch("lawbot.draft_judge.get_anthropic_async_client", return_value=client_inst),
        ):
            out = await run_draft_judge_rubric("Draft body.")
        self.assertTrue(out.get("parse_ok"))
        self.assertEqual(out.get("judge_model"), "claude-judge-test")

    async def test_no_backend_error(self):
        with (
            patch.object(settings, "nvidia_api_key", ""),
            patch.object(settings, "openai_compatible_api_key", ""),
            patch.object(settings, "anthropic_api_key", ""),
        ):
            out = await run_draft_judge_rubric("x")
        self.assertEqual(out.get("error"), "no_llm_backend")


if __name__ == "__main__":
    unittest.main()
