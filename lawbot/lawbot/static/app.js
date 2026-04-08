/** Set `localStorage.lawbot_debug = "1"` and reload to log stream diagnostics to the console (default: silent). */
function lawbotDebug() {
  try {
    return localStorage.getItem("lawbot_debug") === "1";
  } catch (_) {
    return false;
  }
}
function dbgInfo(...args) {
  if (lawbotDebug()) console.info(...args);
}
function dbgErr(...args) {
  if (lawbotDebug()) console.error(...args);
}

const STORAGE_KEY = "lawbot_session_id";
const STORAGE_SEARCH_CASE_LAW = "lawbot_search_case_law";
const STORAGE_DRAFT_JUDGE = "lawbot_draft_judge";
/** Weighted draft score threshold — confirm Download/Print if below and not all_passed */
const SHIP_GATE_MIN_SCORE = 80;
const STORAGE_VAULT_CHUNK_IDS = "lawbot_vault_chunk_ids";
/** Sidebar rubric — Markdown-style task list (GitHub / README convention), persisted locally */
const STORAGE_QUALITY_CHECKLIST = "lawbot_quality_checklist_v1";
const MAX_VAULT_CHUNKS = 20;
/** Simple UI: hide advanced-only controls (default on). Set localStorage to "0" to expand. */
const STORAGE_SIMPLE_MODE = "lawbot_simple_mode";
const QUALITY_CHECKLIST_ITEMS = [
  { id: "primary", label: "Primary deliverable is drafting/strategy (not a cite matrix as the main reply)." },
  { id: "opening", label: "Opening instruction wins — not reframed as verification-only." },
  { id: "appendix", label: "Buried appendix text didn’t hijack the task." },
  { id: "dedupe", label: "No pointless repetition of the same cites." },
  { id: "consistent", label: "Cite/status lines are consistent (no contradictions)." },
  { id: "proportion", label: "Secondary notes don’t dwarf the main answer." },
];
/**
 * Browser-side wait for /v1/chat/stream (server may still finish after abort).
 * Base: floor 3 min; +10ms/char; soft cap ~30 min before bonuses.
 * For pastes ≥8k chars, add headroom when case search and/or two-phase drafting run
 * (many CourtListener round-trips + 2 LLM passes + optional polish). Pastes ≥25k get +8 min
 * (large outputs / reasoning). Absolute max 45 min.
 * Keep in sync with tests/test_chat_timeout_formula.py
 *
 * @param {number} messageLen
 * @param {{ searchCaseLaw?: boolean, twoPhaseFiling?: boolean } | undefined} options
 */
function chatTimeoutMs(messageLen, options) {
  const n = Math.max(0, Math.floor(Number(messageLen) || 0));
  const searchCase =
    options && typeof options.searchCaseLaw === "boolean" ? options.searchCaseLaw : true;
  const twoPhase =
    options && typeof options.twoPhaseFiling === "boolean" ? options.twoPhaseFiling : true;
  let t = Math.min(1800000, 180000 + n * 10);
  if (n >= 8000) {
    if (searchCase) t += 720000; // 12 min — sequential CourtListener + LLM
    if (twoPhase) t += 720000; // 12 min — second model pass
  }
  if (n >= 25000) {
    t += 480000; // +8 min — long generations / strengthen
  }
  return Math.min(2700000, t);
}

let chatInFlight = false;

function $(sel) {
  return document.querySelector(sel);
}

function formatApiError(payload, status) {
  if (!payload || typeof payload !== "object") {
    return `HTTP ${status}`;
  }
  const d = payload.detail;
  if (typeof d === "string") return d;
  if (Array.isArray(d)) {
    return d
      .map((e) => (e.msg ? `${e.loc?.join?.(".") || "?"}: ${e.msg}` : JSON.stringify(e)))
      .join("; ");
  }
  return JSON.stringify(payload);
}

function getSessionId() {
  let id = localStorage.getItem(STORAGE_KEY);
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem(STORAGE_KEY, id);
  }
  return id;
}

function selectSessionInDropdown(sid) {
  const sel = $("#sessionSelect");
  if (!sel || !sid) return;
  const has = Array.from(sel.options).some((o) => o.value === sid && !o.disabled);
  if (has) sel.value = sid;
}

function setSessionId(id) {
  localStorage.setItem(STORAGE_KEY, id);
  const el = $("#sessionDisplay");
  if (el) el.textContent = id;
  selectSessionInDropdown(id);
}

function showError(msg) {
  const el = $("#errorToast");
  if (!el) return;
  el.textContent = msg;
  el.classList.add("visible");
  setTimeout(() => el.classList.remove("visible"), 12000);
}

function appendMessage(role, content, meta) {
  const wrap = $("#messages");
  if (!wrap) return;
  const empty = wrap.querySelector(".empty-hint");
  if (empty) empty.remove();

  const div = document.createElement("div");
  div.className = `msg ${role}`;

  const metaEl = document.createElement("div");
  metaEl.className = "msg-meta";
  if (role === "user") {
    metaEl.textContent = "You";
  } else {
    metaEl.innerHTML = "Lawbot";
    // verification_ok is trivially true when there are no <quote> tags; do not imply "verified citations" with an empty vault.
    if (meta?.vault_empty === true) {
      metaEl.innerHTML +=
        ' <span class="badge" style="background:rgba(139,149,168,0.2);color:var(--muted)">no case text</span>';
    } else if (meta?.verification_ok === true) {
      metaEl.innerHTML +=
        ' <span class="badge ok" title="Quoted passages were matched to text you loaded into the vault for this turn. This does not mean every legal proposition is correct, complete, or that you will win — verify before filing.">quotes match loaded text</span>';
    } else if (meta?.verification_ok === false) {
      metaEl.innerHTML += ' <span class="badge warn">check quotes</span>';
    }
    if (meta?.retrieval_skipped) {
      metaEl.innerHTML += ' <span class="badge" style="background:rgba(139,149,168,0.2);color:var(--muted)">no case lookup</span>';
    }
    if (meta?.chat_model_id) {
      const short = String(meta.chat_model_id).split("/").pop() || meta.chat_model_id;
      metaEl.innerHTML += ` <span class="badge" style="background:rgba(80,120,200,0.22);color:var(--muted)" title="${escapeHtml(
        String(meta.chat_model_id)
      )}">model: ${escapeHtml(short)}</span>`;
    }
    if (meta?.draft_quality) {
      const dq = meta.draft_quality;
      const p = dq.checks_passed ?? 0;
      const t = dq.checks_total ?? 0;
      const pct = dq.score_percent ?? 0;
      const ok = dq.all_passed === true;
      const fails = (dq.checks || []).filter((c) => !c.passed).map((c) => `${c.id}: ${c.detail || ""}`);
      let tip = fails.length ? fails.join(" · ") : "All automated draft checks passed.";
      if (tip.length > 420) tip = tip.slice(0, 417) + "…";
      const bg = ok ? "rgba(61,158,107,0.15)" : "rgba(212,165,52,0.15)";
      const col = ok ? "var(--ok)" : "var(--warn)";
      metaEl.innerHTML += ` <span class="badge" style="background:${bg};color:${col}" title="${escapeHtml(tip)}">draft ${p}/${t} (${pct}%)</span>`;
    }
  }

  const body = document.createElement("div");
  body.className = role === "assistant" ? "msg-body md-content" : "msg-body";
  if (role === "assistant") {
    body.innerHTML = renderAssistantMarkdown(content);
    div._lawbotRawMarkdown = content;
    div._lawbotDraftQuality = meta?.draft_quality ?? null;
  } else {
    body.textContent = content;
  }

  div.appendChild(metaEl);
  div.appendChild(body);

  if (role === "assistant") {
    const actions = document.createElement("div");
    actions.className = "msg-actions";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "copy-msg-btn";
    copyBtn.textContent = "Copy";
    copyBtn.title = "Copy this reply as plain text / Markdown";
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.textContent = "Copied";
        setTimeout(() => {
          copyBtn.textContent = "Copy";
        }, 2000);
      } catch (_) {
        showError("Could not copy automatically — select the text and copy manually.");
      }
    });
    const dlBtn = document.createElement("button");
    dlBtn.type = "button";
    dlBtn.className = "copy-msg-btn";
    dlBtn.textContent = "Download";
    dlBtn.title = "Save this reply as a .md file";
    dlBtn.addEventListener("click", () => {
      const dq = div._lawbotDraftQuality;
      if (_draftExportNeedsConfirm(dq)) {
        const ok = window.confirm(
          `Draft quality is ${dq.score_percent}% (weighted). Not all automated checks passed. Download anyway?`
        );
        if (!ok) return;
      }
      const blob = new Blob([content], { type: "text/markdown;charset=utf-8" });
      const a = document.createElement("a");
      const stamp = new Date().toISOString().slice(0, 10);
      a.href = URL.createObjectURL(blob);
      a.download = `lawbot-reply-${stamp}.md`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
    const printBtn = document.createElement("button");
    printBtn.type = "button";
    printBtn.className = "copy-msg-btn";
    printBtn.textContent = "Print";
    printBtn.title = "Print this reply, or choose Save as PDF in the print dialog";
    printBtn.addEventListener("click", () => {
      const dq = div._lawbotDraftQuality;
      if (_draftExportNeedsConfirm(dq)) {
        const ok = window.confirm(
          `Draft quality is ${dq.score_percent}% (weighted). Not all automated checks passed. Print anyway?`
        );
        if (!ok) return;
      }
      const messagesEl = $("#messages");
      if (!messagesEl) {
        window.print();
        return;
      }
      const bodyEl = div.querySelector(".msg-body");
      let printReminder = null;
      if (bodyEl && _looksLikeCourtFilingMarkdown(div._lawbotRawMarkdown || "")) {
        printReminder = document.createElement("div");
        printReminder.className = "print-filing-reminder";
        printReminder.textContent =
          "Before filing: verify every statute, rule, and case citation against official sources (O.C.G.A., court reporters, or your licensed research). Confirm formatting against the clerk’s current rules and forms — Lawbot does not guarantee legal accuracy or court-specific layout.";
        bodyEl.insertBefore(printReminder, bodyEl.firstChild);
      }
      messagesEl.classList.add("messages-print-one");
      div.classList.add("is-print-focus");
      const cleanup = () => {
        messagesEl.classList.remove("messages-print-one");
        div.classList.remove("is-print-focus");
        if (printReminder && printReminder.parentNode) {
          printReminder.parentNode.removeChild(printReminder);
        }
        window.removeEventListener("afterprint", cleanup);
      };
      window.addEventListener("afterprint", cleanup);
      window.print();
    });
    actions.appendChild(copyBtn);
    actions.appendChild(dlBtn);
    actions.appendChild(printBtn);
    div.appendChild(actions);
    if (meta?.turn_receipt && typeof meta.turn_receipt === "object") {
      const tr = meta.turn_receipt;
      const details = document.createElement("details");
      details.className = "turn-receipt";
      const sum = document.createElement("summary");
      sum.textContent = "What happened this time";
      details.appendChild(sum);
      const ul = document.createElement("ul");
      ul.className = "turn-receipt-list";
      const lines = Array.isArray(tr.summary_lines) ? tr.summary_lines : [];
      for (const line of lines) {
        const li = document.createElement("li");
        li.textContent = line;
        ul.appendChild(li);
      }
      details.appendChild(ul);
      if (tr.quality_line) {
        const p = document.createElement("p");
        p.className = "turn-receipt-quality";
        p.textContent = tr.quality_line;
        details.appendChild(p);
      }
      if (Array.isArray(tr.speed_tips) && tr.speed_tips.length) {
        const st = document.createElement("p");
        st.className = "turn-receipt-speed";
        st.appendChild(document.createTextNode("Faster next time: "));
        st.appendChild(document.createTextNode(tr.speed_tips.join(" ")));
        details.appendChild(st);
      }
      div.appendChild(details);
    }
    if (
      meta?.vault_empty === true &&
      content &&
      content.length > 2500 &&
      _looksLikeCourtFilingMarkdown(content)
    ) {
      const tip = document.createElement("p");
      tip.className = "lawbot-post-tip";
      tip.textContent =
        "Tip for a stronger next reply: add 1–3 short excerpts from Lexis/Westlaw (Add to vault), keep “Look up real court cases” on, two-phase on, paste-only off — then the Editor’s overview can tie quotes to real text.";
      div.appendChild(tip);
    }
  } else if (role === "user") {
    const actions = document.createElement("div");
    actions.className = "msg-actions";
    const copyBtn = document.createElement("button");
    copyBtn.type = "button";
    copyBtn.className = "copy-msg-btn";
    copyBtn.textContent = "Copy";
    copyBtn.title = "Copy your message as plain text";
    copyBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(content);
        copyBtn.textContent = "Copied";
        setTimeout(() => {
          copyBtn.textContent = "Copy";
        }, 2000);
      } catch (_) {
        showError("Could not copy automatically — select the text and copy manually.");
      }
    });
    actions.appendChild(copyBtn);
    div.appendChild(actions);
  }

  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function showThinking() {
  const wrap = $("#messages");
  if (!wrap) return;
  removeThinking();
  const empty = wrap.querySelector(".empty-hint");
  if (empty) empty.remove();
  const div = document.createElement("div");
  div.className = "msg assistant thinking";
  div.id = "lawbotThinking";
  div.innerHTML =
    '<div class="msg-meta">Thinking…</div>' +
    '<div class="thinking-body">' +
    '<div class="thinking-head"><span class="spinner" aria-hidden="true"></span>' +
    "<strong>Progress</strong></div>" +
    '<p class="thinking-compact-hint" id="thinkingCompactHint" hidden></p>' +
    '<p class="thinking-live" id="thinkingLive" aria-live="polite"></p></div>';
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

/** Server sends thinking_mode first (SSE): compact = calm pulse; full = one live status line (updates in place). */
function applyThinkingMode(mode) {
  const t = document.getElementById("lawbotThinking");
  if (!t || !mode) return;
  const live = document.getElementById("thinkingLive");
  const hint = document.getElementById("thinkingCompactHint");
  const headStrong = t.querySelector(".thinking-head strong");
  const meta = t.querySelector(".msg-meta");
  if (mode === "compact") {
    t.classList.add("thinking-compact");
    if (headStrong) headStrong.textContent = "Working on your answer";
    if (hint) {
      hint.hidden = false;
      hint.textContent = "This may take a moment.";
    }
    if (live) {
      live.textContent = "";
      live.hidden = true;
    }
    if (meta) meta.textContent = "";
  } else {
    t.classList.remove("thinking-compact");
    if (headStrong) headStrong.textContent = "Progress";
    if (hint) {
      hint.hidden = true;
      hint.textContent = "";
    }
    if (live) {
      live.hidden = false;
      live.textContent = "";
    }
    if (meta) meta.textContent = "Thinking…";
  }
}

/** Replaces the single live line (not a growing bullet list) as each backend phase reports. */
function appendThinkingStep(message) {
  const t = document.getElementById("lawbotThinking");
  if (t && t.classList.contains("thinking-compact")) return;
  const live = document.getElementById("thinkingLive");
  if (!live || !message) return;
  live.textContent = message;
  const wrap = $("#messages");
  if (wrap) wrap.scrollTop = wrap.scrollHeight;
}

function removeThinking() {
  const t = document.getElementById("lawbotThinking");
  if (t) t.remove();
}

let lawbotStreamBuf = "";

function removeStreamingAssistant() {
  const t = document.getElementById("lawbotStreamingAssistant");
  if (t) t.remove();
  lawbotStreamBuf = "";
}

/** Incremental SSE tokens: plain text until `complete` replaces with rendered Markdown. */
function appendStreamingDelta(delta) {
  const wrap = $("#messages");
  if (!wrap || delta == null || delta === "") return;
  let row = document.getElementById("lawbotStreamingAssistant");
  if (!row) {
    removeThinking();
    row = document.createElement("div");
    row.id = "lawbotStreamingAssistant";
    row.className = "msg assistant streaming";
    row.innerHTML =
      '<div class="msg-meta">Lawbot</div><div class="msg-body streaming-raw" id="lawbotStreamingBody"></div>';
    wrap.appendChild(row);
  }
  lawbotStreamBuf += delta;
  const body = document.getElementById("lawbotStreamingBody");
  if (body) body.textContent = lawbotStreamBuf;
  wrap.scrollTop = wrap.scrollHeight;
}

function setStatusPillText(text) {
  const pill = $("#statusPill");
  if (!pill) return;
  const label = pill.querySelector("span:last-child");
  if (label) label.textContent = text;
}

async function pingHealth() {
  const pill = $("#statusPill");
  if (!pill) return;
  try {
    const r = await fetch("/health", { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    pill.dataset.state = "ok";
    setStatusPillText(j.chat_model || j.llm_backend || "connected");
    const ml = $("#modelLine");
    if (ml) {
      let html = `<div><strong>Connected</strong> · ${escapeHtml(String(j.llm_backend || "ok"))}</div>`;
      if (j.chat_model) {
        html += `<div style="margin-top:0.35rem;font-size:0.75rem;color:var(--text)">Primary model: ${escapeHtml(
          String(j.chat_model)
        )}</div>`;
      }
      if (j.chat_model_fast) {
        html += `<div style="margin-top:0.2rem;font-size:0.72rem;color:var(--muted)">Fast (pings only): ${escapeHtml(
          String(j.chat_model_fast)
        )}</div>`;
      }
      if (j.openai_base_url) {
        html += `<div style="margin-top:0.35rem;word-break:break-all;font-size:0.72rem;color:var(--muted)">${escapeHtml(
          String(j.openai_base_url)
        )}</div>`;
      }
      ml.innerHTML = html;
    }
    const retry = $("#retryHealthBtn");
    if (retry) retry.hidden = true;
  } catch (e) {
    pill.dataset.state = "err";
    setStatusPillText("disconnected");
    showError("Cannot reach /health — is the server running on this host/port?");
    const retry = $("#retryHealthBtn");
    if (retry) retry.hidden = false;
  }
}

function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

/**
 * Show assistant replies like claude.ai: Markdown → safe HTML. Falls back to plain text if libraries missing.
 */
function _draftExportNeedsConfirm(dq) {
  if (!dq || typeof dq.score_percent !== "number") return false;
  if (dq.all_passed === true) return false;
  return dq.score_percent < SHIP_GATE_MIN_SCORE;
}

function _looksLikeCourtFilingMarkdown(text) {
  const head = (text || "").slice(0, 2000);
  return /IN\s+THE\s+\w+[\s\w]*COURT/i.test(head) && /\b(Civil Action|Case\s+No|Plaintiff|Defendant|COMES\s+NOW)\b/i.test(head);
}

/**
 * Center caption-style ## lines (court name, state, v.) while keeping PART/COUNT section headings left-aligned.
 * Markdown has no native "caption" element; we classify leading h2 blocks heuristically.
 */
function _markCaptionH2InFiling(wrappedHtml) {
  try {
    const host = document.createElement("div");
    host.innerHTML = wrappedHtml;
    const wrap = host.querySelector(".lawbot-filing-doc");
    if (!wrap) return wrappedHtml;
    const h2s = wrap.querySelectorAll("h2");
    let n = 0;
    for (const h2 of h2s) {
      const t = (h2.textContent || "").trim();
      if (/^PART\s+/i.test(t)) break;
      if (/^COUNT\s+[A-Z]/i.test(t)) break;
      h2.classList.add("lawbot-caption-line");
      if (++n >= 16) break;
    }
    return host.innerHTML;
  } catch (_) {
    return wrappedHtml;
  }
}

function renderAssistantMarkdown(markdown) {
  const raw = markdown == null ? "" : String(markdown);
  if (typeof marked !== "undefined" && typeof DOMPurify !== "undefined") {
    try {
      marked.setOptions({ gfm: true, breaks: true });
      const overviewSep = /\n---\s*\n(?=##\s*Editor'?s?\s+overview\b)/i;
      const sepMatch = overviewSep.exec(raw);
      if (sepMatch) {
        const mainMd = raw.slice(0, sepMatch.index);
        const overviewMd = raw.slice(sepMatch.index + sepMatch[0].length);
        let mainHtml = marked.parse(mainMd);
        if (_looksLikeCourtFilingMarkdown(mainMd)) {
          mainHtml = _markCaptionH2InFiling(`<div class="lawbot-filing-doc">${mainHtml}</div>`);
        }
        const overviewInner = marked.parse(overviewMd);
        const combined =
          mainHtml +
          `<aside class="lawbot-editor-overview" aria-label="Editor overview (not for filing)">${overviewInner}</aside>`;
        return DOMPurify.sanitize(combined);
      }
      let html = marked.parse(raw);
      if (_looksLikeCourtFilingMarkdown(raw)) {
        html = _markCaptionH2InFiling(`<div class="lawbot-filing-doc">${html}</div>`);
      }
      return DOMPurify.sanitize(html);
    } catch (_) {
      /* fall through */
    }
  }
  return `<p class="md-fallback">${escapeHtml(raw).replace(/\n\n/g, "</p><p class=\"md-fallback\">").replace(/\n/g, "<br />")}</p>`;
}

function loadVaultChunkIds() {
  try {
    const raw = localStorage.getItem(STORAGE_VAULT_CHUNK_IDS);
    if (!raw) return [];
    const o = JSON.parse(raw);
    return Array.isArray(o) ? o.filter((x) => typeof x === "string" && x.length) : [];
  } catch (_) {
    return [];
  }
}

function saveVaultChunkIds(ids) {
  try {
    localStorage.setItem(STORAGE_VAULT_CHUNK_IDS, JSON.stringify(ids.slice(0, MAX_VAULT_CHUNKS)));
  } catch (_) {
    /* ignore */
  }
}

function pushVaultChunkId(id) {
  const cur = loadVaultChunkIds();
  if (cur.includes(id)) return cur;
  cur.push(id);
  const next = cur.slice(-MAX_VAULT_CHUNKS);
  saveVaultChunkIds(next);
  return next;
}

function setVaultStatus(text, isErr) {
  const el = $("#vaultStatus");
  if (!el) return;
  el.textContent = text || "";
  el.style.color = isErr ? "var(--bad)" : "var(--ok)";
}

async function sendChat() {
  const msgEl = $("#message");
  const msg = (msgEl && msgEl.value.trim()) || "";
  if (!msg) return;
  if (chatInFlight) {
    showError("Already waiting for a reply — please wait.");
    return;
  }

  const research = ($("#researchQuery") && $("#researchQuery").value.trim()) || "";
  const jur = ($("#jurisdiction") && $("#jurisdiction").value.trim()) || "";
  const searchCase = $("#caseSearchToggle") ? $("#caseSearchToggle").checked : true;
  // Long / structured answers: always on (same idea as claude.ai — no extra toggle).
  const docMode = true;
  const draftJudge = $("#draftJudgeToggle") ? $("#draftJudgeToggle").checked : false;
  const extraIds = loadVaultChunkIds();
  const composer = $("#composer");
  const sendBtn = $("#sendBtn");
  const twoPhaseToggle = $("#twoPhaseToggle") ? $("#twoPhaseToggle").checked : true;
  // Match server: “paste-only” does not skip retrieval for strengthen-filing; budget as if case search runs when enabled.
  const timeoutMs = chatTimeoutMs(msg.length, {
    searchCaseLaw: searchCase,
    twoPhaseFiling: twoPhaseToggle,
  });
  const hintEl = $("#longMessageHint");

  if (hintEl) {
    if (msg.length >= 20000) {
      hintEl.hidden = false;
      hintEl.textContent =
        "Very long message (~" +
        Math.round(msg.length / 1000) +
        "k characters). Client wait budget up to ~" +
        (timeoutMs / 60000).toFixed(0) +
        " min for this request (hard cap 45 min). Turn off “Look up real court cases” or “Two-phase drafting” to shorten wait; if the browser times out, the server may still be working — check the terminal running uvicorn.";
    } else if (msg.length >= 8000) {
      hintEl.hidden = false;
      hintEl.textContent =
        "Long message — expect several to many minutes with case search / two-phase on. Shorter paste speeds things up; strengthen-filing runs always search opinions when case lookup is on.";
    } else {
      hintEl.hidden = true;
      hintEl.textContent = "";
    }
  }

  chatInFlight = true;
  if (composer) composer.classList.add("loading");
  if (sendBtn) sendBtn.disabled = true;

  appendMessage("user", msg);
  if (msgEl) msgEl.value = "";
  showThinking();

  const sessionId = getSessionId();
  const ctrl = new AbortController();
  const tid = setTimeout(() => ctrl.abort(), timeoutMs);

  try {
    dbgInfo("[Lawbot] POST /v1/chat/stream start", {
      len: msg.length,
      searchCaseLaw: searchCase,
      timeoutMs,
      timeoutMin: (timeoutMs / 60000).toFixed(2),
    });
    const r = await fetch("/v1/chat/stream", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        message: msg,
        session_id: sessionId,
        research_query: research || null,
        search_case_law: searchCase,
        jurisdiction: jur || null,
        response_mode: docMode ? "document" : "chat",
        draft_judge: draftJudge,
        extra_chunk_ids: extraIds.length ? extraIds : null,
        paste_only_no_research: $("#pasteOnlyToggle") ? $("#pasteOnlyToggle").checked : false,
        force_authority_retrieval: $("#forceAuthorityToggle") ? $("#forceAuthorityToggle").checked : false,
        two_phase_filing: $("#twoPhaseToggle") ? $("#twoPhaseToggle").checked : true,
      }),
      signal: ctrl.signal,
    });
    if (!r.ok) {
      let errText = await r.text();
      try {
        const ej = JSON.parse(errText);
        errText = formatApiError(ej, r.status);
      } catch (_) {
        errText = errText.slice(0, 300) || `HTTP ${r.status}`;
      }
      throw new Error(errText);
    }
    const reader = r.body.getReader();
    const dec = new TextDecoder();
    let buf = "";
    let j = null;
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += dec.decode(value, { stream: true });
      let sep;
      while ((sep = buf.indexOf("\n\n")) >= 0) {
        const block = buf.slice(0, sep);
        buf = buf.slice(sep + 2);
        for (const line of block.split("\n")) {
          if (!line.startsWith("data: ")) continue;
          let payload;
          try {
            payload = JSON.parse(line.slice(6));
          } catch {
            continue;
          }
          if (payload.event === "thinking_mode" && payload.mode) {
            applyThinkingMode(payload.mode);
          } else if (payload.event === "step" && payload.message) {
            appendThinkingStep(payload.message);
          } else if (payload.event === "token" && typeof payload.delta === "string") {
            appendStreamingDelta(payload.delta);
          } else if (payload.event === "complete") {
            j = payload.result;
          } else if (payload.event === "error") {
            throw new Error(payload.message || "Stream error");
          }
        }
      }
    }
    if (!j) {
      throw new Error("No response from server (stream ended early).");
    }
    if (j.session_id) setSessionId(j.session_id);

    if (extraIds.length) {
      saveVaultChunkIds([]);
      setVaultStatus("Vault excerpts were sent with this reply. Add more below if you need them again.", false);
    }

    const answer = j.answer || j.error || "(no content)";
    const meta = {
      verification_ok: j.verification_ok,
      vault_empty: j.vault_empty === true,
      turn_receipt: j.turn_receipt || null,
    };
    if (j.retrieval_skipped === true) meta.retrieval_skipped = true;
    if (j.audit && j.audit.chat_model_id) meta.chat_model_id = j.audit.chat_model_id;
    if (j.draft_quality) meta.draft_quality = j.draft_quality;
    appendMessage("assistant", answer, meta);
    dbgInfo("[Lawbot] stream complete", { answerLen: (answer || "").length });
    refreshSessions();
  } catch (e) {
    const name = e && e.name;
    let detail = String(e.message || e);
    if (name === "AbortError") {
      detail =
        "Request timed out after " +
        (timeoutMs / 60000).toFixed(1) +
        " min (browser limit; max 45 min). The server may still be finishing — check the uvicorn terminal. " +
        "Try: shorter paste, turn off “Look up real court cases” or “Two-phase drafting”, or split into parts; reload after deploy so the longer wait budget applies.";
    }
    dbgErr("[Lawbot] POST /v1/chat failed", e);
    showError(detail);
    appendMessage(
      "assistant",
      "Request failed: " +
        detail +
        " Open the browser Network tab → select the /v1/chat request → see status and response."
    );
  } finally {
    clearTimeout(tid);
    removeThinking();
    removeStreamingAssistant();
    chatInFlight = false;
    if (composer) composer.classList.remove("loading");
    if (sendBtn) sendBtn.disabled = false;
    const he = $("#longMessageHint");
    if (he) {
      he.hidden = true;
      he.textContent = "";
    }
  }
}

async function refreshSessions() {
  const sel = $("#sessionSelect");
  if (!sel) return;
  try {
    const r = await fetch("/v1/sessions", { cache: "no-store" });
    if (!r.ok) return;
    const j = await r.json();
    const sessions = j.sessions || [];
    sel.innerHTML = "";
    if (sessions.length === 0) {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "No saved sessions yet";
      o.disabled = true;
      sel.appendChild(o);
      return;
    }
    for (const s of sessions) {
      const o = document.createElement("option");
      o.value = s.session_id;
      const prev = (s.preview || "").replace(/\s+/g, " ").trim().slice(0, 60);
      const tail = (s.session_id || "").slice(0, 8);
      o.textContent = `${prev || "(no preview)"} · ${s.message_count || 0} msgs · ${tail}…`;
      sel.appendChild(o);
    }
    selectSessionInDropdown(getSessionId());
  } catch (_) {
    /* ignore */
  }
}

async function loadSessionMessages() {
  const sel = $("#sessionSelect");
  if (!sel || !sel.value || sel.selectedOptions[0]?.disabled) {
    showError("Select a saved conversation first.");
    return;
  }
  const sid = sel.value;
  try {
    const r = await fetch(`/v1/sessions/${encodeURIComponent(sid)}/messages`, { cache: "no-store" });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const j = await r.json();
    setSessionId(j.session_id || sid);
    const wrap = $("#messages");
    if (!wrap) return;
    wrap.innerHTML = "";
    const rows = j.messages || [];
    if (rows.length === 0) {
      wrap.innerHTML =
        '<p class="empty-hint"><strong>Empty session.</strong> Send a message to start.</p>';
      return;
    }
    for (const m of rows) {
      const role = m.role === "user" ? "user" : "assistant";
      appendMessage(role, m.content || "", role === "assistant" ? {} : undefined);
    }
  } catch (e) {
    showError(String(e.message || e));
  }
}

async function exportSessionMarkdown() {
  const sid = getSessionId();
  let rows = [];
  try {
    const r = await fetch(`/v1/sessions/${encodeURIComponent(sid)}/messages`, { cache: "no-store" });
    if (r.ok) {
      const j = await r.json();
      rows = j.messages || [];
    }
  } catch (_) {
    /* fall through */
  }
  if (rows.length === 0) {
    const wrap = $("#messages");
    if (wrap) {
      wrap.querySelectorAll(".msg:not(.thinking)").forEach((div) => {
        const isUser = div.classList.contains("user");
        const body = div.querySelector(".msg-body");
        let text = "";
        if (isUser) {
          text = body ? body.textContent : "";
        } else {
          text = div._lawbotRawMarkdown || (body ? body.textContent : "") || "";
        }
        rows.push({ role: isUser ? "user" : "assistant", content: text });
      });
    }
  }
  if (rows.length === 0) {
    showError("Nothing to export — send a message or load a session.");
    return;
  }
  let md = `# Lawbot transcript\n\nSession: \`${sid}\`\n\n---\n\n`;
  for (const m of rows) {
    const h = m.role === "user" ? "You" : "Lawbot";
    md += `## ${h}\n\n${m.content || ""}\n\n`;
  }
  const blob = new Blob([md], { type: "text/markdown;charset=utf-8" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `lawbot-${sid.slice(0, 8)}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

/** Insert template for paragraph-by-paragraph Answer vs Statement of Claim (user pastes SOC). */
function insertSocParagraphPrompt() {
  const ta = $("#message");
  if (!ta) return;
  const block = `Strengthen this filing for Georgia Magistrate practice.

TASK — STATEMENT OF CLAIM: Paste the full text of the Plaintiff's Statement of Claim (numbered paragraphs) in the section below. Produce a revised **Part II — Answer to Statement of Claim** that responds **paragraph-by-paragraph** to each SOC ¶ (admit / deny / without knowledge / qualified), with a short factual basis for each denial. Preserve my counterclaim, affirmative defenses, jurisdictional notice, and prayer unless a direct conflict requires a footnote.

If SOC text is not pasted yet, say exactly what is missing and keep my current reservation (e.g. ¶5) until the full SOC is available.

--- PASTE PLAINTIFF STATEMENT OF CLAIM BELOW ---


--- END SOC ---

--- MY CURRENT ANSWER / COUNTERCLAIM (context; optional if already in chat) ---

`;
  const cur = (ta.value || "").trim();
  ta.value = cur ? block + "\n\n" + cur : block;
  ta.focus();
}

function emptyWelcomeMarkup() {
  return (
    '<div class="empty-hint" id="emptyWelcome">' +
    "<p><strong>New session.</strong> Try a starter or type your own question.</p>" +
    '<div class="starter-chips" role="group" aria-label="Suggested prompts">' +
    '<button type="button" class="starter-chip" data-starter="Is this working? Reply in one short sentence.">Connectivity check</button>' +
    '<button type="button" class="starter-chip" data-starter="What should I verify before I rely on case law in a Georgia state court filing?">Filing checklist (short)</button>' +
    '<button type="button" class="starter-chip" data-starter="Paste a paragraph below that you want to strengthen for court — I will suggest concrete edits and point out what needs a real cite from research.">Strengthen a paragraph…</button>' +
    "</div></div>"
  );
}

function wireStarterChips() {
  document.querySelectorAll(".starter-chip[data-starter]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const t = btn.getAttribute("data-starter");
      const ta = $("#message");
      if (ta && t) {
        ta.value = t;
        ta.focus();
      }
    });
  });
}

function applySimpleMode() {
  let on = true;
  try {
    on = localStorage.getItem(STORAGE_SIMPLE_MODE) !== "0";
  } catch (_) {
    /* default on */
  }
  const cb = $("#simpleModeToggle");
  if (cb) cb.checked = on;
  document.body.classList.toggle("lawbot-simple-mode", on);
}

function updateJurisdictionPill() {
  const pill = $("#jurisdictionPill");
  const jur = $("#jurisdiction");
  if (!pill || !jur) return;
  const v = (jur.value || "").trim();
  if (v) {
    pill.hidden = false;
    pill.textContent = "Jurisdiction / place (this chat): " + v;
    pill.title = "Saved to your session profile when you send a message. The model may still discuss general law — verify local rules.";
  } else {
    pill.hidden = true;
    pill.textContent = "";
  }
}

function newSession() {
  const id = crypto.randomUUID();
  setSessionId(id);
  const messages = $("#messages");
  if (messages) {
    messages.innerHTML = emptyWelcomeMarkup();
    wireStarterChips();
  }
  const rq = $("#researchQuery");
  if (rq) rq.value = "";
}

function init() {
  const missing = ["sendBtn", "newSessionBtn", "message", "messages", "composer", "errorToast", "statusPill"].filter(
    (id) => !document.getElementById(id)
  );
  if (missing.length) {
    const toast = document.getElementById("errorToast");
    if (toast) {
      toast.textContent =
        "Lawbot UI failed to load required elements (" + missing.join(", ") + "). Try a hard refresh.";
      toast.classList.add("visible");
    }
    return;
  }

  $("#sendBtn").addEventListener("click", sendChat);
  $("#message").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendChat();
    }
  });

  $("#newSessionBtn").addEventListener("click", newSession);
  const loadSess = $("#loadSessionBtn");
  if (loadSess) loadSess.addEventListener("click", () => loadSessionMessages());
  const exportMd = $("#exportMdBtn");
  if (exportMd) exportMd.addEventListener("click", () => exportSessionMarkdown());
  const retry = $("#retryHealthBtn");
  if (retry) {
    retry.addEventListener("click", () => pingHealth());
    retry.hidden = true;
  }

  setSessionId(getSessionId());
  applySimpleMode();
  const simpleT = $("#simpleModeToggle");
  if (simpleT) {
    simpleT.addEventListener("change", () => {
      try {
        localStorage.setItem(STORAGE_SIMPLE_MODE, simpleT.checked ? "1" : "0");
      } catch (_) {
        /* ignore */
      }
      applySimpleMode();
    });
  }
  wireStarterChips();
  const jurEl = $("#jurisdiction");
  if (jurEl) {
    jurEl.addEventListener("input", updateJurisdictionPill);
    jurEl.addEventListener("change", updateJurisdictionPill);
  }
  wireSearchToggle();
  wireDraftJudge();
  wireVaultPaste();
  const insSoc = $("#insertSocPromptBtn");
  if (insSoc) insSoc.addEventListener("click", insertSocParagraphPrompt);
  initQualityChecklist();
  refreshSessions();
  loadProfileFields();
  updateJurisdictionPill();
  pingHealth();
  setInterval(pingHealth, 60000);
}

function loadQualityState() {
  try {
    const raw = localStorage.getItem(STORAGE_QUALITY_CHECKLIST);
    if (!raw) return {};
    const o = JSON.parse(raw);
    return typeof o === "object" && o ? o : {};
  } catch (_) {
    return {};
  }
}

function saveQualityState(state) {
  try {
    localStorage.setItem(STORAGE_QUALITY_CHECKLIST, JSON.stringify(state));
  } catch (_) {
    /* ignore */
  }
}

function initQualityChecklist() {
  const mount = document.getElementById("qualityChecklistMount");
  const reset = document.getElementById("qcResetBtn");
  if (!mount || !QUALITY_CHECKLIST_ITEMS.length) return;

  let state = loadQualityState();
  mount.innerHTML = "";
  for (const item of QUALITY_CHECKLIST_ITEMS) {
    const label = document.createElement("label");
    label.className = "qc-row";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = !!state[item.id];
    cb.addEventListener("change", () => {
      state = loadQualityState();
      state[item.id] = cb.checked;
      saveQualityState(state);
    });
    label.appendChild(cb);
    label.appendChild(document.createTextNode(" " + item.label));
    mount.appendChild(label);
  }

  if (reset) {
    reset.addEventListener("click", () => {
      state = {};
      saveQualityState(state);
      mount.querySelectorAll('input[type="checkbox"]').forEach((el) => {
        el.checked = false;
      });
    });
  }
}

function wireSearchToggle() {
  const el = $("#caseSearchToggle");
  if (!el) return;
  const v = localStorage.getItem(STORAGE_SEARCH_CASE_LAW);
  el.checked = v === null || v === "1";
  el.addEventListener("change", () => {
    localStorage.setItem(STORAGE_SEARCH_CASE_LAW, el.checked ? "1" : "0");
  });
}

function wireDraftJudge() {
  const el = $("#draftJudgeToggle");
  if (!el) return;
  const v = localStorage.getItem(STORAGE_DRAFT_JUDGE);
  el.checked = v === "1";
  el.addEventListener("change", () => {
    localStorage.setItem(STORAGE_DRAFT_JUDGE, el.checked ? "1" : "0");
  });
}

function wireVaultPaste() {
  const btn = $("#vaultAddBtn");
  if (!btn) return;
  const n = loadVaultChunkIds().length;
  if (n) setVaultStatus(`${n} vault excerpt(s) queued for your next send.`, false);
  btn.addEventListener("click", async () => {
    const label = ($("#vaultCiteLabel") && $("#vaultCiteLabel").value.trim()) || "";
    const excerpt = ($("#vaultExcerpt") && $("#vaultExcerpt").value.trim()) || "";
    const urlRaw = ($("#vaultSourceUrl") && $("#vaultSourceUrl").value.trim()) || "";
    if (!label || !excerpt) {
      setVaultStatus("Add a label and excerpt first.", true);
      return;
    }
    try {
      const r = await fetch("/v1/citations/lexis-paste", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          citation_label: label,
          verbatim_text: excerpt,
          source_url: urlRaw || null,
        }),
      });
      if (!r.ok) {
        let errText = await r.text();
        try {
          const ej = JSON.parse(errText);
          errText = formatApiError(ej, r.status);
        } catch (_) {
          errText = errText.slice(0, 200) || `HTTP ${r.status}`;
        }
        throw new Error(errText);
      }
      const data = await r.json();
      const cid = data.chunk_id;
      if (!cid) throw new Error("No chunk id returned");
      pushVaultChunkId(cid);
      setVaultStatus(
        `Saved — ${cid} will attach to your next send (${loadVaultChunkIds().length} in queue).`,
        false
      );
      const ex = $("#vaultExcerpt");
      if (ex) ex.value = "";
    } catch (e) {
      setVaultStatus(String(e.message || e), true);
    }
  });
}

async function loadProfileFields() {
  const jur = $("#jurisdiction");
  if (!jur) return;
  try {
    const r = await fetch("/v1/profile", { cache: "no-store" });
    if (!r.ok) return;
    const p = await r.json();
    if (p && p.jurisdiction && !jur.value) jur.value = p.jurisdiction;
  } catch (_) {
    /* ignore */
  }
  updateJurisdictionPill();
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
