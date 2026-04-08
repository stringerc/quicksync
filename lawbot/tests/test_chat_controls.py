import unittest
import uuid

from fastapi.testclient import TestClient

from lawbot.api.app import app

from tests.llm_mock import patched_openai_chat_completion


class TestChatControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_search_case_law_false_skips_retrieval(self):
        with patched_openai_chat_completion(
            "Probable cause means a reasonable basis to believe a crime occurred."
        ):
            r = self.client.post(
                "/v1/chat",
                json={
                    "message": "Explain the basic idea of probable cause in one paragraph.",
                    "session_id": None,
                    "search_case_law": False,
                },
            )
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertTrue(d.get("retrieval_skipped"))
        self.assertTrue(d.get("vault_empty"))
        self.assertTrue(d.get("answer"))

    def test_jurisdiction_saved_to_profile(self):
        sid = "test-jur-session"
        jur = f"LawbotTestJur-{uuid.uuid4().hex[:12]}"
        with patched_openai_chat_completion(
            "Hearsay is an out-of-court statement offered to prove the truth of the matter asserted."
        ):
            r = self.client.post(
                "/v1/chat",
                json={
                    "message": "What is hearsay?",
                    "session_id": sid,
                    "search_case_law": False,
                    "jurisdiction": jur,
                },
            )
        self.assertEqual(r.status_code, 200)
        p = self.client.get("/v1/profile").json()
        self.assertEqual(p.get("jurisdiction"), jur)


if __name__ == "__main__":
    unittest.main()
