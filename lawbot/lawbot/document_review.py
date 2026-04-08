"""
Long filings: optional API section focus + **automatic** citation verification.

Automatic mode needs no settings: long or citation-heavy messages get a verification
checklist so the model matches cites to SOURCE CHUNKS instead of inventing law.
"""

from __future__ import annotations

from lawbot.citation_extract import ExtractedCitation

# Optional API overrides (simple web UI hides this — seamless default).
VALID_REVIEW_PASSES = frozenset(
    {"full", "part1", "part2", "part3", "part4", "appendix", "custom"}
)

AUTO_LONG_MESSAGE_CHARS = 7_500
AUTO_MIN_CITATION_CANDIDATES = 2

SECTION_FOCUS: dict[str, str] = {
    "part1": (
        "Focus: **Part I** — Notice of jurisdictional transfer; amount in controversy; "
        "O.C.G.A. § 15-10-45(d) and transfer to an appropriate court of the county; "
        "Gwinnett Magistrate vs State Court framing. "
        "Gwinnett publishes official forms at gwinnettcourts.com/magistrate/civil-filing-forms (MAG 10-xx series)."
    ),
    "part2": (
        "Focus: **Part II** — Answer to the Statement of Claim; admissions/denials; "
        "reservation to supplement; gaps or denials that may need tightening. "
        "In Gwinnett Magistrate civil cases, align with **MAG 10-13** (Answer / Counterclaim) where the user uses that form or structure."
    ),
    "part3": (
        "Focus: **Part III** — Affirmative defenses; whether each defense is clearly pleaded; "
        "avoid overbroad applications of contract or malpractice law; citation fit. "
        "Remind: party/capacity naming issues in Gwinnett often implicate **MAG 10-09** guidance."
    ),
    "part4": (
        "Focus: **Part IV** — Counterclaim (counts, damages, compulsory counterclaim under "
        "O.C.G.A. § 9-11-13 where relevant); expert affidavit issue (O.C.G.A. § 9-11-9.1); "
        "fee / § 13-6-11 allegations if present. "
        "Service of filed answers/counterclaims in Gwinnett is typically documented with **MAG 10-04** Certificate of Service when served by mail (per court’s form page)."
    ),
    "appendix": (
        "Focus: **Appendix / verified authority** — For each major cite, whether the use "
        "matches the proposition; flag non-primary sources (e.g. law firm pages) used for "
        "holdings; do not re-type long statute blocks from memory."
    ),
}

RESPONSE_CHECKLIST = """
Required response structure (follow in order):
1) **Scope** — State which part of the filing you are addressing this turn.
2) **Vault vs not** — For each legal proposition, say whether SOURCE CHUNKS support it (use <quote chunk="..."> only with real ids from allowed_chunk_ids) or mark **not verified in vault this session**.
3) **Substantive risks** — Neutral list: overstatement, procedure, missing elements, or facts that need record support.
4) **Concrete edits** — Numbered list of specific wording or structural fixes (not a full rewrite unless asked).
5) **Outside this tool** — One short paragraph: what still needs a Georgia-licensed attorney or licensed research (Westlaw/Lexis/court file).

Hard bans: placeholder chunk ids (e.g. chk_XXXXX); claiming statutes/cases are “verified true” without a vault quote; “top 0.01%” / elite-attorney role-play.
"""

AUTO_VERIFICATION_PREAMBLE = """AUTOMATIC CITATION REVIEW
This message is long and/or has several citation-like references. Lawbot already searched for real court text when possible. Your job is to check each authority against SOURCE CHUNKS only — do not invent holdings or statute wording. If the vault is empty, say clearly that nothing was verified here.

"""


def should_use_auto_verification(message: str, extracted_count: int) -> bool:
    if len(message) >= AUTO_LONG_MESSAGE_CHARS:
        return True
    if extracted_count >= AUTO_MIN_CITATION_CANDIDATES:
        return True
    return False


def build_auto_verification_block() -> str:
    """Full-message verification checklist (no section picker required)."""
    checklist = RESPONSE_CHECKLIST.replace(
        "1) **Scope** — State which part of the filing you are addressing this turn.",
        "1) **Scope** — Review the user’s entire message for this turn (whole paste).",
    )
    return (AUTO_VERIFICATION_PREAMBLE.strip() + "\n\n" + checklist.strip()).strip()


def suggested_auto_research_hint(extracted: list[ExtractedCitation]) -> str | None:
    """Bias CourtListener when the user left search blank and auto mode is on."""
    priority = frozenset({"statute", "usc", "lexis", "reporter", "case_name"})
    for e in extracted:
        if e.kind in priority:
            raw = e.raw.strip()
            if len(raw) > 500:
                return raw[:500]
            return raw
    return None


def resolve_review_injection(
    review_pass: str | None,
    review_custom_instruction: str | None,
    message: str,
    extracted_count: int,
) -> tuple[str, str]:
    """
    Returns (text injected before USER MESSAGE, audit label).

    Explicit API section/custom always wins. Otherwise long or citation-heavy messages
    get automatic verification instructions (label ``auto``).
    """
    explicit = build_review_instruction_block(review_pass, review_custom_instruction)
    if explicit:
        pid = (review_pass or "full").strip().lower()
        if pid not in VALID_REVIEW_PASSES:
            pid = "custom"
        return explicit, pid

    if should_use_auto_verification(message, extracted_count):
        return build_auto_verification_block(), "auto"

    return "", "full"


def build_review_instruction_block(review_pass: str | None, review_custom_instruction: str | None) -> str:
    """
    Returns text to inject before USER MESSAGE, or empty string for full-document / default behavior.
    """
    pid = (review_pass or "full").strip().lower()
    if pid not in VALID_REVIEW_PASSES:
        pid = "full"
    if pid in ("", "full"):
        return ""

    if pid == "custom":
        focus = (review_custom_instruction or "").strip()
        if not focus:
            return ""
        return (
            "DOCUMENT SECTION REVIEW (this turn)\n\n"
            f"**Custom focus:** {focus}\n\n"
            "The USER MESSAGE may contain a long filing; prioritize the custom focus above. "
            "Do not reproduce the entire document.\n\n"
            + RESPONSE_CHECKLIST.strip()
        )

    body = SECTION_FOCUS.get(pid, "")
    if not body:
        return ""

    return (
        "DOCUMENT SECTION REVIEW (this turn)\n\n"
        f"{body}\n\n"
        "The USER MESSAGE may contain the full text; address this focus first. "
        "You may briefly note cross-part issues only if critical.\n\n"
        + RESPONSE_CHECKLIST.strip()
    )


def suggested_research_query_suffix(review_pass: str | None) -> str | None:
    """Optional hint for CourtListener when user leaves research_query blank."""
    pid = (review_pass or "full").strip().lower()
    hints = {
        "part1": "Gwinnett County Magistrate Court transfer O.C.G.A. 15-10-45 magistrate jurisdiction",
        "part2": "Gwinnett Magistrate Court answer counterclaim MAG 10-13 Georgia",
        "part3": "Georgia affirmative defenses magistrate civil answer",
        "part4": "Georgia compulsory counterclaim O.C.G.A. 9-11-13 expert affidavit 9-11-9.1",
        "appendix": "Georgia Kellos Sawilowsky Cox-Ott attorney standard of care",
    }
    return hints.get(pid)
