#!/usr/bin/env bash
# End-to-end demo: exercises every scenario against a running server.
# Usage: BASE=localhost:8000 ./scripts/demo.sh   (BASE defaults to localhost:8000)
set -euo pipefail
B="${BASE:-localhost:8000}"

post() { curl -s -w "\nHTTP %{http_code}\n" -X POST "$B$1" -H 'content-type: application/json' -d "$2"; }
put()  { curl -s -X PUT "$B$1" -H 'content-type: application/json' -d "$2"; echo; }
get()  { curl -s "$B$1" | python3 -m json.tool; }

echo "== health =="; curl -s "$B/health"; echo

echo; echo "== configure users (different quota + multiplier) =="
put /users/alice/config '{"monthly_allowance":100,"multiplier":1.5}'
put /users/bob/config   '{"monthly_allowance":1000,"multiplier":1.0}'

echo "== successful generation (estimate vs actual) =="
post /users/alice/generate '{"prompt":"Summarize the meeting notes"}'

echo; echo "== per-user multiplier (same prompt, different cost) =="
post /users/alice/generate '{"prompt":"same prompt here"}'
post /users/bob/generate   '{"prompt":"same prompt here"}'

echo; echo "== usage summaries =="
get /users/alice/usage
get /users/bob/usage

echo; echo "== quota exceeded (402) =="
put /users/carol/config '{"monthly_allowance":5,"multiplier":1.0}'
post /users/carol/generate '{"prompt":"hello there"}'

echo; echo "== AI failure before usage (502, reservation released) =="
post /users/alice/generate '{"prompt":"trigger [FAIL] now"}'

echo "== AI failure after partial usage (502, partial committed) =="
post /users/bob/generate '{"prompt":"[FAIL_PARTIAL] mid-stream"}'

echo; echo "== unconfigured user (404) =="
post /users/ghost/generate '{"prompt":"hi"}'

echo; echo "== usage history =="
get /users/alice/usage/records

echo; echo "== multiplier change applies to future requests only =="
put /users/bob/config '{"multiplier":3.0}'
post /users/bob/generate '{"prompt":"after the change"}'
get /users/bob/usage/records

echo; echo "== exhaust a quota -> later requests 402 =="
put /users/dan/config '{"monthly_allowance":40,"multiplier":1.0}'
for i in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w "%{http_code}" -X POST "$B/users/dan/generate" \
    -H 'content-type: application/json' -d '{"prompt":"go","max_tokens":100}')
  echo "  request $i -> HTTP $code"
done
get /users/dan/usage
