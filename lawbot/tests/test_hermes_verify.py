"""Tests for Hermes deterministic verification (lawbot.hermes_verify + API)."""

from __future__ import annotations

import sqlite3
import unittest

from fastapi.testclient import TestClient

from lawbot.api.app import app
from lawbot.citation_vault import CitationVault
from lawbot.db import SCHEMA
from lawbot.hermes_verify import (
    hermes_report_to_dict,
    run_hermes_checks,
    verify_empty_vault_leakage,
)

class TestHermesPure(unittest.TestCase):
    def test_empty_vault_leak_detects_ocga(self):
        errs = verify_empty_vault_leakage("Per O.C.G.A. § 9-3-25", True)
        self.assertTrue(errs)

    def test_empty_vault_clean(self):
        errs = verify_empty_vault_leakage("I do not have matching case text in the vault.", True)
        self.assertFalse(errs)

    def test_run_hermes_good_payload_no_db(self):
        r = run_hermes_checks(
            None,
            {
                "answer": "Hello.",
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "s1",
                "audit": {"vault_chunk_ids": []},
            },
        )
        self.assertTrue(r.passed)

    def test_run_hermes_bad_leakage(self):
        r = run_hermes_checks(
            None,
            {
                "answer": "SOURCE CHUNKS show that O.C.G.A. applies.",
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "s1",
            },
        )
        self.assertFalse(r.passed)

    def test_run_hermes_placeholder_chunk(self):
        r = run_hermes_checks(
            None,
            {
                "answer": "Use chunk chk_XXXXX for the quote.",
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "s1",
                "audit": {"vault_chunk_ids": []},
            },
        )
        self.assertFalse(r.passed)
        self.assertTrue(any("placeholder" in e.lower() for e in r.errors))

    def test_schema_rejects_non_string_answer(self):
        r = run_hermes_checks(
            None,
            {
                "answer": {"nested": "not a string"},
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "s1",
            },
        )
        self.assertFalse(r.passed)
        self.assertTrue(any("string" in e.lower() for e in r.errors))

    def test_run_hermes_quote_mismatch_with_db(self):
        conn = sqlite3.connect(":memory:")
        try:
            conn.executescript(SCHEMA)
            vault = CitationVault(conn)
            cid = vault.store_chunk("test", "The quick brown fox.", None, "x")
            r = run_hermes_checks(
                conn,
                {
                    "answer": f'<quote chunk="{cid}">wrong text</quote>',
                    "verification_ok": True,
                    "verification_errors": [],
                    "vault_empty": False,
                    "audit": {"vault_chunk_ids": [cid]},
                    "session_id": "s1",
                },
            )
            self.assertFalse(r.passed)
            self.assertTrue(any("quote check" in e for e in r.errors))
        finally:
            conn.close()


class TestHermesAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tc = TestClient(app)
        cls.client = cls._tc.__enter__()

    @classmethod
    def tearDownClass(cls):
        cls._tc.__exit__(None, None, None)

    def test_health_deep(self):
        r = self.client.get("/v1/health/deep")
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertEqual(j.get("status"), "ok")
        st = j.get("hermes_self_test") or {}
        self.assertTrue(st.get("clean_answer_passes"))
        self.assertTrue(st.get("ocga_leak_fails_as_expected"))

    def test_hermes_check_endpoint(self):
        r = self.client.post(
            "/v1/hermes/check",
            json={
                "answer": "ok",
                "verification_ok": True,
                "verification_errors": [],
                "vault_empty": True,
                "session_id": "x",
                "audit": {"vault_chunk_ids": []},
            },
        )
        self.assertEqual(r.status_code, 200)
        j = r.json()
        self.assertIn("hermes_passed", j)
        self.assertTrue(j.get("hermes_passed"))


class TestHermesReportDict(unittest.TestCase):
    def test_to_dict(self):
        from lawbot.hermes_verify import HermesReport

        d = hermes_report_to_dict(HermesReport(passed=True, errors=[], warnings=["w"], checks={"k": 1}))
        self.assertTrue(d["hermes_passed"])
        self.assertEqual(d["warnings"], ["w"])


if __name__ == "__main__":
    unittest.main()
