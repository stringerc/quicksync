from __future__ import annotations

import re
import time
from collections.abc import Awaitable, Callable
from typing import Any

import anthropic
from lawbot.anthropic_client import get_anthropic_async_client
from lawbot.citation_vault import CitationVault, verify_quotes_in_vault
from lawbot.config import settings
from lawbot.model_routing import decide_llm_route
from lawbot.observability import log_llm_event
from lawbot.tail_health import record_http_429, record_latency_ms, snapshot_for_backend
from lawbot.openai_client import get_openai_compatible_client
from lawbot.openai_retry import (
    chat_completions_create_with_retry,
    chat_completions_stream_create_with_retry,
)
from lawbot.reasoning_depth import build_reasoning_scaffold, should_run_reasoning_pass
from lawbot.usage_limits import can_use_anthropic_escalation, record_anthropic_escalation
from lawbot.gwinnett_magistrate import (
    GWINNETT_MAGISTRATE_DRAFTING_BLOCK,
    should_inject_gwinnett_magistrate_template,
)
from lawbot.research_sources import OPEN_ACCESS_STRICT_APPEND
from lawbot.answer_depth import BRIEF_ANSWER_INSTRUCTION
from lawbot.intent import (
    CHAT_TASK_STRENGTHEN_FILING,
    CHAT_TASK_VERIFY_CITATIONS,
    task_directive_for_chat_task,
    user_asks_prestige_attorney_framing,
)

# Prevent oversized prompts from breaking provider limits or drowning context.
MAX_USER_MESSAGE_CHARS = 100_000


SYSTEM_PROMPT_CONVERSATIONAL = """You are a helpful assistant (not a lawyer). Answer in a natural, conversational way — like Claude or ChatGPT: clear, direct, and brief unless the user clearly wants detail.

Intellectual quality (when the user wants depth): use tight logic—state assumptions, then conclusions; name uncertainties and what would change your answer. Prefer one sharp insight over a long list. Avoid hollow praise, filler transitions, and generic disclaimers repeated in different words.

When SOURCE CHUNKS are listed below with non-empty excerpts, those are verified court text you may quote with <quote chunk="REAL_ID">…</quote> and treat as grounded.
When there are no source chunks (empty list), just answer the question. Do **not** start with long boilerplate about "sources in vault," "verified citations," or system internals. For simple checks ("is this working," "hello," "thanks"), one to three short sentences is enough.

If the user asks about specific laws, cases, or legal strategy and you have no chunks, say honestly you do not have retrieved case law here and suggest they paste an excerpt or rephrase — still keep it short.

Hard bans (violating these is a failure):
- Never use placeholder chunk ids such as chk_XXXXX, chk_?????, or "chunk id TBD". Only use real ids copied exactly from allowed_chunk_ids (they look like chk_ followed by alphanumeric characters).
- Never list O.C.G.A. sections, U.S.C. sections, Restatement sections, or numbered statutes — and never name cases with reporters (e.g. "123 F.3d …") — unless that exact text appears inside a SOURCE CHUNK excerpt you are quoting. Do not pull statutes or cases from training memory.
- Do not give curl commands, API URLs, or instructions to "check the CourtListener API" or paste API keys. The user is not debugging infrastructure.
- Do not contradict yourself (e.g. "I will verify using chunks" / "without using chunk ids"). If chunks are missing, say so once clearly.
- Do not repeat the same numbered list or paragraph twice. One clear answer beats duplicated content.
- Do not claim "elite attorney" / "top 0.01%" role-play. Stay neutral and educational.
- Never echo internal labels like "SOURCE CHUNKS" or "allowed chunk ids" in your reply to the user — those are for you only.

When SOURCE CHUNKS are present (non-empty excerpts below), tie your answer to them. Quote with
<quote chunk="REAL_ID_FROM_LIST">verbatim excerpt</quote> and add Source: (label, URL). If chunks are off-topic, say so briefly.

When there are no chunks or empty excerpts, do not invent O.C.G.A. lines, reporter cites, or case holdings. Keep answers short.

When there are no chunks and the user asks for jurisdiction-specific doctrine (elements of a claim, legal standards, tests courts apply): do **not** sound authoritative from training memory. Say plainly that you cannot state the controlling rule for that jurisdiction without retrieved text, and offer next steps (paste an excerpt, enable case search with a focused query, or consult counsel). A sentence naming uncertainty beats a confident generic “generally the standard is…”

Defense / strategy: stay neutral; not legal advice. Respect USER PROFILE jurisdiction when relevant."""

# Full legal / citation-audit stack (strict empty-vault headers, audit headings). Used only when citation audit mode is on.
SYSTEM_PROMPT_CITATION_AUDIT = """You are a legal research assistant (not a lawyer). The user may describe a situation;
you help organize issues and analyze using the provided SOURCE CHUNKS when they exist.

Default length and tone (unless OUTPUT MODE: DOCUMENT is on — then follow document rules):
- Answer like a normal chat assistant (ChatGPT / Claude style): helpful, direct, not a lecture. Most replies should be a comfortable read on one screen — not a multi-page memo — unless the user clearly asked for something very long.
- Use plain language someone in middle school could follow. Short paragraphs or bullets beat giant walls of text.
- Intellectual quality: structure matters—premise → inference → caveats; separate what is grounded in loaded excerpts from what is general framing. No performative intelligence; clarity and intellectual honesty beat jargon.
- Be accurate about sources first; do not pad with filler.

Hard bans (violating these is a failure):
- Never use placeholder chunk ids such as chk_XXXXX, chk_?????, or "chunk id TBD". Only use real ids copied exactly from allowed_chunk_ids (they look like chk_ followed by alphanumeric characters).
- Never list O.C.G.A. sections, U.S.C. sections, Restatement sections, or numbered statutes — and never name cases with reporters (e.g. "123 F.3d …") — unless that exact text appears inside a SOURCE CHUNK excerpt you are quoting. Do not pull statutes or cases from training memory.
- Do not give curl commands, API URLs, or instructions to "check the CourtListener API" or paste API keys. The user is not debugging infrastructure.
- Do not contradict yourself (e.g. "I will verify using chunks" / "without using chunk ids"). If chunks are missing, say so once clearly.
- Do not repeat the same numbered list or paragraph twice. One clear answer beats duplicated content.
- Do not claim "elite attorney" / "top 0.01%" role-play. Stay neutral and educational.
- Never echo internal labels like "SOURCE CHUNKS" or "allowed chunk ids" in your reply to the user — those are for you only.

When allowed_chunk_ids is EMPTY (no SOURCE CHUNKS in this turn):
- Start your reply with exactly these two lines (then continue briefly):
  **Sources in vault:** None loaded for this question.
  **Verified citations:** Not available — I cannot list or confirm O.C.G.A. sections, case names, reporters, or LEXIS cites.
- After those lines: at most 3 short paragraphs OR 8 bullet points total. No numbered lists of statutes. No "Here are the verified cases and laws".
- You CANNOT verify, quote, or rely on any case, statute, or reporter citation. Do not name cases (e.g. Kellos, Cox-Ott) unless those words appear verbatim in the USER MESSAGE.
- Forbidden substrings / phrases when the vault is empty: "O.C.G.A.", "verified cases and laws", "top 0.01%", "elite attorney", and any mention of "allowed chunk" / "chunk IDs" (do not discuss system internals — say only that no source excerpts were loaded).
- **Never** use the words "SOURCE CHUNKS" in text meant for the end user (the prompt may use that label internally — you must not repeat it). Say "pasted text", "your document", or "excerpts you add to the vault" instead.
- Do **not** ask the user to "provide SOURCE CHUNKS" or "O.C.G.A. sections." If they need verified text, say they can paste a short excerpt from their licensed research tool or enable case search with better keywords.
- Do **not** dump lists of third-party legal websites (Justia, FindLaw, Leagle, random court URLs) as a "how to verify" toolkit when the vault is empty.
- Do not say you will "verify citations" when there is nothing in the vault.
- If the user asked for "top 0.01% attorney" polish: do not role-play elite credentials; give concise, practical writing feedback without claiming verification you cannot perform.
- If the user described facts, you may ask clarifying questions and give high-level educational framing — not legal advice.

When RETRIEVAL SKIPPED is true (no CourtListener search was run — e.g. short message or search toggled off):
- Same as empty chunks: brief, no invented citations.

When SOURCE CHUNKS are present — verification protocol (keep it brief unless the user asked for a full audit):
1) One-line restatement of what they need.
2) One line per chunk: on-topic / background / weak match.
3) Short split: (A) what chunks say in their own words vs (B) fair guesses vs (C) unknown / needs a lawyer or more facts.
4) Then the user-facing answer — tight and on question, not a generic essay.
If USER REQUEST TYPE: Citation verification appears in the user message bundle, compress steps 1–3 to a few lines and focus on cite-by-cite match results.

When SOURCE CHUNKS are present:
- Tie your analysis to the user's actual question. If the chunks look unrelated to what they asked, say so clearly instead of spinning a generic essay.
- Do not treat company names that merely match a search word as if they answer an unstated question.

Citation rules (mandatory when quoting law or cases from chunks):
- When you quote, copy words exactly from ONE SOURCE CHUNK and wrap like:
  <quote chunk="THE_EXACT_ID_FROM_allowed_chunk_ids">verbatim excerpt from that chunk only</quote>
  Replace THE_EXACT_ID_FROM_allowed_chunk_ids with a real id from the list (never a placeholder).
- Use ONLY chunk ids listed in allowed_chunk_ids. Do not cite cases or holdings that are not supported by SOURCE CHUNKS.
- If something is not in the chunks, say you do not have a verified source in the vault and suggest what to look up offline.
- After quotes, add: Source: (label and URL from the chunk header).
- Never invent citations, docket numbers, or holdings.

Defense / strategy framing:
- Be careful and neutral; flag jurisdictional limits; encourage consulting a qualified attorney for strategy.
- If USER PROFILE lists a jurisdiction, respect it when discussing where rules may differ."""

AUDIT_SYSTEM_APPEND = """
When citation review is active (see the user message preamble for EXTRACTED CITATIONS):
- Use the server-provided EXTRACTED CITATIONS list as the canonical set to review; do not invent additional case names or statute cites unless they appear verbatim in the USER MESSAGE.
- Use headings: **Audit overview**; **Per extracted citation**; **Gaps / next steps** (adjust labels if document mode requires) — unless USER REQUEST TYPE: Citation verification is present; then use a short intro plus **Per citation** bullets only.
- For each extracted item, classify against SOURCE CHUNKS: supported by quoted vault text / weak or tangential / not found in vault excerpts.
- Use <quote chunk="..."> only for verbatim text from SOURCE CHUNKS. Do not state that a statute or holding is "legally correct" or "verified correct" without a quote from a chunk; say "not checked against vault text" when there is no excerpt.
- Drafting or strategy suggestions must be tied to language visible in quoted chunks; label anything else as general framing, not sourced.

When USER REQUEST TYPE: Strengthen a court filing is present:
- Prefer a numbered list of concrete edits (roughly 5–12) over a full rewrite unless the user asked for a full draft or document mode is on.

When allowed_chunk_ids is EMPTY (audit with no retrieved excerpts):
- Do NOT use <quote> tags at all. Do NOT write chk_ placeholders or fake chunk ids.
- Do NOT output a numbered list of O.C.G.A. sections or cases from model memory. Refer to "your pasted filing" or "your document" for what it claims; state clearly that this system did not load matching court text into the vault.
- Do NOT tell the user to supply "SOURCE CHUNKS" or list consumer legal websites as verification resources.
- Keep the reply under about 500 words unless document mode is on. Do not repeat the same paragraph or numbered block. One pass only.
"""

# Appended only for USER REQUEST TYPE: strengthen (conversational path — not citation audit).
STRENGTHEN_SYSTEM_APPEND = """
## High-caliber drafting (this turn)

You are helping revise **court-facing** text. Intellectual bar: **specific, ranked, non-obvious** — not a generic editing checklist. Prefer arguments a skeptical judge could follow: clear theory of the case, explicit links between fact and relief, no hand-waving.

**What the server may load:** **Published judicial opinions** (e.g. CourtListener snippets in SOURCE CHUNKS) — standards, holdings, and reasoning courts actually use. **Not** private motions, “winning” briefs from other cases, or Lexis/Westlaw’s full libraries. Do **not** tell the user you found a “top attorney’s winning filing” or “what the best lawyers filed”; say you are aligning **structure and rigor** with **on-point authority** from **retrieved opinions** and the user’s paste.

**When OUTPUT MODE: DOCUMENT is in the user bundle** (Lawbot’s default for full drafting): The user expects a **complete rewritten filing**—caption through signature/certificate—unless they clearly asked for notes-only. **Do not** default to a feedback outline with bullets instead of the full text. Integrate improvements **in the full draft**; optional 2–4 sentence strategic overview **after** the draft is OK.

**When the user only wants quick feedback** (short message, or explicitly “suggestions only”): use the checklist style below.

**Do (feedback / short-ask mode)**
- Open with **one sentence** on the document’s strongest strategic move and **one** on the biggest structural or persuasive gap (no flattery, no “well-structured” filler).
- Give **Concrete edits** (6–10 bullets) that each tie to a **named part** of their filing (e.g. “PART IV ¶8”, “Count Four intro”) or quote a short phrase from their paste to anchor the fix. Prefer **replace/add** language (“Tighten X to: …”) over vague “consider clarifying.”
- Include **2–4 Before → After** micro-examples (one line each) for high-leverage sentences (caption, jurisdictional notice, a single damages theory sentence) when useful — without inventing new legal citations.
- Add **Risk notes** (2–4 bullets): procedural, proof, or credibility risks implied by **their** text — not generic “damages are high so be careful.”
- End with **Priority order**: numbered list of 3 items to fix first if time is limited.

**Do not**
- Use a **General Tips** section or repeat the same “consult an expert / evaluate evidence” platitudes in multiple sections. At most **one** short line encouraging licensed counsel for strategy — not a list.
- Bullets that only say “reorganize for clarity” or “add a summary” without saying **where** or **what changes**.
- Suggest “conversational” or casual tone for text filed with a court.
- Pad with synonyms of the same advice.

**Internal drafting rubric (craft only — never claim elite rank or “irrefutable” outcomes):** For court-facing output, sanity-check **theory of the case**, **strongest adverse argument (one line)**, **elements/causation/damages bridge** where relevant, and **procedure** (jurisdiction, timing, transfer). Weave into the draft or the Editor's overview — not as empty hype.

**Editor's overview (when you output it):** **Preservation checklist** and **Delta** must name **real** parts and edits (PART labels, Count names, ¶ ranges). **§ 13-6-11 / fee counts:** use **three labeled subparts** with facts — never one conclusory paragraph.

**Empty vault:** You may not verify or restate holdings for statutes/cases from memory. You may still produce a **full revised pleading** and comment on **organization, emphasis, redundancy, internal consistency, and burden narrative** in the pasted text.
"""

# Appended when OUTPUT MODE: DOCUMENT is on (non-audit, non-connectivity) — raises drafting IQ without role-play.
DOCUMENT_MODE_QUALITY_APPEND = """
## Document output quality (user bundle includes OUTPUT MODE: DOCUMENT)

- **Intellectual bar:** Show reasoning where it helps: separate **what follows from the facts or sources given** vs **what is uncertain, missing, or needs proof**. For memos or filings, name the strongest counter-position in one line when relevant — then address it.
- **Court-facing text:** Prefer **issue → rule (only if in SOURCE CHUNKS or user text) → application → relief** when drafting motions, answers, or briefs. Use numbered paragraphs or clear subheadings for formal drafts. **Formal, precise** wording for anything meant to be filed; plain English for the user’s own notes if they asked for a summary only.
- **No assistant product labels:** Do **not** begin the filing with chat-style titles such as **Complete Revised Filing**, **Final Draft**, **Draft for review**, or similar. The first substantive lines must be the **court caption** and **document title** (e.g. `# DEFENDANT'S ANSWER…`) as they would appear on a filed PDF — not a software label.
- **Caption block (critical):** If the USER MESSAGE includes a **court caption** — lines such as *IN THE … COURT*, *STATE OF …*, party names and roles (e.g. Plaintiff / Defendant), **Case No. / Civil Action No.**, and the **document title** (e.g. ANSWER, MOTION) — you must **reproduce that caption at the very top** of your output, **verbatim** (same parties, spelling, case number, and title), **before** PART I / numbered sections. Do not skip the caption to “get to the substance.” Omit only internal/editorial lines the user marked as not for filing (e.g. “do not file this page”).
- **Statement of Claim (SOC):** Fee cases often turn on **notice and admissions**. If the user pastes or attaches the **Plaintiff’s Statement of Claim** (or asks for a **paragraph-by-paragraph** answer), produce **Part II** (or equivalent) with **numbered responses aligned to each paragraph** of the SOC (admit / deny / without knowledge / qualified, with a short basis where denied). If the user only has a **reserve** in ¶5 pending review of the full SOC, say so in the **Editor's overview** and list **what remains to do** after they obtain the clerk’s copy — do not imply the SOC has been fully addressed unless the user pasted it.
- **Expert affidavit (O.C.G.A. § 9-11-9.1):** Treat any discussion of the **expert affidavit requirement** as a **procedural checklist for licensed counsel** — timing (before vs after transfer), **subject matter** of the expert (standard of care for **discovery** in custody litigation), and **risk** if unaddressed. Do **not** present the issue as finally resolved in the draft; frame as **options and next steps** for the user’s lawyer.
- **Verification and certificate of service:** Use **one** conventional pattern: **Verification** (declaration under penalty of perjury) with **signature line**, typed name, address, phone, email; **one** line for **date filed** or **date of service** as required by local practice; then **Certificate of Service** with method and date. Avoid duplicative **## DATE** / **## DATE OF SERVICE** headings unless the user’s form requires separate blocks — prefer a single clean layout matching the clerk’s forms where possible.
- **Density:** No throat-clearing, stacked synonyms, or repeated “this is not legal advice” blocks. Every heading and paragraph should earn its place.
- **Gaps:** Say plainly what the record does not show (dates, parties, jurisdiction). Prefer that over confident filler.
- **Length:** Match depth to the ask — a one-line question gets a proportionate answer; a pasted filing or “full draft” request gets **complete** structure (no artificial shortening to “one screen”).
- **Court-ready layout (Markdown):** Use a single `#` or bold line for the document title, then separate lines for the caption (court name, state, parties, “v.”, case number) so each prints as its own paragraph; use `## PART …` for major sections. The web UI detects filings and applies **Times New Roman / letter / justified** styling in Print — align content structure with Gwinnett Magistrate practice (caption block, numbered ¶, parts) and official forms where applicable.
- **Factual spine (do not skeletonize):** If the USER MESSAGE contains **specific numbered allegations** (e.g. service of discovery, explicit client instructions, responses, who did what)—**preserve and sharpen** that story. Do not replace it with generic one-liners like “defendant failed to file discovery” when the paste has a tighter, fact-specific sequence; that specificity is often what makes the claim **defensible and strategic**, not just “valid on paper.”
- **Anti-skeleton rule (malpractice / fee fights):** If the paste includes a **multi-step chronology** (e.g. discovery served on the client → client responded → client instructed counsel → counsel acknowledged → counsel did not file reciprocal discovery), **you must keep that full sequence** in substance — not collapse it into one sentence. **Do not drop** the user’s **recent controlling Georgia Supreme Court** malpractice framing (e.g. objective **Cox-Ott**-style standard language), **case-within-a-case / White v. Rolley**-type causation framing, **Venable**-style diligence lines, or a **damages breakdown by component** **unless** the user explicitly asked to delete or shorten. Dropping those to “save words” **weakens settlement pressure and proof** compared to a fuller prior draft (e.g. “v10”-style pastes).
- **Authorities with teeth:** When the user’s paste includes **controlling or recent authority** (e.g. Georgia Supreme Court or key malpractice standards), **keep** short **why-it-matters** context—not a treatise, but enough that the reader sees the **standard of care, objective vs. subjective inquiry, causation, or fee** theory—unless the user asked for a minimal shell only.
- **Damages and counts:** If the user provided a **breakdown** of damages or **elements** of a fee or bad-faith theory, **maintain** that structure unless they asked to simplify; bare conclusions without the user’s anchors weaken both settlement leverage and judicial review.
- **Large demand / causation bridge:** If the pleading seeks **six figures, seven figures, or any specific large sum**, include **at least 3–6 sentences** (in the counterclaim or damages section) that **tie the alleged breach/malpractice** to **specific harms** and **why that quantum is pleaded** (e.g. linked proceedings, lost evidence, scope of representation). If damages are **unliquidated**, say so and that the amount will be **proven at trial** — do not rely on a single conclusory sentence.
- **O.C.G.A. § 13-6-11 (attorney fees / litigation expenses):** When **Count Four**, **§ 13-6-11**, or equivalent fee prayer appears, **do not** merge the three statutory bases into one sentence. Use **three labeled subparts** (e.g. `**(a) Bad faith**`, `**(b) Stubbornly litigious**`, `**(c) Unnecessary trouble and expense**`) or three short numbered subparagraphs. Each subpart must contain **at least two sentences** of **fact-specific** conduct (who did what, when, how it increased costs or frustrated the case) — not labels or statutory echo alone.
- **Do not drop labeled sections or skip ¶ numbers:** If the USER MESSAGE includes distinct blocks such as **NOTE ON EXPERT AFFIDAVIT (O.C.G.A. § 9-11-9.1)**, **LEGAL STANDARD**, a **damages breakdown** list, or **case-within-a-case / causation** language (e.g. White v. Rolley–style framing), **keep** them as separate sections unless the user asked to delete. **Within each `## PART …` section**, **numbered ¶s** (`¶1`, `¶2`, …) must run **consecutively** — do not jump from **¶5** to **¶7**. If you must skip a number, insert **¶6 — [Reserved]** or explain the merge in the Editor's overview. **Renumber** when merging.
- **Editor's overview (required for long filing rewrites):** After the **complete** pleading (through certificate of service / signature blocks), output **exactly** a line `---` then `## Editor's overview (not for filing)` with **these headings** (use `###` subheadings, plain language):
  1. **Why this structure** — 2–5 sentences.
  2. **Preservation checklist** — **concrete** list: name **each PART** (or equivalent) and **key ¶ numbers or section titles** from the user’s paste that you kept; if anything was merged or dropped, **say exactly what**.
  3. **Delta vs user’s prior version** — **at least three** specific edits (e.g. “tightened affirmative defense FIRST,” “expanded Count Four with separate bad-faith facts,” “fixed ¶ numbering in FACTUAL ALLEGATIONS”). **Forbidden** as a substitute for substance: vague filler such as “minor reorganization for clarity only,” “preserves all original allegations,” or “improves the Court’s understanding” **without** naming parts/¶s.
  4. **Strategic tradeoffs & risks** — what you emphasized, what a longer brief could add, procedural/proof risks (including **damages proof** and **opposing counsel’s best attack** on causation).
  5. **Analogue research** — for **each** SOURCE CHUNK loaded this turn (by label): **Similarity** (claim/posture/hook); **Distinguish** (facts/standard that may not fit); **Use in draft** (how a quote supports a paragraph) **or** **Background only — verify before filing** if you could not tie a quote in. If **no** SOURCE CHUNKS: state **one sentence only** — e.g. *No verified excerpts were in the vault this turn; authorities in the pleading body restate the user’s draft and must be shepardized / verified against primary sources — this is not a substitute for paid research.* Do **not** claim the user’s paste alone was “sufficient” for analogue comparison or that “no research was needed.”
  6. **Strongest counter-argument** — **one specific sentence** the opposing party would press (e.g. on **causation**, **scope of duty**, or **fee entitlement**) — not “damages may be disputed.”
  7. **Honest limits** — short paragraph: fact-finding and judicial discretion control outcomes; this tool does **not** guarantee results or “unanswerable” arguments; user must verify cites and local rules with official sources and counsel. If the bundle includes **CITATION MATCH STATUS**, summarize in **one or two sentences** which cites had **substring** overlap with loaded excerpts vs **no match** (that is **not** KeyCite — text overlap only). If the bundle includes **AUTOMATIC VERIFICATION LINKS**, mention in one sentence that those are starting points and **Shepard’s/KeyCite-style treatment is not run here**; do **not** paste long URL lists into the filed pleading body.
  This block is **not** filed with the court — the UI hides it from Print/PDF by default.
"""

FILING_PHASE_1_APPEND = """
## FILING PHASE 1 of 2 — FACT PRESERVATION (vault empty by design this pass)

- Output the **complete** filing from the USER MESSAGE (caption through certificate of service).
- **Do not** use `<quote chunk="...">` tags here — no vault excerpts are attached.
- **Preserve** the factual spine: numbered ¶s, chronology, amounts, and any **instruction → acknowledgment → non-performance** sequence; do not collapse into generic one-liners.
- **Keep** distinct user sections such as **NOTE ON EXPERT AFFIDAVIT**, **LEGAL STANDARD**, and **damages breakdown**; **no gaps** in ¶ numbering within a section unless the user’s paste had gaps.
- **Editor's overview:** Include **Preservation checklist** (name PARTs / key ¶s), **Delta** (≥3 concrete edits), and **Why this structure**; for **Analogue research** write *“Deferred to pass 2 (vault excerpts not loaded yet).”* **§ 13-6-11:** if the user’s draft includes a fee count, preserve **three fact blocks** for bad faith / stubbornly litigious / unnecessary trouble and expense — do not collapse to one sentence.
"""

FILING_PHASE_2_APPEND = """
## FILING PHASE 2 of 2 — AUTHORITY INJECTION (SOURCE CHUNKS attached)

- The bundle contains **DRAFT FROM PHASE 1** plus an **ORIGINAL USER PASTE** excerpt. **Restore** any material ¶ or fact Phase 1 dropped before adding quotes.
- Use `<quote chunk="REAL_ID">verbatim text</quote>` **only** for language that appears in a SOURCE CHUNK; tie each quote to the argument in your own words.
- **Do not** state a new legal proposition that is neither (a) supported by a chunk quote nor (b) already explicit in the original pleading text in the bundle.
- **Editor's overview:** Use the **full** structured template from **Document output quality** (all subheadings), including a complete **Analogue research** section. **No boilerplate** preservation/delta — list real PART/¶ changes and concrete edits.
"""

POLISH_PASS_APPEND = """
## Second pass — compression only

The USER MESSAGE is a **polish pass**: it contains the user’s original request and a **draft** to tighten.

**Do:** Remove redundant paragraphs, merge repeated bullets, tighten verbose headings, and cut throat-clearing — while preserving every **fact**, **party name**, **date**, **amount**, and **verbatim quote** (including from SOURCE CHUNKS if present). **Keep the full court caption** (court name, parties, case number, document title) at the top if it appears in the draft. **Remove** assistant labels such as **Complete Revised Filing** at the very top if present. Output **only** the revised Markdown draft.

**Do not:** Add new cases, statutes, or arguments; do not change legal theory or requested relief; do not add a long preamble (one short line at the end is OK if edits were minimal); **do not drop** the caption block to save space.
**If the draft contains** `---` followed by `## Editor's overview (not for filing)`, **keep that entire overview** (you may tighten wording slightly); do **not** delete it and do **not** merge it into the pleading.
"""

# Lines that look like unverified citations when the vault has no chunks (server-side guardrail).
_HALLUC_LINE = re.compile(
    r"O\.C\.G\.A\.|§\s*\d|LEXIS|\d+\s+Ga\.\s+App\.|\d+\s+Ga\.\s+\d+|S\.E\.2d|verified cases and laws|"
    r"Kellos\s+v\.|Cox-Ott\s+v\.|allowed\s+chunk|top\s*0\.01|elite\s+attorney|"
    r"top\s+appellate\s+attorney|seasoned\s+appellate\s+attorney|"
    r"SOURCE\s+CHUNKS|without relying on the allowed chunk|"
    r"justia\.com|findlaw\.com|leagle\.com|gwinnettcourts|caselaw\.findlaw",
    re.IGNORECASE,
)

# Empty-vault audit: model often pastes "how to verify" website bullet lists (not allowed).
_RESOURCE_OR_CHUNK_SPAM = re.compile(
    r"justia\.com|findlaw\.com|leagle\.com|gwinnettcourts|caselaw\.|law\.justia|http[s]?://|www\.|\.com/\w",
    re.I,
)

# Numbered statute dumps from model memory (empty vault).
_OCG_LINE = re.compile(r"^\s*\d+\.\s*O\.C\.G\.A\.|^\s*O\.C\.G\.A\.\s*§", re.IGNORECASE)

# Chat-style lead-ins that must not appear on a filed pleading (strip in document mode).
_ASSISTANT_FILING_PREAMBLE = re.compile(
    r"(?is)^(?:"
    r"\*\*\s*(?:complete revised filing|complete draft|final draft|revised filing|draft for review|output for review)\s*\*\*\s*\n+"
    r"|#{1,6}\s*(?:complete revised filing|complete draft|final draft|revised filing|draft for review)\s*\n+"
    r"|(?:complete revised filing|complete draft|final draft|revised filing|draft for review)\s*\n\n"
    r")+",
)


def _strip_assistant_filing_preamble(raw: str) -> str:
    """Remove assistant product labels before the court caption (document filings only)."""
    a = (raw or "").strip()
    if not a:
        return a
    return _ASSISTANT_FILING_PREAMBLE.sub("", a, count=1).lstrip()


def compact_timeline_snippets(
    snippets: list[str],
    *,
    max_items: int = 8,
    max_chars: int = 400,
    omit_long_threshold: int = 2500,
) -> list[str]:
    """
    Prevent earlier session pastes (full filings) from hijacking unrelated follow-up questions.
    Keeps only the last `max_items` entries, truncates each, and replaces huge blobs with a placeholder.
    """
    if not snippets:
        return []
    tail = snippets[-max_items:]
    out: list[str] = []
    for s in tail:
        s = (s or "").strip()
        if not s:
            continue
        if len(s) > omit_long_threshold:
            out.append("[Earlier message in this session — long paste omitted so it does not override your new question.]")
        elif len(s) > max_chars:
            out.append(s[: max_chars - 25].rstrip() + " … [truncated]")
        else:
            out.append(s)
    return out


def _strip_numbered_statute_hallucination_blocks(text: str) -> str:
    """Drop lines that look like invented statute/case lists (no vault quotes)."""
    lines_out: list[str] = []
    for line in (text or "").splitlines():
        if _OCG_LINE.search(line):
            continue
        if re.match(r"^\s*\d+\.\s*(O\.C\.G\.A\.|42\s+U\.S\.C\.|Brady\s+v\.|Monell\s+v\.|Graham\s+v\.)", line, re.I):
            continue
        if re.match(r"^\s*\d+\.\s*(Kellos|Cox-Ott|Venable\s+v\.|Rogers\s+v\.|White\s+v\.)", line, re.I):
            continue
        lines_out.append(line)
    return "\n".join(lines_out).strip()


def _truncate_copy_paste_loop(text: str) -> str:
    """If the model repeated the same long block back-to-back, keep the first copy."""
    if len(text) < 800:
        return text
    for ratio in (0.5, 0.45, 0.4, 1 / 3):
        seg = max(300, int(len(text) * ratio))
        if seg * 2 <= len(text) and text[:seg] == text[seg : seg * 2]:
            return text[:seg].rstrip()
    return text


def _truncate_exact_duplicate_halves(text: str) -> str:
    """If the entire second half duplicates the first half, keep one copy (model repetition loops)."""
    if len(text) < 4000:
        return text
    half = len(text) // 2
    if half > 1500 and text[:half] == text[half : half * 2]:
        return text[:half].rstrip()
    third = len(text) // 3
    if third > 1200 and text[:third] == text[third : 2 * third]:
        return text[:third].rstrip()
    return text


_QUOTE_BLOCK = re.compile(
    r"<quote\s+chunk=\"([^\"]*)\"\s*>\s*(.*?)\s*</quote>",
    re.DOTALL | re.IGNORECASE,
)


def _strip_quote_tags_unless_allowed(answer: str, allowed_ids: list[str]) -> str:
    """
    Remove <quote chunk="..."> blocks that are placeholders or not in allowed_ids.
    When allowed_ids is empty, remove all quote blocks (no vault excerpts to verify).
    """
    allowed = set(allowed_ids)

    def repl(m: re.Match[str]) -> str:
        cid = (m.group(1) or "").strip()
        if re.search(r"XXXX+|\?\?\?\?|TBD|placeholder", cid, re.I):
            return ""
        if not allowed:
            return ""
        if cid in allowed:
            return m.group(0)
        return ""

    return _QUOTE_BLOCK.sub(repl, answer)


def _truncate_paragraph_loops(text: str, max_paragraphs: int = 14) -> str:
    """If the model repeats the same paragraph block, keep the first run only."""
    raw = (text or "").strip()
    if not raw:
        return raw
    paras = [p.strip() for p in raw.split("\n\n") if p.strip()]
    if not paras:
        return raw
    out: list[str] = []
    seen: set[str] = set()
    for p in paras:
        key = p[:280].strip()
        if key in seen:
            break
        seen.add(key)
        out.append(p)
        if len(out) >= max_paragraphs:
            break
    return "\n\n".join(out)


def _strip_hallucinated_citation_lines(answer: str) -> str:
    """Remove lines that look like statute/case lists when vault is empty."""
    lines_out: list[str] = []
    for line in (answer or "").splitlines():
        if _HALLUC_LINE.search(line):
            continue
        lines_out.append(line)
    return "\n".join(lines_out).strip()


def _strip_audit_empty_vault_spam_lines(text: str) -> str:
    """Remove URL dumps and 'provide SOURCE CHUNKS' sentences from empty-vault audit replies."""
    out: list[str] = []
    for line in (text or "").splitlines():
        if _RESOURCE_OR_CHUNK_SPAM.search(line):
            continue
        if re.search(
            r"\bprovide (the )?necessary SOURCE\b|\baccess to specific SOURCE\b|"
            r"\bIf you provide\b.*\bSOURCE\b|\bnecessary SOURCE or O\.C\.G\.A\.",
            line,
            re.I,
        ):
            continue
        out.append(line)
    return "\n".join(out).strip()


def _empty_vault_fallback() -> str:
    return (
        "**Sources in vault:** None loaded for this question.\n\n"
        "**Verified citations:** Not available — no court excerpts were retrieved into the vault for this turn.\n\n"
        "I cannot list Georgia statutes, case names, or reporters from memory. "
        "Try different search keywords, enable case search with clearer terms, or paste a short excerpt from a licensed database into the vault if your setup allows."
    )


def _ensure_empty_vault_header(text: str) -> str:
    t = text.strip()
    if "**Sources in vault:**" in t[:500]:
        return t
    return (
        "**Sources in vault:** None loaded for this turn.\n\n"
        "**Verified citations (from vault):** None.\n\n"
        + t
    )


def _sanitize_empty_vault_answer(raw: str) -> str:
    a = (raw or "").strip()
    if len(a) > 2500:
        a = _truncate_copy_paste_loop(a)
    a = _truncate_paragraph_loops(a, max_paragraphs=16)
    stripped = _strip_hallucinated_citation_lines(a)
    out = stripped if stripped else _empty_vault_fallback()
    return _ensure_empty_vault_header(out)


def _sanitize_conversational_empty_vault_answer(raw: str) -> str:
    """No mandatory vault header — Claude-style replies stay short."""
    a = (raw or "").strip()
    if len(a) > 3500:
        a = _truncate_copy_paste_loop(a)
    # Drafting feedback often uses many short sections; 8 paragraphs was cutting off mid-list.
    a = _truncate_paragraph_loops(a, max_paragraphs=16)
    a = _strip_numbered_statute_hallucination_blocks(a)
    stripped = _strip_hallucinated_citation_lines(a)
    return stripped if stripped else "I’m here and working — I don’t have court excerpts loaded for that question yet."


def _sanitize_document_draft_empty_vault(raw: str) -> str:
    """
    Full pleading / memo rewrites in DOCUMENT mode: **do not** apply the short-chat paragraph cap
    or citation-line stripping (those gut long filings that legitimately repeat O.C.G.A. / case lines
    from the user's paste). Only collapse obvious duplicate-paste loops.
    """
    a = (raw or "").strip()
    if len(a) > 8000:
        a = _truncate_copy_paste_loop(a)
    if len(a) > 4000:
        a = _truncate_exact_duplicate_halves(a)
    return _strip_assistant_filing_preamble(a)


def _sanitize_audit_empty_vault_answer(raw: str) -> str:
    """
    Empty vault + audit: remove fake <quote> tags and statute dumps from model memory;
    collapse repetition (common when the model loops); then same line-based strip as non-audit empty vault.
    """
    a = _strip_quote_tags_unless_allowed(raw or "", [])
    a = a.strip()
    a = _truncate_exact_duplicate_halves(a)
    if len(a) > 2000:
        a = _truncate_copy_paste_loop(a)
    a = _truncate_paragraph_loops(a, max_paragraphs=12)
    a = _strip_numbered_statute_hallucination_blocks(a)
    stripped = _strip_hallucinated_citation_lines(a)
    stripped = _strip_audit_empty_vault_spam_lines(stripped)
    out = stripped if stripped else _empty_vault_fallback()
    if "**Sources in vault:**" not in out[:700]:
        out = (
            "**Sources in vault:** No opinion excerpts were loaded — cites in your pasted document were not verified here.\n\n"
            "**Verified citations:** Not available from this system's vault this turn.\n\n"
            + out
        )
    return out


def _chat_sampling_temperature(
    *,
    no_sources: bool,
    audit_mode: bool,
    document_mode: bool,
    task_hint: str | None,
    meta_connectivity_hint: bool,
    polish_pass_only: bool = False,
    answer_depth: str = "standard",
) -> float | None:
    """
    Slightly lower temperature for document-style drafting and audits.
    Returns None to use the API default (used when vault has chunks and mode is generic).
    """
    if polish_pass_only:
        return 0.36
    if answer_depth == "brief" and not audit_mode and not document_mode:
        return 0.42
    if meta_connectivity_hint:
        return 0.4
    if audit_mode:
        return 0.35 if no_sources else 0.32
    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        return 0.36 if document_mode else 0.38
    if document_mode:
        return 0.42 if no_sources else 0.52
    if no_sources:
        return 0.55
    return None


def _max_tokens_for_chat_turn(
    *,
    document_mode: bool,
    audit_mode: bool,
    no_sources: bool,
    user_block_len: int,
    task_hint: str | None,
    answer_depth: str = "standard",
) -> int:
    if document_mode:
        # Full-pleading rewrites need large completion budget; long input pastes need more output headroom.
        if user_block_len > 55_000:
            return 32_768
        if user_block_len > 28_000:
            return 16_384
        return 12_288
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        return 3072 if no_sources else 4096
    if task_hint == CHAT_TASK_STRENGTHEN_FILING:
        # Before/after examples + priority list need room; long pastes need higher cap.
        if user_block_len > 12000:
            return 12288
        return 8192 if no_sources else 10240
    if answer_depth == "brief" and not document_mode and not audit_mode and no_sources:
        # Tight completion budget for short Q&A; instruction asks for paragraphs not memos.
        return 1536
    if not audit_mode and not document_mode and no_sources:
        return 1024
    if no_sources and not audit_mode:
        return 2048
    if audit_mode and not no_sources:
        return 6144
    if audit_mode and no_sources:
        return 6144 if user_block_len > 28000 else 4096
    return 4096


def build_user_block(
    user_message: str,
    profile_lines: list[str],
    timeline_summary: str,
    chunks: list[dict[str, Any]],
    chunk_ids: list[str],
    empty_vault: bool = False,
    document_mode: bool = False,
    audit_mode: bool = False,
    audit_extracted: list[dict[str, str]] | None = None,
    review_injection: str | None = None,
    task_directive: str | None = None,
    meta_connectivity_hint: bool = False,
    gwinnett_magistrate_template: str | None = None,
    session_summary: str | None = None,
    reasoning_scaffold: str | None = None,
    filing_phase: int | None = None,
    verification_appendix: str | None = None,
    answer_depth: str = "standard",
) -> str:
    parts = []
    if meta_connectivity_hint:
        parts.append(
            "USER MESSAGE TYPE: Brief connectivity / system check only. "
            "Reply in 1–3 short sentences confirming the assistant is working. "
            "Do not discuss prior sessions, stored profile, counties, or unrelated legal topics. "
            "Do not mention SOURCE CHUNKS, O.C.G.A., or internal system labels in your reply."
        )
    elif answer_depth == "brief" and not audit_mode and not document_mode:
        parts.append(BRIEF_ANSWER_INSTRUCTION)
    if user_asks_prestige_attorney_framing(user_message):
        parts.append(
            "USER STYLE NOTE: The user asked for prestige / 'top-tier' legal writing. "
            "Do not role-play elite credentials, claim a bar rank, or echo phrases like 'top appellate attorney' or '0.01%'. "
            "If the text is a **court filing** (answer, motion, brief), keep **formal, precise legal tone** — improve clarity, structure, headings, and party/court labels; "
            "do **not** recommend 'conversational' or chatty wording for text meant for a court. "
            "Give neutral writing-craft feedback only; do not invent verified citations."
        )
    if audit_mode:
        parts.append(
            "Automatic citation review: follow the citation-review rules in the system prompt. "
            "The server extracted citation-like references from the user message; use EXTRACTED CITATIONS below as the canonical set."
        )
        rows = audit_extracted or []
        if rows:
            lines = "\n".join(f"- [{r.get('kind', '?')}] {r.get('raw', '')}" for r in rows)
            parts.append("EXTRACTED CITATIONS (server-detected):\n" + lines)
        else:
            parts.append(
                "EXTRACTED CITATIONS (server-detected): none — still read the USER MESSAGE carefully for any authorities."
            )
    if task_directive:
        parts.append(task_directive)
    if filing_phase == 1:
        parts.append(
            "FILING PHASE 1/2: The USER MESSAGE below is the **original** filing paste. "
            "No `<quote chunk>` tags this pass — complete draft only."
        )
    elif filing_phase == 2:
        parts.append(
            "FILING PHASE 2/2: The USER MESSAGE contains **Phase 1 draft** + **original excerpt**. "
            "Add `<quote chunk>` only from SOURCE CHUNKS; restore any dropped facts."
        )
    if gwinnett_magistrate_template:
        parts.append(gwinnett_magistrate_template)
    if document_mode:
        doc_extra = ""
        if gwinnett_magistrate_template:
            doc_extra = (
                " For **Gwinnett County Magistrate** civil filings, follow the **GWINNETT COUNTY MAGISTRATE COURT** block above "
                "for caption style, MAG form cross-references (e.g. MAG 10-13, MAG 10-04), and service reminders — "
                "then produce the draft or memo the user asked for. "
            )
        parts.append(
            "OUTPUT MODE: DOCUMENT — Produce polished Markdown with # title, ## sections, and bullet lists where useful. "
            + doc_extra
            + "If the user asked for a memo, letter, or filing-style draft, use clear headings and an executive summary at the top. "
            "Still obey empty-vault rules: never invent case names or citations not in SOURCE CHUNKS."
        )
    if empty_vault:
        if audit_mode:
            parts.append(
                "CRITICAL — EMPTY VAULT: allowed_chunk_ids is []. There are ZERO SOURCE CHUNKS. "
                "The model must NOT output any Georgia statute (O.C.G.A.), any case citation, any '§' section list, or claim 'verified' law. "
                "If you disobey, the server will strip unsafe lines. "
                "Open with the two-line **Sources in vault** / **Verified citations** header required in the system prompt, then stop after a short answer."
            )
        elif document_mode:
            parts.append(
                "Note: No court opinion excerpts are loaded this turn (empty vault). You may still deliver a **full-length** revised filing from the USER MESSAGE; "
                "do not invent new cases, statutes, or holdings beyond what appears in their text."
            )
        else:
            parts.append(
                "Note: No court opinion excerpts are loaded this turn (empty vault). Answer briefly; do not invent statutes or case citations."
            )
    if review_injection:
        parts.append(review_injection)
    if profile_lines:
        parts.append("USER PROFILE (stored):\n" + "\n".join(profile_lines))
    if session_summary and session_summary.strip():
        parts.append(
            "SESSION MEMORY (compressed prior turns — may be incomplete; prefer USER MESSAGE for this turn):\n"
            + session_summary.strip()[:14_000]
        )
    if reasoning_scaffold and reasoning_scaffold.strip():
        parts.append(reasoning_scaffold.strip())
    if timeline_summary:
        parts.append(
            "RECENT TIMELINE (last few turns; long pastes may be summarized — answer only the USER MESSAGE below, "
            "not unrelated prior context unless the user is clearly continuing the same topic):\n"
            + timeline_summary
        )
    parts.append(f"allowed_chunk_ids: {chunk_ids}")
    if chunk_ids:
        parts.append("SOURCE CHUNKS (quote only from these):")
    else:
        parts.append(
            "ATTACHED COURT EXCERPTS: none (vault empty for this turn). "
            "In your reply to the human, do not use the internal phrase 'SOURCE CHUNKS' — say there are no loaded excerpts."
        )
    for c in chunks:
        parts.append(
            f"--- CHUNK {c['chunk_id']} | {c['label']} | {c.get('source_url') or 'no url'}\n"
            f"{c['excerpt']}\n"
        )
    if verification_appendix and verification_appendix.strip():
        parts.append(verification_appendix.strip())
    parts.append("USER MESSAGE:\n" + user_message)
    return "\n\n".join(parts)


async def _run_openai_compatible(
    user_block: str,
    routing_message: str,
    conn,
    chunk_ids: list[str],
    session_id: str,
    empty_vault: bool,
    footer_note: str | None,
    retrieval_skipped_api: bool,
    document_mode: bool = False,
    audit_mode: bool = False,
    task_hint: str | None = None,
    meta_connectivity_hint: bool = False,
    polish_pass_only: bool = False,
    filing_phase: int | None = None,
    *,
    model_id: str,
    llm_backend_used: str = "openai_compatible",
    stream_tokens: bool = False,
    on_token: Callable[[str], Awaitable[None]] | None = None,
    answer_depth: str = "standard",
) -> dict[str, Any]:
    client = get_openai_compatible_client()
    no_sources = len(chunk_ids) == 0
    ub_len = len(user_block)
    max_tokens = _max_tokens_for_chat_turn(
        document_mode=document_mode,
        audit_mode=audit_mode,
        no_sources=no_sources,
        user_block_len=ub_len,
        task_hint=task_hint,
        answer_depth=answer_depth,
    )
    base = SYSTEM_PROMPT_CITATION_AUDIT if audit_mode else SYSTEM_PROMPT_CONVERSATIONAL
    system_text = base + (AUDIT_SYSTEM_APPEND if audit_mode else "")
    if not audit_mode and task_hint == CHAT_TASK_STRENGTHEN_FILING:
        system_text += STRENGTHEN_SYSTEM_APPEND
    if document_mode and not audit_mode and not meta_connectivity_hint:
        system_text += POLISH_PASS_APPEND if polish_pass_only else DOCUMENT_MODE_QUALITY_APPEND
        if not polish_pass_only:
            system_text += OPEN_ACCESS_STRICT_APPEND
    if document_mode and not audit_mode and not meta_connectivity_hint and not polish_pass_only:
        if filing_phase == 1:
            system_text += FILING_PHASE_1_APPEND
        elif filing_phase == 2:
            system_text += FILING_PHASE_2_APPEND
    create_kw: dict[str, Any] = {
        "model": model_id,
        "max_tokens": max_tokens,
        "messages": [
            {"role": "system", "content": system_text},
            {"role": "user", "content": user_block},
        ],
    }
    t = _chat_sampling_temperature(
        no_sources=no_sources,
        audit_mode=audit_mode,
        document_mode=document_mode,
        task_hint=task_hint,
        meta_connectivity_hint=meta_connectivity_hint,
        polish_pass_only=polish_pass_only,
        answer_depth=answer_depth,
    )
    if t is not None:
        create_kw["temperature"] = t

    do_stream = bool(stream_tokens and on_token is not None)
    llm_wall_ms: float
    llm_ttft_ms: float | None = None
    usage: dict[str, Any] = {}

    if do_stream:
        t_llm0 = time.perf_counter()
        stream = await chat_completions_stream_create_with_retry(client, **create_kw)
        parts: list[str] = []
        async for chunk in stream:
            u = getattr(chunk, "usage", None)
            if u is not None:
                pt = getattr(u, "prompt_tokens", None)
                ct = getattr(u, "completion_tokens", None)
                if isinstance(pt, int):
                    usage["prompt_tokens"] = pt
                if isinstance(ct, int):
                    usage["completion_tokens"] = ct
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            piece = getattr(delta, "content", None) if delta is not None else None
            if piece:
                if llm_ttft_ms is None:
                    llm_ttft_ms = (time.perf_counter() - t_llm0) * 1000
                parts.append(piece)
                await on_token(piece)
        answer = "".join(parts).strip()
        llm_wall_ms = (time.perf_counter() - t_llm0) * 1000
    else:
        t_llm0 = time.perf_counter()
        msg = await chat_completions_create_with_retry(client, **create_kw)
        llm_wall_ms = (time.perf_counter() - t_llm0) * 1000
        choice = msg.choices[0].message
        answer = (choice.content or "").strip()
        u = getattr(msg, "usage", None)
        if u is not None:
            pt = getattr(u, "prompt_tokens", None)
            ct = getattr(u, "completion_tokens", None)
            if isinstance(pt, int):
                usage["prompt_tokens"] = pt
            if isinstance(ct, int):
                usage["completion_tokens"] = ct

    model_label = f"{settings.openai_base_url}::{model_id}"
    out = _finalize_answer(
        answer,
        conn,
        chunk_ids,
        session_id,
        model_label,
        empty_vault,
        footer_note,
        retrieval_skipped_api,
        audit_mode=audit_mode,
        document_mode=document_mode,
        llm_backend_used=llm_backend_used,
    )
    out["response_mode"] = "document" if document_mode else "chat"
    out["chat_model_id"] = model_id
    out["_chat_llm_timing"] = {
        "duration_ms": round(llm_wall_ms, 2),
        "ttft_ms": round(llm_ttft_ms, 2) if llm_ttft_ms is not None else None,
        "streamed": do_stream,
    }
    if usage:
        out["_llm_usage"] = usage
    return out


async def _anthropic_messages_create_with_thinking_fallback(
    client: anthropic.AsyncAnthropic,
    anth_attempt: dict[str, Any],
    anth_kw: dict[str, Any],
    *,
    enable_thinking: bool,
    session_id: str,
    model_id: str,
) -> Any:
    try:
        return await client.messages.create(**anth_attempt)
    except anthropic.RateLimitError:
        record_http_429("anthropic")
        raise
    except Exception as first_exc:
        if enable_thinking and "thinking" in anth_attempt:
            log_llm_event(
                {
                    "event": "anthropic_thinking_fallback",
                    "session_id": session_id,
                    "model_id": model_id,
                    "error": str(first_exc)[:500],
                }
            )
            return await client.messages.create(**anth_kw)
        raise first_exc


async def _run_anthropic(
    user_block: str,
    conn,
    chunk_ids: list[str],
    session_id: str,
    empty_vault: bool,
    footer_note: str | None,
    retrieval_skipped_api: bool,
    document_mode: bool = False,
    audit_mode: bool = False,
    task_hint: str | None = None,
    meta_connectivity_hint: bool = False,
    polish_pass_only: bool = False,
    filing_phase: int | None = None,
    *,
    model_id: str,
    llm_backend_used: str = "anthropic",
    enable_thinking: bool = False,
    stream_tokens: bool = False,
    on_token: Callable[[str], Awaitable[None]] | None = None,
    answer_depth: str = "standard",
) -> dict[str, Any]:
    client = get_anthropic_async_client()
    no_sources = len(chunk_ids) == 0
    ub_len = len(user_block)
    max_tokens = _max_tokens_for_chat_turn(
        document_mode=document_mode,
        audit_mode=audit_mode,
        no_sources=no_sources,
        user_block_len=ub_len,
        task_hint=task_hint,
        answer_depth=answer_depth,
    )
    base = SYSTEM_PROMPT_CITATION_AUDIT if audit_mode else SYSTEM_PROMPT_CONVERSATIONAL
    system_text = base + (AUDIT_SYSTEM_APPEND if audit_mode else "")
    if not audit_mode and task_hint == CHAT_TASK_STRENGTHEN_FILING:
        system_text += STRENGTHEN_SYSTEM_APPEND
    if document_mode and not audit_mode and not meta_connectivity_hint:
        system_text += POLISH_PASS_APPEND if polish_pass_only else DOCUMENT_MODE_QUALITY_APPEND
        if not polish_pass_only:
            system_text += OPEN_ACCESS_STRICT_APPEND
    if document_mode and not audit_mode and not meta_connectivity_hint and not polish_pass_only:
        if filing_phase == 1:
            system_text += FILING_PHASE_1_APPEND
        elif filing_phase == 2:
            system_text += FILING_PHASE_2_APPEND
    anth_kw: dict[str, Any] = {
        "model": model_id,
        "max_tokens": max_tokens,
        "system": system_text,
        "messages": [{"role": "user", "content": user_block}],
    }
    t = _chat_sampling_temperature(
        no_sources=no_sources,
        audit_mode=audit_mode,
        document_mode=document_mode,
        task_hint=task_hint,
        meta_connectivity_hint=meta_connectivity_hint,
        polish_pass_only=polish_pass_only,
        answer_depth=answer_depth,
    )
    if t is not None:
        anth_kw["temperature"] = t

    thinking_budget = min(max(1024, settings.anthropic_thinking_budget_tokens), 32_000)
    anth_attempt = dict(anth_kw)
    if enable_thinking:
        anth_attempt["thinking"] = {"type": "enabled", "budget_tokens": thinking_budget}
        anth_attempt["max_tokens"] = min(max_tokens + thinking_budget, 64_000)

    do_stream = bool(stream_tokens and on_token is not None)
    t_llm0 = time.perf_counter()
    llm_ttft_ms: float | None = None
    msg: Any = None
    answer = ""
    stream_used = False

    if do_stream:
        try:
            async with client.messages.stream(**anth_attempt) as stream:
                async for text in stream.text_stream:
                    if llm_ttft_ms is None and text:
                        llm_ttft_ms = (time.perf_counter() - t_llm0) * 1000
                    await on_token(text)
                answer = (await stream.get_final_text()).strip()
                msg = await stream.get_final_message()
                stream_used = True
        except anthropic.RateLimitError:
            record_http_429("anthropic")
            raise
        except Exception as e:
            log_llm_event(
                {
                    "event": "anthropic_stream_fallback",
                    "session_id": session_id,
                    "model_id": model_id,
                    "error": str(e)[:500],
                }
            )

    if msg is None:
        msg = await _anthropic_messages_create_with_thinking_fallback(
            client,
            anth_attempt,
            anth_kw,
            enable_thinking=enable_thinking,
            session_id=session_id,
            model_id=model_id,
        )
        text_parts: list[str] = []
        for block in msg.content:
            if getattr(block, "type", None) == "text":
                text_parts.append(block.text)
        answer = "".join(text_parts).strip()

    llm_wall_ms = (time.perf_counter() - t_llm0) * 1000
    usage: dict[str, Any] = {}
    u = getattr(msg, "usage", None)
    if u is not None:
        inp = getattr(u, "input_tokens", None)
        outp = getattr(u, "output_tokens", None)
        if isinstance(inp, int):
            usage["input_tokens"] = inp
        if isinstance(outp, int):
            usage["output_tokens"] = outp
    out = _finalize_answer(
        answer,
        conn,
        chunk_ids,
        session_id,
        model_id,
        empty_vault,
        footer_note,
        retrieval_skipped_api,
        audit_mode=audit_mode,
        document_mode=document_mode,
        llm_backend_used=llm_backend_used,
    )
    out["response_mode"] = "document" if document_mode else "chat"
    out["chat_model_id"] = model_id
    out["_chat_llm_timing"] = {
        "duration_ms": round(llm_wall_ms, 2),
        "ttft_ms": round(llm_ttft_ms, 2) if llm_ttft_ms is not None else None,
        "streamed": stream_used,
    }
    if usage:
        out["_llm_usage"] = usage
    return out


def _finalize_answer(
    answer: str,
    conn,
    chunk_ids: list[str],
    session_id: str,
    model_label: str,
    empty_vault: bool,
    footer_note: str | None,
    retrieval_skipped_api: bool,
    audit_mode: bool = False,
    document_mode: bool = False,
    *,
    llm_backend_used: str,
) -> dict[str, Any]:
    answer = (answer or "").strip()
    if not chunk_ids:
        if audit_mode:
            answer = _sanitize_audit_empty_vault_answer(answer)
        elif document_mode:
            answer = _sanitize_document_draft_empty_vault(answer)
        else:
            answer = _sanitize_conversational_empty_vault_answer(answer)
    elif document_mode and not audit_mode:
        answer = _strip_assistant_filing_preamble(answer)

    vault = CitationVault(conn)
    ok, errs = verify_quotes_in_vault(answer, vault, chunk_ids)
    errs = list(errs)
    if chunk_ids and not ok:
        answer += (
            "\n\n---\n[Verification warning] Some quoted passages did not match the citation vault:\n"
            + "\n".join(errs)
        )
    elif not chunk_ids and footer_note:
        answer += "\n\n---\n[Note] " + footer_note

    out = {
        "answer": answer,
        "verification_ok": ok,
        "verification_errors": errs if not ok else [],
        "model": model_label,
        "session_id": session_id,
        "llm_backend": llm_backend_used,
        "retrieval_skipped": retrieval_skipped_api,
        "vault_empty": len(chunk_ids) == 0,
    }
    return out


async def run_chat(
    conn,
    user_message: str,
    session_id: str,
    profile: dict[str, str],
    timeline_snippets: list[str],
    chunks: list[dict[str, Any]],
    chunk_ids: list[str],
    empty_vault: bool = False,
    footer_note: str | None = None,
    retrieval_skipped_api: bool = False,
    document_mode: bool = False,
    audit_mode: bool = False,
    audit_extracted: list[dict[str, str]] | None = None,
    review_injection: str | None = None,
    task_hint: str | None = None,
    meta_connectivity_hint: bool = False,
    polish_pass_only: bool = False,
    session_summary: str | None = None,
    on_step: Callable[[str, str], Awaitable[None]] | None = None,
    filing_phase: int | None = None,
    court_template_message: str | None = None,
    reasoning_enabled: bool = True,
    verification_appendix: str | None = None,
    stream_tokens: bool = False,
    on_token: Callable[[str], Awaitable[None]] | None = None,
    timing_segment: str = "primary",
    answer_depth: str = "standard",
) -> dict[str, Any]:
    if settings.llm_backend() is None:
        return {
            "error": "No LLM configured. Set NVIDIA_API_KEY (recommended) or ANTHROPIC_API_KEY in .env",
            "answer": "",
            "verification_ok": False,
        }

    routing_message = user_message or ""
    if len(user_message) > MAX_USER_MESSAGE_CHARS:
        user_message = (
            user_message[:MAX_USER_MESSAGE_CHARS]
            + "\n\n---\n[Server note: Message truncated — only the first "
            f"{MAX_USER_MESSAGE_CHARS:,} characters were sent. "
            "For very long filings, ask in parts or paste key sections separately.]\n"
        )

    profile_lines = [f"{k}: {v}" for k, v in profile.items()]
    timeline_compact = compact_timeline_snippets(timeline_snippets)
    timeline_summary = "\n".join(f"- {t}" for t in timeline_compact)
    task_directive = task_directive_for_chat_task(task_hint, document_mode=document_mode)
    gwin_msg = court_template_message if court_template_message is not None else user_message
    gwinnett_tpl = (
        GWINNETT_MAGISTRATE_DRAFTING_BLOCK
        if should_inject_gwinnett_magistrate_template(
            gwin_msg,
            profile,
            document_mode=document_mode,
            task_hint=task_hint,
            audit_mode=audit_mode,
        )
        else None
    )
    reasoning_scaffold: str | None = None
    reasoning_ms = 0.0
    if reasoning_enabled and should_run_reasoning_pass(
        user_message=routing_message,
        document_mode=document_mode,
        audit_mode=audit_mode,
        task_hint=task_hint,
        meta_connectivity_hint=meta_connectivity_hint,
        polish_pass_only=polish_pass_only,
        answer_depth=answer_depth,
    ):
        if on_step:
            await on_step("reasoning", "Structuring issues and facts…")
        t_rs = time.perf_counter()
        reasoning_scaffold = await build_reasoning_scaffold(
            user_message=routing_message,
            profile=profile,
        )
        reasoning_ms = (time.perf_counter() - t_rs) * 1000
    user_block = build_user_block(
        user_message,
        profile_lines,
        timeline_summary,
        chunks,
        chunk_ids,
        empty_vault=empty_vault,
        document_mode=document_mode,
        audit_mode=audit_mode,
        audit_extracted=audit_extracted,
        review_injection=review_injection,
        task_directive=task_directive,
        meta_connectivity_hint=meta_connectivity_hint,
        gwinnett_magistrate_template=gwinnett_tpl,
        session_summary=session_summary,
        reasoning_scaffold=reasoning_scaffold,
        filing_phase=filing_phase,
        verification_appendix=verification_appendix,
        answer_depth=answer_depth,
    )

    cap_ok = can_use_anthropic_escalation(conn)
    route = decide_llm_route(
        user_message=routing_message,
        meta_connectivity_hint=meta_connectivity_hint,
        document_mode=document_mode,
        audit_mode=audit_mode,
        task_hint=task_hint,
        polish_pass_only=polish_pass_only,
        anthropic_budget_ok=cap_ok,
    )
    enable_thinking = (
        route.backend == "anthropic"
        and (settings.lawbot_anthropic_thinking or "auto").strip().lower() == "auto"
        and not polish_pass_only
        and not meta_connectivity_hint
        and (
            document_mode
            or audit_mode
            or route.escalation
            or len(user_block) > 10_000
        )
    )

    use_token_stream_oc = bool(
        stream_tokens and on_token is not None and route.backend == "openai_compatible"
    )
    use_token_stream_anth = bool(
        stream_tokens and on_token is not None and route.backend == "anthropic"
    )
    t0 = time.perf_counter()
    if route.backend == "openai_compatible":
        out = await _run_openai_compatible(
            user_block,
            routing_message,
            conn,
            chunk_ids,
            session_id,
            empty_vault,
            footer_note,
            retrieval_skipped_api,
            document_mode,
            audit_mode,
            task_hint=task_hint,
            meta_connectivity_hint=meta_connectivity_hint,
            polish_pass_only=polish_pass_only,
            filing_phase=filing_phase,
            model_id=route.model_id,
            llm_backend_used="openai_compatible",
            stream_tokens=use_token_stream_oc,
            on_token=on_token if use_token_stream_oc else None,
            answer_depth=answer_depth,
        )
    else:
        out = await _run_anthropic(
            user_block,
            conn,
            chunk_ids,
            session_id,
            empty_vault,
            footer_note,
            retrieval_skipped_api,
            document_mode,
            audit_mode,
            task_hint=task_hint,
            meta_connectivity_hint=meta_connectivity_hint,
            polish_pass_only=polish_pass_only,
            filing_phase=filing_phase,
            model_id=route.model_id,
            llm_backend_used="anthropic",
            enable_thinking=enable_thinking,
            stream_tokens=use_token_stream_anth,
            on_token=on_token if use_token_stream_anth else None,
            answer_depth=answer_depth,
        )
    dt_ms = (time.perf_counter() - t0) * 1000
    usage = out.pop("_llm_usage", None) or {}
    lm_timing = out.pop("_chat_llm_timing", None) or {}
    llm_wall = float(lm_timing.get("duration_ms", dt_ms))
    llm_ttft = lm_timing.get("ttft_ms")
    log_payload: dict[str, Any] = {
        "event": "llm_complete",
        "phase": "polish" if polish_pass_only else "primary",
        "segment": timing_segment,
        "backend": route.backend,
        "model_id": route.model_id,
        "escalation": route.escalation,
        "session_id": session_id,
        "duration_ms": round(llm_wall, 2),
        "answer_depth": answer_depth,
        **usage,
    }
    if llm_ttft is not None:
        log_payload["llm_ttft_ms"] = llm_ttft
    if lm_timing.get("streamed"):
        log_payload["streamed"] = True
    record_latency_ms(route.backend, float(log_payload["duration_ms"]))
    log_payload.update(snapshot_for_backend(route.backend))
    log_llm_event(log_payload)
    out["phase_timings"] = {
        "segment": timing_segment,
        "reasoning_ms": round(reasoning_ms, 2),
        "llm_ms": round(llm_wall, 2),
        "llm_ttft_ms": round(float(llm_ttft), 2) if isinstance(llm_ttft, (int, float)) else llm_ttft,
    }
    if route.backend == "anthropic" and route.escalation and not out.get("error"):
        record_anthropic_escalation(conn)
    if not out.get("error"):
        out["reasoning_pass_used"] = bool(reasoning_scaffold)
    return out
