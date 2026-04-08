#!/usr/bin/env bash
# End-to-end checks like a human using http://127.0.0.1:8765/ (server must already be running).
# Usage: ./scripts/verify_user_flow.sh
# Optional: BASE_URL=http://127.0.0.1:8765 ./scripts/verify_user_flow.sh
set -euo pipefail
BASE="${BASE_URL:-http://127.0.0.1:8765}"
export BASE
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [[ -f .venv/bin/activate ]]; then
  # shellcheck source=/dev/null
  . .venv/bin/activate
fi

fail() { echo "FAIL: $*" >&2; exit 1; }

echo "== Health =="
curl -sS --max-time 5 "${BASE}/health" | python -c "import sys,json; j=json.load(sys.stdin); assert j.get('status')=='ok'; print('ok', j.get('llm_backend'))" || fail health

echo "== GET /v1/health/deep (DB + Hermes self-test, no LLM) =="
curl -sS --max-time 10 "${BASE}/v1/health/deep" | python -c "
import sys, json
j = json.load(sys.stdin)
assert j.get('status') == 'ok', j
st = j.get('hermes_self_test') or {}
assert st.get('clean_answer_passes') is True, j
assert st.get('ocga_leak_fails_as_expected') is True, j
print('hermes self-test ok')
" || fail health_deep

echo "== POST /v1/hermes/check (synthetic payload) =="
curl -sS --max-time 10 -X POST "${BASE}/v1/hermes/check" \
  -H "Content-Type: application/json" \
  -d '{"answer":"ok","verification_ok":true,"verification_errors":[],"vault_empty":true,"session_id":"flowtest","audit":{"vault_chunk_ids":[]}}' \
  | python -c "import sys,json; j=json.load(sys.stdin); assert j.get('hermes_passed') is True, j; print('hermes check ok')" || fail hermes_check

echo "== GET / and static =="
code_root=$(curl -sS -o /dev/null -w "%{http_code}" "${BASE}/")
[[ "$code_root" == "200" ]] || fail "GET / -> $code_root"
code_js=$(curl -sS -o /dev/null -w "%{http_code}" "${BASE}/static/app.js")
[[ "$code_js" == "200" ]] || fail "GET app.js -> $code_js"

echo "== POST /v1/chat (live LLM, case search off) =="
python - <<'PY'
import json, os, urllib.request

base = os.environ["BASE"].rstrip("/")
req = urllib.request.Request(
    base + "/v1/chat",
    data=json.dumps(
        {
            "message": "Reply with exactly one word: verify-ok",
            "session_id": None,
            "search_case_law": False,
        }
    ).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
with urllib.request.urlopen(req, timeout=120) as r:
    body = json.loads(r.read().decode())
assert not body.get("error"), body.get("error")
assert body.get("answer"), "empty answer"
assert body.get("vault_empty") is True
print("answer snippet:", repr((body.get("answer") or "")[:120]))
PY

echo "== POST /v1/chat/stream (SSE) =="
python - <<'PY'
import json, os, urllib.request

base = os.environ["BASE"].rstrip("/")
req = urllib.request.Request(
    base + "/v1/chat/stream",
    data=json.dumps(
        {
            "message": "Say only: stream-check",
            "session_id": None,
            "search_case_law": False,
        }
    ).encode(),
    headers={"Content-Type": "application/json"},
    method="POST",
)
raw = urllib.request.urlopen(req, timeout=120).read().decode("utf-8", errors="replace")
assert "complete" in raw, raw[:800]
assert "step" in raw or "event" in raw, raw[:800]
print("stream ok, bytes:", len(raw))
PY

echo "== Mock-LLM E2E sanitize (proves server strips toxic output) =="
python -m unittest tests.test_e2e_mock_llm_sanitize -q

echo ""
echo "ALL CHECKS PASSED."
echo "Optional (real Chromium UI): FULL=1 python scripts/browser_smoke.py"
