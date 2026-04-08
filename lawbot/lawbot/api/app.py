from __future__ import annotations

import asyncio
import json
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import Body, Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from lawbot.chat_turn import execute_chat_turn
from lawbot.observability import configure_llm_logging
from lawbot.citation_vault import CitationVault
from lawbot.config import settings
from lawbot.db import connect
from lawbot.hud_broadcast import broadcast_hud
from lawbot.memory import MemoryStore
from lawbot.hermes_verify import hermes_report_to_dict, run_hermes_checks
from lawbot.intent import extract_jurisdiction_hint
from lawbot.schemas import ChatIn
from lawbot.rate_limit import register_rate_limit_middleware
from lawbot.usage_limits import get_daily_count, METRIC_ANTHROPIC_ESCALATION


def get_conn(request: Request) -> sqlite3.Connection:
    return request.app.state.conn


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_llm_logging()
    prev = getattr(app.state, "conn", None)
    if prev is not None:
        try:
            prev.close()
        except Exception:
            pass
    app.state.conn = connect(settings.lawbot_db_path)
    app.state.hud_clients: list[WebSocket] = []
    app.state.hud_last: dict[str, Any] = {}
    try:
        yield
    finally:
        c = getattr(app.state, "conn", None)
        if c is not None:
            try:
                c.close()
            except Exception:
                pass


app = FastAPI(title="Lawbot API", lifespan=lifespan)

register_rate_limit_middleware(app, lambda: settings.lawbot_rate_limit_per_minute)

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


@app.get("/")
def serve_ui():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/favicon.ico")
def favicon_ico():
    """Browsers request /favicon.ico by default; serve the SVG with correct type."""
    return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")


class ProfileSet(BaseModel):
    key: str
    value: str


class LexisPasteIn(BaseModel):
    citation_label: str
    verbatim_text: str
    source_url: str | None = None


@app.get("/health")
def health():
    oc = bool(settings.openai_compatible_key())
    anthropic_escalations_today: int | None = None
    if settings.both_llm_backends_configured():
        try:
            c = connect(settings.lawbot_db_path)
            try:
                anthropic_escalations_today = get_daily_count(c, METRIC_ANTHROPIC_ESCALATION)
            finally:
                c.close()
        except Exception:
            anthropic_escalations_today = None
    return {
        "status": "ok",
        "llm_backend": settings.llm_backend(),
        "chat_model": settings.chat_model if oc else settings.anthropic_model,
        "chat_model_fast": settings.chat_model_fast if oc else None,
        "chat_model_max": (((settings.chat_model_max or "").strip() or None) if oc else None),
        "openai_base_url": settings.openai_base_url if oc else None,
        "anthropic_configured": settings.anthropic_configured(),
        "anthropic_escalation_mode": settings.anthropic_escalation_mode if oc and settings.anthropic_configured() else None,
        "anthropic_escalation_model": settings.resolved_anthropic_escalation_model()
        if oc and settings.anthropic_configured()
        else None,
        "max_anthropic_escalations_per_day": settings.max_anthropic_escalations_per_day
        if oc and settings.anthropic_configured()
        else None,
        "anthropic_escalations_today": anthropic_escalations_today,
        "model_routing_note": (
            "CHAT_MODEL for most substantive turns; optional CHAT_MODEL_MAX for high-stakes NVIDIA-only turns; "
            "CHAT_MODEL_FAST only for trivial connectivity checks (see lawbot/model_routing.py)."
            if oc
            else None
        ),
    }


@app.get("/v1/health/deep")
def health_deep(conn: sqlite3.Connection = Depends(get_conn)):
    """
    DB touch + Hermes self-test (no LLM). Use for monitoring / OpenClaw smoke.
    """
    mem = MemoryStore(conn)
    mem.list_sessions(1)
    good = {
        "answer": "Short reply with no invented citations.",
        "verification_ok": True,
        "verification_errors": [],
        "vault_empty": True,
        "session_id": "hermes-selftest",
        "audit": {"vault_chunk_ids": []},
    }
    bad = {
        "answer": "See O.C.G.A. § 1-1-1 for details.",
        "verification_ok": True,
        "verification_errors": [],
        "vault_empty": True,
        "session_id": "hermes-selftest",
        "audit": {"vault_chunk_ids": []},
    }
    r_ok = run_hermes_checks(None, good)
    r_bad = run_hermes_checks(None, bad)
    return {
        "status": "ok",
        "sqlite": "ok",
        "hermes_self_test": {
            "clean_answer_passes": r_ok.passed,
            "ocga_leak_fails_as_expected": not r_bad.passed,
        },
    }


@app.post("/v1/hermes/check")
def hermes_check_endpoint(
    body: dict[str, Any] = Body(...),
    conn: sqlite3.Connection = Depends(get_conn),
):
    """
    Deterministic Hermes verification on a JSON object (typically a full /v1/chat response).
    """
    report = run_hermes_checks(conn, body)
    return hermes_report_to_dict(report)


@app.post("/v1/chat")
async def chat(request: Request, body: ChatIn, conn: sqlite3.Connection = Depends(get_conn)):
    return await execute_chat_turn(conn, body, request)


@app.post("/v1/chat/stream")
async def chat_stream(request: Request, body: ChatIn, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Server-Sent Events while processing a chat turn: step lines (Perplexity-style), optional token deltas
    from the OpenAI-compatible stream, then one final JSON payload (same shape as ``/v1/chat``).
    Each event is ``data: {"event":"thinking_mode"|"step"|"token"|"complete"|"error", ...}\\n\\n``.
    ``thinking_mode`` carries ``{"mode":"compact"|"full"}`` so the client can show a minimal pulse vs a step list.
    Token events: ``{"event":"token","delta":"..."}`` (assistant text fragments; may be empty — ignore).
    """

    async def event_bytes() -> AsyncIterator[bytes]:
        queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()

        async def on_step(_phase: str, message: str) -> None:
            if _phase == "thinking_mode":
                await queue.put(("chunk", {"event": "thinking_mode", "mode": message}))
                return
            await queue.put(("chunk", {"event": "step", "message": message}))

        async def on_token(delta: str) -> None:
            if delta:
                await queue.put(("chunk", {"event": "token", "delta": delta}))

        async def worker() -> None:
            try:
                out = await execute_chat_turn(
                    conn,
                    body,
                    request,
                    on_step=on_step,
                    broadcast=True,
                    stream_tokens=True,
                    on_token=on_token,
                )
                await queue.put(("chunk", {"event": "complete", "result": out}))
            except Exception as e:
                await queue.put(("chunk", {"event": "error", "message": str(e)}))

        task = asyncio.create_task(worker())
        try:
            while True:
                kind, payload = await queue.get()
                if kind != "chunk":
                    continue
                yield f"data: {json.dumps(payload)}\n\n".encode("utf-8")
                if payload.get("event") in ("complete", "error"):
                    break
        finally:
            await task

    headers = {"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"}
    return StreamingResponse(event_bytes(), media_type="text/event-stream", headers=headers)


@app.post("/v1/profile")
def set_profile(body: ProfileSet, conn: sqlite3.Connection = Depends(get_conn)):
    mem = MemoryStore(conn)
    mem.set_profile(body.key, body.value)
    return {"ok": True}


@app.get("/v1/profile")
def get_profile(conn: sqlite3.Connection = Depends(get_conn)):
    mem = MemoryStore(conn)
    return mem.all_profile()


@app.get("/v1/sessions")
def list_sessions(conn: sqlite3.Connection = Depends(get_conn)):
    mem = MemoryStore(conn)
    return {"sessions": mem.list_sessions(50)}


@app.get("/v1/sessions/{session_id}/messages")
def session_messages(session_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    mem = MemoryStore(conn)
    return {"session_id": session_id, "messages": mem.messages_in_order(session_id)}


@app.get("/v1/sessions/{session_id}/timeline")
def timeline(session_id: str, conn: sqlite3.Connection = Depends(get_conn)):
    mem = MemoryStore(conn)
    return {"session_id": session_id, "events": mem.recent_timeline(session_id, limit=100)}


@app.post("/v1/citations/lexis-paste")
def lexis_paste(body: LexisPasteIn, conn: sqlite3.Connection = Depends(get_conn)):
    """
    Ingest a verbatim excerpt you copied from Lexis (or any licensed system) into the vault.
    """
    vault = CitationVault(conn)
    cid = vault.store_chunk(
        source_system="lexis_paste",
        verbatim_text=body.verbatim_text,
        source_url=body.source_url,
        citation_label=body.citation_label,
        raw_meta={"ingest": "manual"},
    )
    return {"chunk_id": cid}


@app.get("/v1/citations/recent")
def citations_recent(conn: sqlite3.Connection = Depends(get_conn)):
    vault = CitationVault(conn)
    return {"chunks": vault.list_recent(30)}


@app.websocket("/ws/hud")
async def ws_hud(websocket: WebSocket):
    token = websocket.query_params.get("token")
    await websocket.accept()
    if settings.hud_token and token != settings.hud_token:
        await websocket.close(code=4401)
        return
    app.state.hud_clients.append(websocket)
    try:
        if app.state.hud_last:
            await websocket.send_text(json.dumps(app.state.hud_last))
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        if websocket in app.state.hud_clients:
            app.state.hud_clients.remove(websocket)


@app.post("/webhooks/twilio/sms")
async def twilio_sms(request: Request, conn: sqlite3.Connection = Depends(get_conn)):
    form = await request.form()
    body = dict(form)
    if settings.twilio_validate_signature and settings.twilio_auth_token:
        from twilio.request_validator import RequestValidator

        validator = RequestValidator(settings.twilio_auth_token)
        url = settings.public_base_url.rstrip("/") + "/webhooks/twilio/sms"
        if not validator.validate(url, body, request.headers.get("X-Twilio-Signature", "")):
            raise HTTPException(status_code=403, detail="Invalid Twilio signature")

    incoming = (body.get("Body") or "").strip()
    from_num = body.get("From") or "unknown"
    mem = MemoryStore(conn)
    sid_key = f"twilio_session:{from_num}"
    existing = mem.get_profile(sid_key)
    sid = existing or mem.ensure_session(None)
    if not existing:
        mem.set_profile(sid_key, sid)

    hint = extract_jurisdiction_hint(incoming)
    if hint:
        mem.set_profile("jurisdiction", hint)

    # Same pipeline as web/API: audit mode, citation extract, task routing, merged retrieval.
    chat_body = ChatIn(
        message=incoming,
        session_id=sid,
        search_case_law=True,
        research_query=None,
        jurisdiction=None,
        extra_chunk_ids=None,
        response_mode="chat",
        review_pass=None,
        review_custom_instruction=None,
    )
    out = await execute_chat_turn(conn, chat_body, request, broadcast=False)
    sid = out.get("session_id", sid)
    text = out.get("answer") or out.get("error") or ""
    audit = out.get("audit") or {}
    await broadcast_hud(
        app,
        {
            "session_id": sid,
            "summary": text[:1200],
            "from": from_num,
            "chunk_ids": audit.get("vault_chunk_ids", []),
            "verification_ok": out.get("verification_ok"),
            "audit": audit,
        },
    )

    if settings.twilio_account_sid and settings.twilio_auth_token:
        from twilio.rest import Client

        twilio_client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
        to = body.get("From")
        from_ = body.get("To")
        if to and from_:
            for part in _sms_chunks(text, 1500):
                twilio_client.messages.create(to=to, from_=from_, body=part)
        return PlainTextResponse("")

    return PlainTextResponse(text[:16000])


def _sms_chunks(text: str, size: int) -> list[str]:
    if len(text) <= size:
        return [text]
    return [text[i : i + size] for i in range(0, len(text), size)]


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
