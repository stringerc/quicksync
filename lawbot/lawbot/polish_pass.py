"""Optional second LLM pass: compress redundancy without changing substance."""

from __future__ import annotations

from lawbot.chat_service import MAX_USER_MESSAGE_CHARS


def build_polish_second_pass_user_message(original_user_message: str, first_draft: str) -> str:
    """
    User bundle for a polish-only turn. Keeps the original ask so local templates (e.g. Gwinnett)
    and party/relief context stay visible to the model.
    """
    o = (original_user_message or "").strip()
    d = (first_draft or "").strip()
    core = (
        "POLISH PASS — Reply with only the tightened draft (Markdown). "
        "Follow the system instructions: compress redundancy; do not add new authorities.\n\n"
        "Original user request (preserve parties, relief, and legal theory — editing for length only):\n\n"
        f"{o}\n\n"
        "---\n\n"
        "Draft to tighten — remove duplicate paragraphs and repeated points; merge overlapping bullets; "
        "shorten verbose headings. Preserve names, dates, amounts, and quoted text exactly. "
        "If the draft begins with a court caption (IN THE … COURT, parties, case number, title), keep it at the top unchanged.\n"
        "If the draft ends with --- and ## Editor's overview (not for filing), preserve that section.\n\n"
        f"{d}\n"
    )
    if len(core) <= MAX_USER_MESSAGE_CHARS:
        return core
    # Preserve original ask; truncate draft if absurdly long.
    budget = max(4000, MAX_USER_MESSAGE_CHARS - len(o) - 500)
    d_trunc = d[:budget] + "\n\n---\n[Server: draft truncated for polish pass — ask in parts if needed.]\n"
    return (
        "POLISH PASS — Reply with only the tightened draft (Markdown).\n\n"
        "Original user request:\n\n"
        f"{o}\n\n---\n\nDraft to tighten:\n\n{d_trunc}"
    )
