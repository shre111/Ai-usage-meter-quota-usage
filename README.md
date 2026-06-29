# AI Usage Metering & Quota Service

A small FastAPI service that exposes an AI text-generation endpoint and meters token
usage against configurable per-user credit quotas. Requests are priced in credits
(weighted tokens × per-user multiplier), checked against the user's allowance before
generation via a reservation, and reconciled to actual usage afterwards.

See [DESIGN.md](DESIGN.md) for the architecture, quota/credit model, failure handling,
and a worked numeric example. See [task.md](task.md) for the original assignment.

## Requirements

- Python 3.11–3.13

## Setup

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
# from the repo root, with the virtualenv activated
uvicorn app.main:app --reload --port 8000
```

- Service: `http://127.0.0.1:8000`
- **Web UI (visual demo):** `http://127.0.0.1:8000/ui/`
- Interactive API docs (Swagger UI): `http://127.0.0.1:8000/docs`
- Health check: `curl localhost:8000/health` → `{"status":"ok"}`

The web UI lets you configure a user, generate text, and watch usage, remaining credits,
and history update live — including quota-exceeded (402) and AI-failure (502) behavior via
the "Simulate AI failure" / "Partial failure" buttons. No build step; it is a single
static page served by the app.

The default AI provider is a deterministic **mock** that returns realistic token usage,
so no API key is needed. It is selected behind an `AIProvider` interface; a real provider
can be added without touching the metering logic.

State is stored in a local SQLite file `quota.db` (created on first run). To start from a
clean slate, stop the server and delete it:

```bash
rm -f quota.db
```

## Test

### Automated tests

```bash
pytest
```

37 tests cover the behaviors the assignment asks for:

- successful generation and usage recording;
- credit calculation and per-user multiplier scaling;
- different users getting different quota/multiplier behavior;
- quota enforcement (enough vs. not enough remaining);
- AI-layer failure, both before usage and after partial usage;
- retrieval of current usage / remaining allowance and history;
- estimate-vs-actual usage (under-use frees credits; over-use is honored as overage);
- near-simultaneous requests from one user (5 threads, no overspend) — `tests/test_concurrency.py`.

### End-to-end testing (manual)

With the server running, run the scripted walkthrough that exercises every scenario:

```bash
./scripts/demo.sh                 # defaults to localhost:8000
BASE=localhost:8000 ./scripts/demo.sh
```

Run it against a fresh `quota.db` to see the quota-exhaustion transition cleanly.

Or step through the scenarios by hand:

```bash
# 1. Configure two users with different quota + multiplier
curl -X PUT localhost:8000/users/alice/config \
  -H 'content-type: application/json' -d '{"monthly_allowance":100,"multiplier":1.5}'
curl -X PUT localhost:8000/users/bob/config \
  -H 'content-type: application/json' -d '{"monthly_allowance":1000,"multiplier":1.0}'

# 2. Successful generation (estimate assumes 300 completion tokens; actual is lower)
curl -X POST localhost:8000/users/alice/generate \
  -H 'content-type: application/json' -d '{"prompt":"Summarize the meeting notes"}'
#    -> estimated_credits 14, actual_credits 6, remaining_credits 94

# 3. Per-user multiplier: same prompt costs more for the higher multiplier
curl -X POST localhost:8000/users/alice/generate \
  -H 'content-type: application/json' -d '{"prompt":"same prompt here"}'   # 1.5x -> 6
curl -X POST localhost:8000/users/bob/generate \
  -H 'content-type: application/json' -d '{"prompt":"same prompt here"}'   # 1.0x -> 4

# 4. Inspect current usage / remaining
curl localhost:8000/users/alice/usage

# 5. Quota exceeded -> HTTP 402 with remaining/required
curl -X PUT localhost:8000/users/carol/config \
  -H 'content-type: application/json' -d '{"monthly_allowance":5,"multiplier":1.0}'
curl -i -X POST localhost:8000/users/carol/generate \
  -H 'content-type: application/json' -d '{"prompt":"hello there"}'

# 6. AI failure BEFORE usage -> HTTP 502, reservation released (usage unchanged)
curl -i -X POST localhost:8000/users/alice/generate \
  -H 'content-type: application/json' -d '{"prompt":"trigger [FAIL] now"}'

# 7. AI failure AFTER partial usage -> HTTP 502, partial usage committed
curl -i -X POST localhost:8000/users/bob/generate \
  -H 'content-type: application/json' -d '{"prompt":"[FAIL_PARTIAL] mid-stream"}'

# 8. Unconfigured user -> HTTP 404
curl -i -X POST localhost:8000/users/ghost/generate \
  -H 'content-type: application/json' -d '{"prompt":"hi"}'

# 9. Usage history (status + multiplier_at_time per record)
curl localhost:8000/users/alice/usage/records

# 10. Multiplier change applies to FUTURE requests only
curl -X PUT localhost:8000/users/bob/config \
  -H 'content-type: application/json' -d '{"multiplier":3.0}'
curl -X POST localhost:8000/users/bob/generate \
  -H 'content-type: application/json' -d '{"prompt":"after the change"}'
curl localhost:8000/users/bob/usage/records   # old records keep their 1.0 multiplier
```

## API

| Method | Path | Purpose |
|--------|------|---------|
| `PUT` | `/users/{user_id}/config` | Create/update quota allowance and/or multiplier |
| `GET` | `/users/{user_id}/usage` | Current usage, remaining credits, and config |
| `POST` | `/users/{user_id}/generate` | Generate text and meter usage |
| `GET` | `/users/{user_id}/usage/records` | Inspect usage history (`?limit=` optional) |

Status codes: `200` success, `402` quota exceeded (body includes remaining/required),
`404` user not configured, `502` AI generation failed.

## Configuration

Environment variables (prefix `QUOTA_`), all optional:

| Variable | Default | Meaning |
|----------|---------|---------|
| `QUOTA_DATABASE_URL` | `sqlite:///./quota.db` | Storage connection string |
| `QUOTA_AI_PROVIDER` | `mock` | AI provider selector |
| `QUOTA_INPUT_WEIGHT` | `1.0` | Weight per prompt token |
| `QUOTA_OUTPUT_WEIGHT` | `3.0` | Weight per completion token |
| `QUOTA_CREDITS_PER_1K_WEIGHTED_TOKENS` | `10.0` | Credits per 1000 weighted tokens |
| `QUOTA_ESTIMATED_COMPLETION_TOKENS` | `300` | Assumed completion length for pre-request estimate |
