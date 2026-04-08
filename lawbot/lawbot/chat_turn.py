"""
Single chat turn: profile → retrieval → LLM → persist. Optional progress callbacks for streaming UI.
"""

from __future__ import annotations

import asyncio
import sqlite3
import time
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi import Request

from lawbot.audit_retrieval import build_audit_queries, merge_retrieval_results
from lawbot.authority_retrieval import effective_max_queries, merge_queries_with_authority_cap
from lawbot.document_review import (
    resolve_review_injection,
    suggested_auto_research_hint,
    suggested_research_query_suffix,
)
from lawbot.chat_mode import should_use_citation_audit
from lawbot.chat_service import run_chat
from lawbot.citation_extract import extract_citation_candidates, extracted_to_json_rows
from lawbot.citation_vault import CitationVault
from lawbot.hud_broadcast import broadcast_hud
from lawbot.intent import (
    CHAT_TASK_STRENGTHEN_FILING,
    CHAT_TASK_VERIFY_CITATIONS,
    classify_simple_task,
    extract_jurisdiction_hint,
    is_meta_connectivity_message,
    is_smoke_test_message,
    prepare_case_law_search,
)
from lawbot.auto_quality import resolve_polish_second_pass
from lawbot.config import settings
from lawbot.draft_quality_gate import analyze_draft_quality, build_draft_shipping
from lawbot.memory import MemoryStore
from lawbot.polish_pass import build_polish_second_pass_user_message
from lawbot.research import retrieve_for_query_conn
from lawbot.session_compaction import maybe_compact_session
from lawbot.session_rag import (
    ingest_turn,
    merge_chunk_lists,
    retrieve_session_context,
    retrieve_session_context_isolated,
)
from lawbot.thinking_ui import compact_thinking_eligible
from lawbot.answer_depth import classify_answer_depth
from lawbot.observability import log_llm_event
from lawbot.retrieval_coherence import apply_coherence_query_cap, coherence_score_for_retrieval
from lawbot.tail_health import snapshot_all_backends
from lawbot.turn_receipt import build_turn_receipt
from lawbot.turn_signals import build_turn_signals
from lawbot.schemas import ChatIn
from lawbot.vault_flags import vault_footer_and_flags
from lawbot.citation_graph import enrich_opinion_forward_citation_counts
from lawbot.citation_match_status import build_citation_match_status
from lawbot.verification_bundle import build_verification_appendix

OnStep = Callable[[str, str], Awaitable[None]]
OnToken = Callable[[str], Awaitable[None]]

_TWO_PHASE_ORIG_EXCERPT_CHARS = 14_000


def _merge_phase_timings(
    retrieval_ms: float,
    segments: list[dict[str, Any]],
    turn_ms: float,
    embed_ms: float = 0.0,
) -> dict[str, Any]:
    """Flatten per-``run_chat`` segments into one JSON-safe dict for logs and turn_receipt."""
    flat: dict[str, Any] = {
        "retrieval_ms": round(retrieval_ms, 2),
        "turn_ms": round(turn_ms, 2),
    }
    if embed_ms > 0:
        flat["embed_ms"] = round(embed_ms, 2)
    reasoning_ms = 0.0
    for s in segments:
        r = s.get("reasoning_ms")
        if isinstance(r, (int, float)) and r > 0:
            reasoning_ms = float(r)
            break
    flat["reasoning_ms"] = round(reasoning_ms, 2)
    for s in segments:
        seg = (s.get("segment") or "primary").strip()
        lm = s.get("llm_ms")
        if not isinstance(lm, (int, float)):
            lm = 0.0
        ttft = s.get("llm_ttft_ms")
        if seg == "primary":
            flat["llm_primary_ms"] = round(float(lm), 2)
            if ttft is not None and isinstance(ttft, (int, float)):
                flat["llm_ttft_ms"] = round(float(ttft), 2)
        elif seg == "phase1":
            flat["llm_phase1_ms"] = round(float(lm), 2)
        elif seg == "phase2":
            flat["llm_phase2_ms"] = round(float(lm), 2)
            if ttft is not None and isinstance(ttft, (int, float)):
                flat["llm_ttft_ms"] = round(float(ttft), 2)
        elif seg == "polish":
            flat["polish_ms"] = round(float(lm), 2)
    return flat


async def _retrieve_for_query_isolated(db_path: str, q: str, profile: dict[str, str]) -> dict[str, Any]:
    """
    Run CourtListener + vault store on a dedicated SQLite connection so multiple queries can run in parallel.
    """
    c = sqlite3.connect(db_path, timeout=60.0, check_same_thread=False)
    try:
        return await retrieve_for_query_conn(c, q, profile)
    finally:
        c.close()


def _effective_paste_only_no_research(body: ChatIn, task_hint: str | None) -> bool:
    """
    Strengthen-this-filing + case-law search: always retrieve CourtListener (ignore paste-only).
    Paste-only remains available for other tasks when it applies.
    """
    if task_hint == CHAT_TASK_STRENGTHEN_FILING and body.search_case_law:
        return False
    return bool(body.paste_only_no_research)


def _build_two_phase_followup_user_message(original_message: str, phase1_answer: str) -> str:
    """Phase-2 user bundle: prior draft + original paste excerpt for fact cross-check."""
    om = original_message or ""
    excerpt = om[:_TWO_PHASE_ORIG_EXCERPT_CHARS]
    omitted = len(om) - len(excerpt)
    tail = (
        f"\n\n[... {omitted} characters of original omitted — do not drop facts that appear only there; "
        "align with the Phase 1 draft and this excerpt.]\n"
        if omitted > 0
        else ""
    )
    return (
        "### DRAFT FROM PHASE 1\n\n"
        f"{phase1_answer}\n\n"
        "### ORIGINAL USER PASTE (excerpt for cross-check)\n\n"
        f"{excerpt}{tail}"
    )


async def execute_chat_turn(
    conn: sqlite3.Connection,
    body: ChatIn,
    request: Request,
    *,
    on_step: OnStep | None = None,
    broadcast: bool = True,
    stream_tokens: bool = False,
    on_token: OnToken | None = None,
) -> dict[str, Any]:
    """
    Run one user message through retrieval + model. If on_step is set, emit short user-facing lines
    (Perplexity / “agent steps” style) before each major phase.
    """
    t0 = time.perf_counter()
    session_rag_done = False
    sr_chunks: list[dict[str, Any]] = []
    sr_ids: list[str] = []
    embed_timing: dict[str, float] = {}

    mem = MemoryStore(conn)
    sid = mem.ensure_session(body.session_id)
    hint = extract_jurisdiction_hint(body.message)
    place_msg: str | None = None

    if body.jurisdiction and body.jurisdiction.strip():
        mem.set_profile("jurisdiction", body.jurisdiction.strip())
    elif hint:
        mem.set_profile("jurisdiction", hint)
        place_msg = f"Got it — you mentioned {hint}."

    profile = mem.all_profile()
    await maybe_compact_session(conn, mem, sid)
    session_summary_for_turn = mem.get_session_summary(sid) or ""

    meta_connectivity = is_meta_connectivity_message(body.message)
    extracted = extract_citation_candidates(body.message)
    msg_stripped = (body.message or "").strip()
    queries_ran: list[str] = []
    task_hint = classify_simple_task(body.message)

    review_injection, review_audit_label = resolve_review_injection(
        body.review_pass,
        body.review_custom_instruction,
        body.message,
        len(extracted),
    )

    thinking_compact = compact_thinking_eligible(
        msg_stripped=msg_stripped,
        meta_connectivity=meta_connectivity,
        task_hint=task_hint,
        review_audit_label=review_audit_label,
        extracted_count=len(extracted),
        response_mode=(body.response_mode or "chat").strip().lower(),
        explicit_research_query=body.research_query,
        force_authority_retrieval=bool(body.force_authority_retrieval),
    )

    async def emit_user_step(phase: str, message: str) -> None:
        if not on_step or thinking_compact:
            return
        await on_step(phase, message)

    if on_step:
        await on_step("thinking_mode", "compact" if thinking_compact else "full")

    if place_msg:
        await emit_user_step("place", place_msg)

    await emit_user_step("read", "Reading what you wrote…")
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        await emit_user_step("task", "Checking cites against loaded court text…")
    elif task_hint == CHAT_TASK_STRENGTHEN_FILING:
        await emit_user_step("task", "Looking for concrete ways to strengthen your filing…")
    if review_audit_label == "auto" and task_hint != CHAT_TASK_STRENGTHEN_FILING:
        await emit_user_step(
            "verify",
            "Long or citation-heavy message — we’ll match cites to real court text when we find it.",
        )

    effective_research_query = body.research_query
    if not (effective_research_query and str(effective_research_query).strip()):
        hint = suggested_research_query_suffix(body.review_pass)
        if hint:
            effective_research_query = hint
        elif review_audit_label == "auto":
            hint = suggested_auto_research_hint(extracted)
            if hint:
                effective_research_query = hint
    effective_paste_only = _effective_paste_only_no_research(body, task_hint)
    t_retrieval_start = time.perf_counter()
    retrieval_coherence: float | None = None
    retrieval_coherence_trimmed = False

    # Long drafting pastes: skip CourtListener only when paste-only is in effect (after strengthen override).
    # force_authority_retrieval overrides and always searches when search_case_law is on.
    skip_cl_for_drafting = (
        body.search_case_law
        and not body.force_authority_retrieval
        and task_hint == CHAT_TASK_STRENGTHEN_FILING
        and len(msg_stripped) >= 2800
        and not (body.research_query and str(body.research_query).strip())
        and effective_paste_only
    )

    if skip_cl_for_drafting and body.search_case_law:
        await emit_user_step(
            "search",
            "Paste-only mode: skipping case-law search — your text is the sole source this turn.",
        )
        queries_ran = []
        retrieval = {
            "chunks": [],
            "chunk_ids": [],
            "retrieval_skipped": True,
            "query_executed": False,
        }
    elif body.search_case_law:
        if (
            is_smoke_test_message(msg_stripped)
            and not (body.research_query and str(body.research_query).strip())
            and not body.force_authority_retrieval
        ):
            await emit_user_step(
                "search",
                "Skipping opinion lookup for this short message.",
            )
            queries_ran = []
            retrieval = {
                "chunks": [],
                "chunk_ids": [],
                "retrieval_skipped": True,
                "query_executed": False,
            }
        else:
            # Extract cite-like strings, targeted queries, optional Georgia authority pack for strengthen+document.
            queries_ran = build_audit_queries(body.message, extracted, profile, effective_research_query)
            # Strengthen-this-filing: merge Georgia / issue-targeted authority queries whenever case-law search is on.
            include_authority = body.force_authority_retrieval or (
                task_hint == CHAT_TASK_STRENGTHEN_FILING and body.search_case_law and not effective_paste_only
            )
            if include_authority:
                queries_ran = merge_queries_with_authority_cap(
                    queries_ran,
                    body.message,
                    profile,
                    include_authority_pass=True,
                    max_queries=effective_max_queries(len(msg_stripped)),
                )
            doc_mode_early = (body.response_mode or "chat").strip().lower() == "document"
            retrieval_coherence = coherence_score_for_retrieval(
                msg_stripped,
                document_mode=doc_mode_early,
                explicit_research_query=effective_research_query,
            )
            queries_ran, retrieval_coherence_trimmed = apply_coherence_query_cap(
                queries_ran,
                coherence=retrieval_coherence,
                include_authority_pack=include_authority,
                force_authority=bool(body.force_authority_retrieval),
            )
            if queries_ran:
                if (
                    body.paste_only_no_research
                    and task_hint == CHAT_TASK_STRENGTHEN_FILING
                    and body.search_case_law
                ):
                    await emit_user_step(
                        "search",
                        "Strengthen filing — searching court opinions (paste-only ignored for this task).",
                    )
                else:
                    await emit_user_step(
                        "search",
                        "Looking up court cases…",
                    )
                db_path = str(settings.lawbot_db_path)
                want_sr = settings.session_rag_enabled() and not meta_connectivity
                if len(queries_ran) > 1:
                    if want_sr:
                        retrievals, sr_pair = await asyncio.gather(
                            asyncio.gather(
                                *[_retrieve_for_query_isolated(db_path, q, profile) for q in queries_ran]
                            ),
                            retrieve_session_context_isolated(
                                db_path, sid, body.message, embed_ms_accum=embed_timing
                            ),
                        )
                        retrieval = merge_retrieval_results(list(retrievals))
                        sr_chunks, sr_ids = sr_pair
                        session_rag_done = True
                    else:
                        retrievals = await asyncio.gather(
                            *[_retrieve_for_query_isolated(db_path, q, profile) for q in queries_ran]
                        )
                        retrieval = merge_retrieval_results(list(retrievals))
                elif want_sr:
                    retrieval, sr_pair = await asyncio.gather(
                        retrieve_for_query_conn(conn, queries_ran[0], profile),
                        retrieve_session_context_isolated(
                            db_path, sid, body.message, embed_ms_accum=embed_timing
                        ),
                    )
                    sr_chunks, sr_ids = sr_pair
                    session_rag_done = True
                else:
                    retrieval = await retrieve_for_query_conn(conn, queries_ran[0], profile)
            else:
                rq = prepare_case_law_search(body.message, effective_research_query, profile)
                queries_ran = [rq] if rq else []
                db_path = str(settings.lawbot_db_path)
                want_sr = settings.session_rag_enabled() and not meta_connectivity
                if rq:
                    await emit_user_step(
                        "search",
                        "Looking up court cases…",
                    )
                    if want_sr:
                        retrieval, sr_pair = await asyncio.gather(
                            retrieve_for_query_conn(conn, rq, profile),
                            retrieve_session_context_isolated(
                                db_path, sid, body.message, embed_ms_accum=embed_timing
                            ),
                        )
                        sr_chunks, sr_ids = sr_pair
                        session_rag_done = True
                    else:
                        retrieval = await retrieve_for_query_conn(conn, rq, profile)
                else:
                    await emit_user_step(
                        "search",
                        "Nothing to look up from this message — answering without loaded opinions.",
                    )
                    retrieval = {
                        "chunks": [],
                        "chunk_ids": [],
                        "retrieval_skipped": True,
                        "query_executed": False,
                    }
    else:
        await emit_user_step("search", "Court lookup is off — answering from your question only.")
        retrieval = {"chunks": [], "chunk_ids": [], "retrieval_skipped": True, "query_executed": False}

    chunks = list(retrieval["chunks"])
    chunk_ids = list(retrieval["chunk_ids"])
    session_rag_excerpt_count = 0

    vault = CitationVault(conn)
    for eid in body.extra_chunk_ids or []:
        row = vault.get_chunk(eid)
        if not row:
            continue
        chunks.append(
            {
                "chunk_id": row["id"],
                "label": row["citation_label"] or eid,
                "source_url": row["source_url"],
                "excerpt": row["verbatim_text"],
            }
        )
        if row["id"] not in chunk_ids:
            chunk_ids.append(row["id"])

    if settings.session_rag_enabled() and not meta_connectivity and not session_rag_done:
        sr_chunks, sr_ids = await retrieve_session_context(
            conn, sid, body.message, embed_ms_accum=embed_timing
        )
    session_rag_excerpt_count = len(sr_ids)
    if settings.session_rag_enabled() and not meta_connectivity and sr_chunks:
        chunks, chunk_ids = merge_chunk_lists(sr_chunks, chunks)
        await emit_user_step(
            "context",
            f"Pulled {session_rag_excerpt_count} relevant excerpt{'s' if session_rag_excerpt_count != 1 else ''} from earlier in this chat.",
        )

    n = len(chunk_ids)
    if n:
        await emit_user_step(
            "sources",
            f"Found {n} bit{'s' if n != 1 else ''} of court text to work with.",
        )
    else:
        no_sources_msg = (
            "Answering without loaded court excerpts — nothing to attach for this message."
            if is_smoke_test_message(msg_stripped)
            else "No court text found this time — I’ll still answer carefully."
        )
        await emit_user_step("sources", no_sources_msg)

    t_retrieval_end = time.perf_counter()
    retrieval_ms = (t_retrieval_end - t_retrieval_start) * 1000

    empty_vault, footer_note, retrieval_skipped_api = vault_footer_and_flags(
        retrieval, body.search_case_law, chunk_ids
    )
    tl = mem.recent_timeline(sid, limit=30)
    timeline_snippets = [t["content"] for t in tl]
    if meta_connectivity:
        timeline_snippets = []
        await emit_user_step(
            "context",
            "System check — ignoring older session context for this message.",
        )

    mem.append_message(sid, "user", body.message)
    mem.add_timeline(sid, "user_message", body.message, {"chunk_ids": chunk_ids})

    doc_mode = (body.response_mode or "chat").strip().lower() == "document"
    doc_mode_effective = doc_mode
    # Citation verification is a matrix/checklist reply — never full pleading rewrite (UI defaults to document).
    if task_hint == CHAT_TASK_VERIFY_CITATIONS:
        doc_mode_effective = False
    elif (
        doc_mode
        and is_smoke_test_message(msg_stripped)
        and len(msg_stripped) <= 120
        and not (body.research_query and str(body.research_query).strip())
    ):
        doc_mode_effective = False
    await emit_user_step(
        "write",
        "Writing your answer…",
    )

    audit_rows = extracted_to_json_rows(extracted)
    use_citation_audit = should_use_citation_audit(
        body,
        len(extracted),
        task_hint,
        review_audit_label,
        len(chunk_ids),
    )
    review_effective = (review_injection or None) if use_citation_audit else None

    _depth = classify_answer_depth(
        message=msg_stripped,
        meta_connectivity=meta_connectivity,
        document_mode=doc_mode_effective,
        use_citation_audit=use_citation_audit,
        task_hint=task_hint,
        chunk_ids=chunk_ids,
        explicit_research_query=body.research_query,
        force_authority_retrieval=body.force_authority_retrieval,
    )
    answer_depth_level = _depth.level
    answer_depth_reason = _depth.reason

    citation_graph_counts: dict[int, int] = {}
    if (
        doc_mode_effective
        and not use_citation_audit
        and not meta_connectivity
        and body.search_case_law
        and chunks
        and len(msg_stripped) >= 160
    ):
        await emit_user_step(
            "search",
            "Citation graph (CourtListener): fetching forward-citation counts — not Westlaw KeyCite.",
        )
        citation_graph_counts = await enrich_opinion_forward_citation_counts(chunks)

    verification_appendix = build_verification_appendix(
        user_message=body.message,
        retrieved_chunks=chunks,
        profile=profile,
        document_mode=doc_mode_effective,
        audit_mode=use_citation_audit,
        meta_connectivity=meta_connectivity,
        search_case_law=body.search_case_law,
        citation_graph_counts=citation_graph_counts if citation_graph_counts else None,
    )

    citation_match_status_md: str | None = None
    if doc_mode_effective and not use_citation_audit and not meta_connectivity:
        citation_match_status_md = build_citation_match_status(body.message, chunks)
    if citation_match_status_md:
        if verification_appendix:
            verification_appendix = verification_appendix + "\n\n" + citation_match_status_md
        else:
            verification_appendix = citation_match_status_md

    two_phase_eligible = (
        doc_mode_effective
        and body.two_phase_filing
        and not use_citation_audit
        and not meta_connectivity
        and task_hint == CHAT_TASK_STRENGTHEN_FILING
        and len(msg_stripped) >= 2000
    )
    run_two_phase = two_phase_eligible and bool(chunk_ids)
    two_phase_note: str | None = None
    if two_phase_eligible and not chunk_ids:
        two_phase_note = "skipped_no_vault_chunks"

    out: dict[str, Any]
    timing_segments: list[dict[str, Any]] = []
    if run_two_phase:
        await emit_user_step(
            "write",
            "Drafting (1/2): fact preservation — holding vault excerpts for the next pass…",
        )
        out = await run_chat(
            conn,
            body.message,
            sid,
            profile,
            timeline_snippets,
            [],
            [],
            empty_vault=True,
            footer_note=footer_note,
            retrieval_skipped_api=retrieval_skipped_api,
            document_mode=doc_mode_effective,
            audit_mode=use_citation_audit,
            audit_extracted=audit_rows,
            review_injection=review_effective,
            task_hint=task_hint,
            meta_connectivity_hint=meta_connectivity,
            session_summary=session_summary_for_turn,
            on_step=emit_user_step,
            filing_phase=1,
            court_template_message=body.message,
            reasoning_enabled=True,
            verification_appendix=verification_appendix,
            stream_tokens=False,
            on_token=None,
            timing_segment="phase1",
            answer_depth=answer_depth_level,
        )
        timing_segments.append(out.pop("phase_timings", {}))
        if out.get("answer") and not out.get("error"):
            await emit_user_step(
                "write",
                "Drafting (2/2): adding verified quotes from retrieved court text…",
            )
            p2_user = _build_two_phase_followup_user_message(body.message, out["answer"])
            out = await run_chat(
                conn,
                p2_user,
                sid,
                profile,
                timeline_snippets,
                chunks,
                chunk_ids,
                empty_vault=empty_vault,
                footer_note=footer_note,
                retrieval_skipped_api=retrieval_skipped_api,
                document_mode=doc_mode_effective,
                audit_mode=use_citation_audit,
                audit_extracted=audit_rows,
                review_injection=review_effective,
                task_hint=task_hint,
                meta_connectivity_hint=meta_connectivity,
                session_summary=session_summary_for_turn,
                on_step=emit_user_step,
                filing_phase=2,
                court_template_message=body.message,
                reasoning_enabled=False,
                verification_appendix=verification_appendix,
                stream_tokens=stream_tokens,
                on_token=on_token if stream_tokens else None,
                timing_segment="phase2",
                answer_depth=answer_depth_level,
            )
            timing_segments.append(out.pop("phase_timings", {}))
    else:
        out = await run_chat(
            conn,
            body.message,
            sid,
            profile,
            timeline_snippets,
            chunks,
            chunk_ids,
            empty_vault=empty_vault,
            footer_note=footer_note,
            retrieval_skipped_api=retrieval_skipped_api,
            document_mode=doc_mode_effective,
            audit_mode=use_citation_audit,
            audit_extracted=audit_rows,
            review_injection=review_effective,
            task_hint=task_hint,
            meta_connectivity_hint=meta_connectivity,
            session_summary=session_summary_for_turn,
            on_step=emit_user_step,
            filing_phase=None,
            court_template_message=None,
            reasoning_enabled=True,
            verification_appendix=verification_appendix,
            stream_tokens=stream_tokens,
            on_token=on_token if stream_tokens else None,
            timing_segment="primary",
            answer_depth=answer_depth_level,
        )
        timing_segments.append(out.pop("phase_timings", {}))

    run_polish, polish_reason = resolve_polish_second_pass(
        requested=body.polish_second_pass,
        message=body.message,
        task_hint=task_hint,
        use_citation_audit=use_citation_audit,
        meta_connectivity=meta_connectivity,
        retrieval_skipped=retrieval_skipped_api,
    )

    polish_applied = False
    if (
        run_polish
        and out.get("answer")
        and not out.get("error")
        and not meta_connectivity
    ):
        await emit_user_step("write", "Tightening wording (second pass)…")
        polish_user = build_polish_second_pass_user_message(body.message, out["answer"])
        polish_out = await run_chat(
            conn,
            polish_user,
            sid,
            profile,
            [],
            chunks,
            chunk_ids,
            empty_vault=empty_vault,
            footer_note=footer_note,
            retrieval_skipped_api=retrieval_skipped_api,
            document_mode=True,
            audit_mode=False,
            audit_extracted=None,
            review_injection=None,
            task_hint=None,
            meta_connectivity_hint=False,
            polish_pass_only=True,
            session_summary=session_summary_for_turn,
            on_step=None,
            verification_appendix=None,
            stream_tokens=False,
            on_token=None,
            timing_segment="polish",
            answer_depth="standard",
        )
        timing_segments.append(polish_out.pop("phase_timings", {}))
        if polish_out.get("answer"):
            out["answer"] = polish_out["answer"]
            out["verification_ok"] = polish_out.get("verification_ok")
            out["verification_errors"] = polish_out.get("verification_errors") or []
            out["vault_empty"] = polish_out.get("vault_empty")
            out["model"] = polish_out.get("model")
            out["chat_model_id"] = polish_out.get("chat_model_id")
            polish_applied = True
    if run_polish:
        out["polish_second_pass_applied"] = polish_applied
        if polish_reason:
            out["polish_second_pass_reason"] = polish_reason

    if out.get("answer"):
        out["draft_quality"] = analyze_draft_quality(
            out["answer"],
            user_message=body.message,
            document_mode=doc_mode_effective,
            citation_audit=use_citation_audit,
            vault_chunk_ids=chunk_ids,
        )
        if body.draft_judge:
            from lawbot.draft_judge import run_draft_judge_rubric

            try:
                out["draft_judge"] = await run_draft_judge_rubric(out["answer"])
            except Exception as e:
                out["draft_judge"] = {"error": str(e), "parse_ok": False}
        else:
            out["draft_judge"] = None
    else:
        out["draft_judge"] = None
        out["draft_quality"] = None

    out["draft_shipping"] = build_draft_shipping(
        out.get("draft_quality"),
        verification_ok=out.get("verification_ok"),
        draft_judge=out.get("draft_judge"),
    )

    out["audit"] = {
        "enabled": use_citation_audit,
        "mode": "citation_audit" if use_citation_audit else "conversational",
        "retrieval_skipped": bool(out.get("retrieval_skipped")),
        "extracted_citations": audit_rows,
        "retrieval_queries_executed": queries_ran,
        "vault_chunk_count": len(chunk_ids),
        "vault_chunk_ids": list(chunk_ids),
        "quote_verification_ok": out.get("verification_ok"),
        "quote_verification_errors": out.get("verification_errors") or [],
        "review_pass": review_audit_label,
        "task_hint": task_hint,
        "chat_model_id": out.get("chat_model_id"),
        "polish_second_pass_applied": bool(out.get("polish_second_pass_applied")),
        "polish_second_pass_reason": out.get("polish_second_pass_reason"),
        "session_rag_excerpts": session_rag_excerpt_count,
        "two_phase_filing_applied": run_two_phase,
        "two_phase_filing_note": two_phase_note,
        "paste_only_no_research": body.paste_only_no_research,
        "paste_only_no_research_effective": effective_paste_only,
        "strengthen_always_retrieves": task_hint == CHAT_TASK_STRENGTHEN_FILING and body.search_case_law,
        "force_authority_retrieval": body.force_authority_retrieval,
        "verification_appendix": bool(verification_appendix),
        "citation_graph_opinions": len(citation_graph_counts),
        "citation_match_status": bool(citation_match_status_md),
        "phase_timings": out.get("phase_timings"),
        "answer_depth": answer_depth_level,
        "answer_depth_reason": answer_depth_reason,
        "document_mode_requested": doc_mode,
        "document_mode_effective": doc_mode_effective,
        "thinking_ui_compact": thinking_compact,
    }

    out["turn_signals"] = build_turn_signals(
        conn,
        out,
        body_message=body.message,
        meta_connectivity=meta_connectivity,
        use_citation_audit=use_citation_audit,
        document_mode=doc_mode_effective,
        task_hint=task_hint,
        chunk_ids=list(chunk_ids),
        queries_ran=queries_ran,
        retrieval_coherence=retrieval_coherence,
        retrieval_coherence_trimmed=retrieval_coherence_trimmed,
        answer_depth_level=answer_depth_level,
        answer_depth_reason=answer_depth_reason,
    )
    ts = out["turn_signals"]
    out["audit"]["task_regime"] = ts.get("task_regime")
    out["audit"]["citation_confidence"] = ts.get("citation_confidence")
    out["audit"]["hermes_passed"] = (ts.get("gates") or {}).get("hermes_passed")
    log_llm_event(
        {
            "event": "turn_decision",
            "session_id": sid,
            "task_regime": ts.get("task_regime"),
            "citation_confidence": ts.get("citation_confidence"),
            "hermes_passed": (ts.get("gates") or {}).get("hermes_passed"),
            "user_visible_warning_count": ts.get("user_visible_warning_count"),
            "vault_chunk_count": (ts.get("vault_coverage") or {}).get("chunk_count"),
            "queries_executed": (ts.get("retrieval_depth") or {}).get("queries_executed"),
            "answer_depth": answer_depth_level,
            "answer_depth_reason": answer_depth_reason,
            **snapshot_all_backends(),
        }
    )

    if out.get("answer"):
        mem.append_message(sid, "assistant", out["answer"])
        mem.add_timeline(
            sid,
            "assistant",
            out["answer"][:2000],
            {
                "verification_ok": out.get("verification_ok"),
                "citation_audit": use_citation_audit,
            },
        )
        if settings.session_rag_enabled() and not meta_connectivity:
            await ingest_turn(conn, sid, body.message, out["answer"])

    if broadcast:
        await broadcast_hud(
            request.app,
            {
                "session_id": sid,
                "summary": (out.get("answer") or "")[:1200],
                "chunk_ids": chunk_ids,
                "verification_ok": out.get("verification_ok"),
                "audit": out.get("audit"),
            },
        )

    turn_ms = (time.perf_counter() - t0) * 1000
    flat_pt = _merge_phase_timings(
        retrieval_ms,
        timing_segments,
        turn_ms,
        embed_ms=float(embed_timing.get("embed_ms", 0.0)),
    )
    out["phase_timings"] = flat_pt
    log_llm_event({"event": "turn_phases", "session_id": sid, **flat_pt})
    duration_ms = int(turn_ms)
    out["turn_receipt"] = build_turn_receipt(
        session_id=sid,
        duration_ms=duration_ms,
        out=out,
        audit=out.get("audit") or {},
        meta_connectivity=meta_connectivity,
        phase_timings=flat_pt,
    )

    out["session_id"] = sid
    return out
