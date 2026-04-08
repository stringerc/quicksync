"""
Decide whether to run a CourtListener search and compose the query string.

- Short or smoke test messages skip auto search (avoids junk hits from words like "testing").
- Messages that clearly name a U.S. state / federal circuit can trigger search with fewer words.
- Jurisdiction is inferred from the message (e.g. "in Georgia") and merged into the search query
  so users do not need separate fields.
"""

from __future__ import annotations

import re

# Messages shorter than this (after strip) won't auto-trigger case search,
# unless _message_mentions_state_or_court() matches.
MIN_MESSAGE_CHARS_FOR_AUTO_RETRIEVAL = 24

MIN_MESSAGE_CHARS_WITH_PLACE_HINT = 10

# Exact phrases (lowercase) that should not trigger a case-law search alone.
_SMOKE = frozenset(
    {
        "test",
        "testing",
        "tests",
        "ping",
        "pong",
        "hello",
        "hi",
        "hey",
        "ok",
        "okay",
        "yes",
        "no",
        "thanks",
        "thank you",
        "thankyou",
        "yo",
        "sup",
        "hi there",
        "hello there",
    }
)

# "new york" before "york" etc. — longer names first for regex alternation
_US_STATE_NAMES = (
    "district of columbia",
    "north carolina",
    "south carolina",
    "north dakota",
    "south dakota",
    "new hampshire",
    "new jersey",
    "new mexico",
    "new york",
    "rhode island",
    "west virginia",
    "alabama",
    "alaska",
    "arizona",
    "arkansas",
    "california",
    "colorado",
    "connecticut",
    "delaware",
    "florida",
    "georgia",
    "hawaii",
    "idaho",
    "illinois",
    "indiana",
    "iowa",
    "kansas",
    "kentucky",
    "louisiana",
    "maine",
    "maryland",
    "massachusetts",
    "michigan",
    "minnesota",
    "mississippi",
    "missouri",
    "montana",
    "nebraska",
    "nevada",
    "ohio",
    "oklahoma",
    "oregon",
    "pennsylvania",
    "tennessee",
    "texas",
    "utah",
    "vermont",
    "virginia",
    "washington",
    "wisconsin",
    "wyoming",
)

# Two-letter state codes as whole words (lowercase message).
_PLACE_PATTERN = re.compile(
    r"\b("
    + "|".join(re.escape(s.replace(" ", r"\s+")) for s in _US_STATE_NAMES)
    + r"|11th\s+circuit|eleventh\s+circuit|1st\s+circuit|first\s+circuit|2d\s+circuit|second\s+circuit|"
    r"3d\s+circuit|third\s+circuit|4th\s+circuit|fourth\s+circuit|5th\s+circuit|fifth\s+circuit|"
    r"6th\s+circuit|sixth\s+circuit|7th\s+circuit|seventh\s+circuit|8th\s+circuit|eighth\s+circuit|"
    r"9th\s+circuit|ninth\s+circuit|10th\s+circuit|tenth\s+circuit|federal\s+circuit|"
    r"u\.s\.\s+supreme\s+court|supreme\s+court)\b",
    re.I,
)


def _message_mentions_state_or_court(lower: str) -> bool:
    # Only full state / circuit phrases — two-letter postal codes collide with common English ("in", "or", "ok", "me").
    return bool(_PLACE_PATTERN.search(lower))


# If the user is clearly discussing law/facts, do not treat as a "ping" even if they say "testing".
_LEGAL_SUBSTANCE_HINT = re.compile(
    r"\b(custody|malpractice|attorney|plaintiff|defendant|motion|court|statute|"
    r"o\.c\.g\.a|petition|order|hearing|judge|discovery|complaint|appeal|gwinnett|"
    r"georgia|county|federal|damages|negligence|contract|divorce|visitation|alienation)\b",
    re.I,
)


def message_suggests_substantive_legal_topic(message: str) -> bool:
    """True when a short message still looks like real legal subject matter (prefer standard/deep routing)."""
    return bool(_LEGAL_SUBSTANCE_HINT.search((message or "").lower()))


def is_smoke_test_message(user_message: str) -> bool:
    """
    True for very short hello/ping-style messages (see _SMOKE).
    Used for model routing, optional retrieval skip, and chat-vs-memo shaping when Document UI is on.
    """
    m = (user_message or "").strip().lower()
    if not m:
        return True
    if len(m) > 80:
        return False
    return m in _SMOKE


def is_meta_connectivity_message(user_message: str) -> bool:
    """
    True for short "is the system up?" messages — skip case-law search and prior-session timeline.

    Avoid false positives: if the message mentions substantive legal/fact hooks, return False.
    """
    s = (user_message or "").strip()
    if not s or len(s) > 140:
        return False
    lower = s.lower()
    if _LEGAL_SUBSTANCE_HINT.search(lower):
        return False
    patterns = (
        r"\btesting\s+to\s+see\s+if\b",
        r"\btest\s+to\s+see\s+if\b",
        r"\bsee\s+if\s+this\s+works\b",
        r"\bsee\s+if\s+it\s+works\b",
        r"\bdoes\s+this\s+work\b",
        r"\bis\s+this\s+working\b",
        r"\btrying\s+to\s+see\s+if\b",
        r"\bjust\s+checking(\s+if)?\b",
        r"\bchecking\s+if\s+this\s+works\b",
    )
    return any(re.search(p, lower) for p in patterns)


_PRESTIGE_ATTORNEY_FRAMING = re.compile(
    r"top\s*0?\.01%|0\.01%\s*attorney|elite\s+attorney|top\s+appellate\s+attorney|"
    r"seasoned\s+appellate\s+attorney|like\s+a\s+top\s+[\d.]+%?\s*attorney|"
    r"best\s+.*\s+attorney\s+would|prestigious\s+attorney",
    re.I,
)


def user_asks_prestige_attorney_framing(user_message: str) -> bool:
    """User wants 'elite / top percentile' legal writing — trigger neutral craft feedback, not role-play."""
    return bool(_PRESTIGE_ATTORNEY_FRAMING.search(user_message or ""))


def _title_case_place(name: str) -> str:
    return " ".join(w.capitalize() if w not in ("of",) else w for w in name.strip().split())


def extract_jurisdiction_hint(user_message: str) -> str | None:
    """
    Best-effort human-readable jurisdiction label from the message (e.g. "Georgia", "11th Circuit").
    """
    msg = (user_message or "").strip()
    if not msg:
        return None
    lower = msg.lower()
    m = _PLACE_PATTERN.search(lower)
    if m:
        span = m.group(0)
        if "circuit" in span or "court" in span:
            return span.title()
        return _title_case_place(span)
    return None


def infer_research_query(user_message: str, explicit_research_query: str | None) -> str:
    """
    Return the string to pass to CourtListener search, or "" to skip retrieval.

    If the user filled "Optional: case-law search query" in the UI, that always wins.
    """
    if explicit_research_query is not None and explicit_research_query.strip():
        return explicit_research_query.strip()

    msg = (user_message or "").strip()
    if not msg:
        return ""

    lower = msg.lower()
    if lower in _SMOKE:
        return ""

    if is_meta_connectivity_message(msg):
        return ""

    if _message_mentions_state_or_court(lower):
        if len(msg) >= MIN_MESSAGE_CHARS_WITH_PLACE_HINT:
            return msg

    if len(msg) < MIN_MESSAGE_CHARS_FOR_AUTO_RETRIEVAL:
        return ""

    token = re.sub(r"[^\w\s]", "", lower).strip()
    if not token or (len(token.split()) <= 2 and token in _SMOKE):
        return ""

    return msg


def _sanitize_query(q: str) -> str:
    q = " ".join(q.split())
    if len(q) > 2000:
        q = q[:2000]
    return q


CHAT_TASK_VERIFY_CITATIONS = "verify_citations"
CHAT_TASK_STRENGTHEN_FILING = "strengthen_filing"

# User instructions are almost always at the top; appendices ("how to verify") must not hijack routing.
_LEADING_INTENT_CHARS = 2200


def _leading_intent_text(user_message: str, max_chars: int = _LEADING_INTENT_CHARS) -> str:
    s = (user_message or "").strip()
    return s[:max_chars].lower()


def classify_simple_task(user_message: str) -> str | None:
    """
    Light keyword routing for common asks — no heavy NLP.

    - Leading slice only for verify/check (avoids pasted "HOW TO VERIFY" appendices winning over "rewrite this…").
    - rewrite/redraft/rephrase at the top + long paste or filing vocabulary → strengthen/draft first.
    - strengthen/improve/… + pleading vocabulary → drafting help.
    """
    m_full = (user_message or "").strip().lower()
    if not m_full:
        return None

    lead = _leading_intent_text(user_message)
    lead1200 = lead[:1200]

    def _paste_is_filing_context() -> bool:
        long_paste = len(user_message) > 3500
        filingish = bool(
            re.search(
                r"\b(answer|counterclaim|complaint|motion|brief|petition|pleading|"
                r"magistrate|defendant|plaintiff|comes\s+now|wherefore)\b",
                m_full,
                re.I,
            )
        )
        return long_paste or filingish

    # 1) Opening rewrite/draft beats buried verification language later in the same paste.
    if re.search(r"\b(rewrite|redraft|rephrase)\b", lead1200) and _paste_is_filing_context():
        return CHAT_TASK_STRENGTHEN_FILING

    # 1b) Same for elite / "top .01% appellate" style asks (prestige framing), not only "rewrite".
    if user_asks_prestige_attorney_framing(lead1200) and _paste_is_filing_context():
        return CHAT_TASK_STRENGTHEN_FILING

    # 2) Verification ask only if it appears in the leading text (not deep in a filing appendix).
    # Match "verified"/"verifying" (not just "verify" word), plus "make sure"/"ensure" asks.
    verify_intent = re.search(
        r"\b(verify|verif(?:y|ied|ying|ication)|check|confirm|validat\w*|ensure|make\s+sure)\b",
        lead,
        re.I,
    )
    authority_intent = re.search(
        r"\b(citations?|cites?|cases?|case\s+law|laws?|statutes?|authorities|holdings?|o\.c\.g\.a\.)\b",
        lead,
        re.I,
    )
    if verify_intent and authority_intent:
        return CHAT_TASK_VERIFY_CITATIONS

    # 3) Strengthen / polish + pleading terms (leading instruction or anywhere in short messages).
    lead_or_full = lead if len(user_message) > 800 else m_full
    if re.search(
        r"\b(strengthen|improve|beef\s+up|tighten|sharpen|upgrade|polish|rewrite|redraft|rephrase)\b",
        lead_or_full,
    ) and re.search(
        r"\b(motion|answer|brief|pleading|filing|opposition|reply|counterclaim|complaint|petition)\b",
        m_full,
    ):
        return CHAT_TASK_STRENGTHEN_FILING

    return None


def task_directive_for_chat_task(task: str | None, *, document_mode: bool = False) -> str | None:
    """Short block injected into the user message bundle (not shown to user)."""
    if task == CHAT_TASK_VERIFY_CITATIONS:
        return (
            "USER REQUEST TYPE: Citation verification (keep the reply short — like a normal chat).\n"
            "- Work through the citation-like items in the USER MESSAGE and in EXTRACTED CITATIONS (if listed).\n"
            "- For each: does a SOURCE CHUNK support what the user said? Say in plain words: **Matches what we loaded**, "
            "**Partly matches**, or **Not in the loaded sources**.\n"
            "- If something looks wrong, say what’s off in one line. Only give a different case name, cite, or reporter line "
            "if that exact text appears in a SOURCE CHUNK — never guess from memory.\n"
            "- Do **not** output a redrafted pleading, condensed filing, or section-by-section rewrite unless the user "
            "explicitly asked to rewrite — even if they pasted a long document.\n"
            "- Skip long essays, long introductions, and repeating the user’s whole document."
        )
    if task == CHAT_TASK_STRENGTHEN_FILING:
        if document_mode:
            return (
                "USER REQUEST TYPE: Strengthen or rewrite a court filing (document mode — default for the Lawbot web UI).\n"
                "- **Primary deliverable:** Output the **complete revised pleading or filing** in Markdown, top to bottom: "
                "**court caption** (verbatim from their paste unless they asked otherwise), parties, case number, document title, "
                "then all numbered parts, defenses, counterclaims, prayer, verification, and certificate of service **as a continuous draft**—"
                "the same expectation as a standalone drafting assistant (e.g. Claude-style full rewrite). "
                "Do **not** substitute only a bullet list of edits, Before→After samples, or a feedback memo unless the user clearly asked for comments-only.\n"
                "- Improve wording, structure, and persuasion **in the full text**; keep formal court tone.\n"
                "- Follow **Document output quality** and **Caption block** rules in the system prompt.\n"
                "- **Do not** structure the reply like citation verification matrices unless the user asked verify-only.\n"
                "- If no SOURCE CHUNKS: do not invent new holdings; you may still rewrite the entire pasted text for clarity and force.\n"
                "- **Preserve factual specificity** from the user’s paste (numbered ¶s, chronology, instructions)—do not collapse into a generic shell when the paste had detail.\n"
                "- **Preserve structural sections** from the paste when present: e.g. **NOTE ON EXPERT AFFIDAVIT**, **LEGAL STANDARD**, **damages breakdown** — do not drop them for brevity. Keep **consecutive ¶ numbering** (no gaps like ¶5 → ¶7) unless the user’s original had gaps.\n"
                "- After the pleading, include the **Editor's overview (not for filing)** section exactly as described in **Document output quality**.\n"
                "- Do not invent cases or statutes beyond what appears in the USER MESSAGE; stay within citation rules."
            )
        return (
            "USER REQUEST TYPE: Strengthen or rewrite a court filing (practical; prioritize this over side tasks).\n"
            "- Follow the **High-caliber drafting feedback** rules in the system prompt: strategic opening, anchored edits, Before→After examples, risk notes, **Priority order** — not generic checklists.\n"
            "- **Do not** structure the reply like citation verification: avoid **Scope**, **Vault vs not**, or per-cite matrices unless the user asked verify-only.\n"
            "- If **no** court excerpts are attached, one short acknowledgment; then focus on structure, emphasis, and internal consistency in the pasted text — do not invent holdings.\n"
            "- When SOURCE CHUNKS exist and are on-topic, a short subordinate note is OK; ignore off-topic chunks.\n"
            "- Do not invent cases or statutes; stay within the citation rules in the system prompt."
        )
    return None


def prepare_case_law_search(
    user_message: str,
    explicit_research_query: str | None,
    profile: dict[str, str],
) -> str:
    """
    Build the final CourtListener `q` parameter: core legal query + jurisdiction hint when helpful.
    """
    q = infer_research_query(user_message, explicit_research_query)
    if not q:
        return ""
    stored = (profile.get("jurisdiction") or "").strip()
    hint = extract_jurisdiction_hint(user_message)
    place = hint or stored
    if place and place.lower() not in q.lower():
        q = f"{q} {place}"
    return _sanitize_query(q)
