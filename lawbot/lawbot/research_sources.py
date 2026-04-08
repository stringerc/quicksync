"""
Open-access legal research context for prompts and UI copy.

Lawbot does not integrate LexisNexis or Westlaw. CourtListener is used for automated retrieval.
Users can paste verbatim excerpts from public sources into the citation vault for <quote chunk> verification.
"""

from __future__ import annotations

# Short list for index.html / tooltips (no endorsement of “winning” — verify before filing).
OPEN_ACCESS_VAULT_HINT_LINES = [
    "CourtListener (courtlistener.org) — opinions; aligns with Lawbot’s automated search",
    "Official court PDFs — Supreme Court of Georgia, Georgia Court of Appeals, federal courts",
    "Google Scholar — Case law tab — verify reporter cite and court",
    "Justia / FindLaw — case pages; treat as a finding aid — verify holding and cite",
    "Cornell LII (law.cornell.edu) — federal statutes and U.S. Code",
    "Georgia Code — law.justia.com/codes/georgia or other public O.C.G.A. mirrors — confirm current session and official source for filing",
]

OPEN_ACCESS_STRICT_APPEND = """
## Open-access authority & verification (strict — document mode)

**Automated retrieval in Lawbot:** The server may load **CourtListener** opinion snippets into **SOURCE CHUNKS**. That is **not** LexisNexis, Westlaw, or Shepard’s/KeyCite. Do **not** tell the user that cites were “verified” or “good law” unless the **verbatim** text appears in a SOURCE CHUNK or the user’s own paste.

**Vault excerpts users may paste:** Verbatim text from **official court PDFs**; **CourtListener**; **Google Scholar** (case law); **Justia** / **FindLaw** (verify reporter, court, and date); **Cornell LII** (federal); **Georgia statutory** text from **law.justia.com/codes/georgia** or another **public** O.C.G.A. source the user treats as authoritative — **always** encourage confirming against the **official** code book or counsel for the operative session.

**Opinions vs. party filings:** SOURCE CHUNKS are **court opinions** (judges), not **party briefs** or motions from other cases — there is no database hook here for “what winning lawyers filed.”

**Do not claim:** “Winning” cases, “top appellate” sourcing, Shepardization, or that free web sources equal paid databases.

**If the user cannot use Lexis/Westlaw:** Point them to **CourtListener** + **Google Scholar** + **Justia** for **finding** opinion text; they should paste **verbatim** excerpts into the vault. **No** free site replaces KeyCite — later-history checks are manual (e.g. more searches), not automated treatment flags.

**O.C.G.A. § 13-6-11:** If the draft seeks **litigation expenses / attorney’s fees** under this statute, the **facts** must **separately** support each **prong** the pleading invokes (typically described as **bad faith**, **stubbornly litigious**, and **unnecessary trouble and expense**) with **specific** allegations tied to **this** dispute — not a bare citation to the statute alone. Use **three labeled subparts** (a)/(b)/(c) or equivalent; each needs **multiple sentences** of conduct, not one merged paragraph.
"""
