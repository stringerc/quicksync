"""Shared request bodies for the API (avoids circular imports with chat_turn)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatIn(BaseModel):
    message: str
    session_id: str | None = None
    research_query: str | None = Field(
        None,
        description="Optional query for case-law retrieval; defaults to the user message.",
    )
    search_case_law: bool = Field(
        True,
        description="If false, skip CourtListener search (Lexis/extra chunks may still apply).",
    )
    jurisdiction: str | None = Field(
        None,
        description="Optional jurisdiction hint (saved to session profile when non-empty).",
    )
    extra_chunk_ids: list[str] | None = Field(
        None,
        description="Include vault chunks (e.g. from /v1/citations/lexis-paste) in this turn.",
    )
    response_mode: str = Field(
        "chat",
        description="`chat` (default) or `document` for memo-style Markdown with headings.",
    )
    review_pass: str | None = Field(
        None,
        description=(
            "Optional API-only override for long filings (`part1`–`part4`, `appendix`, `custom`). "
            "Leave unset — the server automatically adds citation verification for long or citation-heavy messages."
        ),
    )
    review_custom_instruction: str | None = Field(
        None,
        description="When review_pass is `custom`, short focus text (API integrations only).",
    )
    polish_second_pass: bool = Field(
        False,
        description=(
            "If true, force a second model pass to tighten wording (extra latency/cost). "
            "When false, the server may still run polish automatically for long pastes, "
            "strengthen-this-filing tasks, or long citation-audit turns — see response "
            "`polish_second_pass_reason`."
        ),
    )
    draft_judge: bool = Field(
        False,
        description=(
            "If true, run an optional small LLM rubric (clarity/structure 1–5). Uses the fast OpenAI-compatible "
            "model when configured; otherwise Anthropic. Extra latency/cost."
        ),
    )
    paste_only_no_research: bool = Field(
        False,
        description=(
            "If true: intended to skip CourtListener on long drafting pastes (faster). "
            "Ignored when the message is classified as strengthen-this-filing and search_case_law is true — "
            "the server always runs opinion retrieval for that task. Ignored when force_authority_retrieval is true."
        ),
    )
    force_authority_retrieval: bool = Field(
        False,
        description=(
            "If true: never skip case-law retrieval for long drafting pastes; merge targeted authority queries. "
            "Overrides paste_only_no_research."
        ),
    )
    two_phase_filing: bool = Field(
        True,
        description=(
            "For document-mode strengthen-filing on substantive pastes: run fact-preservation pass then "
            "authority-injection pass when vault has chunks after retrieval. Extra latency/cost."
        ),
    )
