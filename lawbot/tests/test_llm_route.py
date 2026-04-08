"""decide_llm_route — multi-provider routing (no live APIs)."""

from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from lawbot.intent import CHAT_TASK_VERIFY_CITATIONS
from lawbot.model_routing import decide_llm_route


class TestDecideLLMRoute(unittest.TestCase):
    def _patch_settings(self, **kwargs):
        """Patch lawbot.model_routing.settings for routing tests."""
        oc_key = kwargs.get("oc_key", "")
        anth_on = kwargs.get("anth_on", False)
        mode = kwargs.get("mode", "auto")
        esc_model = kwargs.get("esc_model", "claude-opus-test")

        mock_s = MagicMock()
        mock_s.openai_compatible_key = MagicMock(return_value=oc_key)
        mock_s.anthropic_configured = MagicMock(return_value=anth_on)
        mock_s.anthropic_escalation_mode = mode
        mock_s.resolved_anthropic_escalation_model = MagicMock(return_value=esc_model)
        mock_s.chat_model = "PRIMARY_MODEL"
        mock_s.chat_model_fast = "FAST_MODEL"
        mock_s.chat_model_max = kwargs.get("chat_model_max", "")
        mock_s.anthropic_model = "SONNET_MODEL"

        p = patch("lawbot.model_routing.settings", mock_s)
        return p, mock_s

    def test_only_openai_compatible(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=False)
        with p:
            r = decide_llm_route(
                user_message="Explain hearsay in Georgia.",
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertEqual(r.model_id, "PRIMARY_MODEL")
        self.assertFalse(r.escalation)

    def test_only_openai_uses_max_tier_when_configured(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=False, chat_model_max="MAX_MODEL")
        with p:
            r = decide_llm_route(
                user_message="Short ask",
                meta_connectivity_hint=False,
                document_mode=True,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertEqual(r.model_id, "MAX_MODEL")
        self.assertFalse(r.escalation)

    def test_only_openai_max_tier_for_verify_task(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=False, chat_model_max="MAX_MODEL")
        with p:
            r = decide_llm_route(
                user_message="Verify these cites.",
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=CHAT_TASK_VERIFY_CITATIONS,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.model_id, "MAX_MODEL")

    def test_only_anthropic(self):
        p, _ = self._patch_settings(oc_key="", anth_on=True)
        with p:
            r = decide_llm_route(
                user_message="Hello",
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "anthropic")
        self.assertEqual(r.model_id, "SONNET_MODEL")
        self.assertFalse(r.escalation)

    def test_both_never_uses_openai(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="never")
        with p:
            r = decide_llm_route(
                user_message="x" * 5000,
                meta_connectivity_hint=False,
                document_mode=True,
                audit_mode=True,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertFalse(r.escalation)

    def test_both_always_anthropic_when_budget(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="always", esc_model="opus")
        with p:
            r = decide_llm_route(
                user_message="hi",
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "anthropic")
        self.assertEqual(r.model_id, "opus")
        self.assertTrue(r.escalation)

    def test_both_always_falls_back_when_no_budget(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="always")
        with p:
            r = decide_llm_route(
                user_message="hi",
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=False,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertFalse(r.escalation)

    def test_auto_connectivity_stays_openai(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="auto")
        with p:
            r = decide_llm_route(
                user_message="testing to see if this works",
                meta_connectivity_hint=True,
                document_mode=True,
                audit_mode=True,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertEqual(r.model_id, "FAST_MODEL")

    def test_auto_polish_pass_stays_openai(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="auto")
        with p:
            r = decide_llm_route(
                user_message="POLISH PASS …" + "x" * 5000,
                meta_connectivity_hint=False,
                document_mode=True,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=True,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "openai_compatible")
        self.assertFalse(r.escalation)

    def test_auto_document_mode_escalates(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="auto", esc_model="opus-x")
        with p:
            r = decide_llm_route(
                user_message="Short ask",
                meta_connectivity_hint=False,
                document_mode=True,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "anthropic")
        self.assertEqual(r.model_id, "opus-x")
        self.assertTrue(r.escalation)

    def test_auto_long_message_escalates(self):
        p, _ = self._patch_settings(oc_key="k", anth_on=True, mode="auto")
        with p:
            r = decide_llm_route(
                user_message="a" * 1600,
                meta_connectivity_hint=False,
                document_mode=False,
                audit_mode=False,
                task_hint=None,
                polish_pass_only=False,
                anthropic_budget_ok=True,
            )
        self.assertEqual(r.backend, "anthropic")
        self.assertTrue(r.escalation)


if __name__ == "__main__":
    unittest.main()
