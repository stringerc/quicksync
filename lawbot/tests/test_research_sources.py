"""research_sources module is importable and exposes expected symbols."""

from lawbot import research_sources


def test_open_access_strict_append_nonempty():
    assert len(research_sources.OPEN_ACCESS_STRICT_APPEND.strip()) > 200


def test_open_access_vault_hint_lines():
    assert len(research_sources.OPEN_ACCESS_VAULT_HINT_LINES) >= 4
    assert any("CourtListener" in line for line in research_sources.OPEN_ACCESS_VAULT_HINT_LINES)
