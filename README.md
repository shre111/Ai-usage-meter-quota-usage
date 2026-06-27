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
uvicorn app.main:app --reload
```

Interactive API docs at `http://127.0.0.1:8000/docs`. Health check at `GET /health`.

The default AI provider is a deterministic **mock** that returns realistic token usage,
so no API key is needed. It is selected behind an `AIProvider` interface; a real provider
can be added without touching the metering logic.

## Test

```bash
pytest
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

## Example session

```bash
# Configure a user: 100 credits, 1.5x multiplier
curl -X PUT localhost:8000/users/alice/config \
  -H 'content-type: application/json' \
  -d '{"monthly_allowance": 100, "multiplier": 1.5}'

# Generate
curl -X POST localhost:8000/users/alice/generate \
  -H 'content-type: application/json' \
  -d '{"prompt": "Summarize the meeting notes"}'

# Inspect usage and history
curl localhost:8000/users/alice/usage
curl localhost:8000/users/alice/usage/records
```

To demonstrate failure handling, include `[FAIL]` (fails before usage) or `[FAIL_PARTIAL]`
(fails after partial usage) in the prompt.
```bash
curl -X POST localhost:8000/users/alice/generate \
  -H 'content-type: application/json' -d '{"prompt": "boom [FAIL]"}'
```

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
