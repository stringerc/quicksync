# Open-access research vs. Lexis / Westlaw (Lawbot)

Lawbot does **not** integrate LexisNexis, Westlaw, or Shepard’s / KeyCite. Automated retrieval uses **CourtListener** for opinion search and snippets. Users can paste **verbatim** excerpts into the **citation vault** so the model can ground `<quote chunk="…">` tags.

## What “top” practitioners actually use

Elite appellate counsel still rely on **paid** citators and official reporters for **whether** a case remains good law and for **pin cites**. Public websites are not a moral or IQ substitute; they are **convenience** and **starting points**.

## Reasonable open-access complements

| Role | Examples | Caveat |
|------|----------|--------|
| Opinions | CourtListener, Google Scholar case tab, court websites’ PDFs | Verify reporter line, court, date; check later history elsewhere |
| “Case pages” | Justia, FindLaw | Useful navigation; **never** treat as Shepardized |
| Federal statute | Cornell LII | Cross-check current U.S.C. as filed for your proceeding |
| Georgia statutes | Public O.C.G.A. mirrors (e.g. Justia Georgia Code) | Confirm **session** and **official** publication your court expects |

## When Lexis / Westlaw is not affordable (next-best **free** stack)

Nothing free is a **citator** (no KeyCite / Shepard’s replacement). This is a **workflow**, not a guarantee.

1. **Opinion text & quotes:** **CourtListener** (Lawbot can search it) → open the opinion page → copy **verbatim** paragraphs into Lawbot’s **vault** for `<quote chunk>` grounding. **Google Scholar** (Case law) as a second finder; **Justia** case pages for navigation — always confirm **reporter, court, and date** against the **slip opinion or official PDF** when possible.
2. **Georgia statutes:** **law.justia.com/codes/georgia** or other public O.C.G.A. mirrors — confirm you have the **session** your court expects; cross-check a **second** source if the section is dispositive.
3. **Federal / U.S. Supreme Court:** **Cornell LII** + **Supreme Court** slip PDFs from **supremecourt.gov** when applicable.
4. **Later history without a citator:** Search **Google Scholar** / **CourtListener** for **later cases citing** your key case (rough substitute for “what cites this”) — still not treatment flags.
5. **In Lawbot:** Paste **short verbatim excerpts** into the vault; keep **“Look up real court cases”** on so retrieval can load related opinions. The **CITATION MATCH STATUS** section only checks **text overlap** with loaded chunks — not “good law.”

If budget allows later, **paid** research remains the standard for **citator** and **pin-cite** confidence.

## Strengthen-this-filing (automatic behavior)

When the message is classified as **strengthen / improve filing** and **case-law search** is on, the server **always** runs CourtListener retrieval and merges the Georgia/issue **authority query pack** — the **paste-only** option does not apply to that task (see `chat_turn._effective_paste_only_no_research`). That still retrieves **judicial opinions**, not private “winning” motions from other cases.

## Product honesty

- **Editor’s overview** must not imply “sufficient authority” or “winning” cites when the vault is empty or chunks were not used for every proposition.
- **§ 13-6-11** fee allegations should spell out facts supporting **bad faith**, **stubbornly litigious**, and **unnecessary trouble and expense** when those prongs are invoked — not statute-only boilerplate.

Implementation: `lawbot/research_sources.py` (prompt append) and vault copy in `lawbot/static/index.html`.
