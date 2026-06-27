# Design — AI Usage Metering & Quota Service

## 1. Overview

A FastAPI service that exposes an AI text-generation endpoint and meters token usage
against per-user credit quotas. Each request is priced in **credits** derived from the
token usage reported by the AI layer and scaled by a per-user multiplier. The service
decides whether a request is affordable *before* generation (using an estimate) and
records the *actual* cost afterwards.

## 2. Architecture and responsibilities

The project is structured so each responsibility lives in one place:

| Layer | Module | Responsibility |
|-------|--------|----------------|
| API routing / validation | `app/api/` | HTTP endpoints, request/response schemas, status codes |
| Schemas | `app/schemas.py` | Pydantic request/response models |
| AI generation | `app/ai/` | `AIProvider` interface + deterministic `MockProvider`, selected by a factory |
| Credit calculation | `app/services/credits.py` | Pure, deterministic token→credit functions |
| Quota enforcement | `app/services/quota.py` | Atomic reserve / commit / release of credits |
| Orchestration | `app/services/metering.py` | estimate → reserve → generate → commit/release + recording |
| Persistence | `app/db.py`, `app/models.py`, `app/repositories.py` | SQLAlchemy engine, ORM models, data access |

This separation makes the foreseeable changes cheap: a new AI endpoint is a new router
calling the same `GenerationService`; a different provider is a new class behind
`AIProvider`; moving off SQLite is a connection-string change because all access goes
through the repository/session layer; a new quota period or plan is a field/policy change
in the quota model and credit functions.

## 3. Persistence choice

**SQLite via SQLAlchemy 2.0.** It is zero-setup and file-backed (survives restarts),
which is enough to demonstrate real accounting and history, while the repository
abstraction keeps a future move to Postgres mechanical. The tradeoff is that SQLite
serializes writes; for a single-instance metering service this is acceptable and actually
helps the concurrency guarantee below. A multi-instance deployment would move the same
atomic-guard logic to Postgres (`SELECT ... FOR UPDATE` or the identical guarded
`UPDATE`).

Two tables:

- `user_quotas`: `user_id` (PK), `monthly_allowance`, `multiplier`, `used_credits`,
  `reserved_credits`.
- `usage_records`: one row per attempt with token counts, `estimated_credits`,
  `actual_credits`, `multiplier_at_time`, and `status` (`success` / `failed` /
  `rejected`). Storing `multiplier_at_time` keeps history truthful when the multiplier
  later changes.

## 4. Credit model (explicit and deterministic)

```
weighted_tokens = prompt_tokens * INPUT_WEIGHT + completion_tokens * OUTPUT_WEIGHT
credits         = ceil(weighted_tokens / 1000 * CREDITS_PER_1K_WEIGHTED_TOKENS * multiplier)
```

Defaults (in `app/config.py`): `INPUT_WEIGHT=1`, `OUTPUT_WEIGHT=3`,
`CREDITS_PER_1K_WEIGHTED_TOKENS=10`. Output tokens are weighted 3× input, mirroring real
LLM pricing. `ceil` guarantees a non-zero, integer charge. The multiplier is the per-user
commercial lever. The rule is identical for the pre-request estimate and the post-request
actual — only the completion-token count differs.

## 5. Quota model

`remaining = monthly_allowance - used_credits - reserved_credits`.

- **Allowance and multiplier are per user** and updatable at any time.
- A multiplier change applies to **future** requests only; past `usage_records` keep the
  multiplier they were charged at.
- Monthly period rollover is intentionally out of scope (documented as future work): the
  schema carries the allowance/usage needed to add it without restructuring.

## 6. Estimate vs. actual and concurrency (the core)

The exact cost is unknown until generation finishes, and multiple requests can arrive
together. We use a **reservation pattern backed by a single atomic, guarded SQL UPDATE**:

1. **Estimate** credits from the prompt, assuming `estimated_completion_tokens` (or the
   caller's `max_tokens`).
2. **Reserve**:
   ```sql
   UPDATE user_quotas
      SET reserved_credits = reserved_credits + :est
    WHERE user_id = :u
      AND (monthly_allowance - used_credits - reserved_credits) >= :est
   ```
   `rowcount == 0` ⇒ not affordable ⇒ **402** (a `rejected` record is written).
3. **Generate** via the AI provider.
4. **Commit**: `reserved -= est; used += actual` (actual computed from reported usage).
5. **Release** (on failure with no usage): `reserved -= est`.

Why this is correct under concurrency: the guarded UPDATE is atomic, so two
near-simultaneous requests can never both pass the affordability check beyond the
allowance — the reservation is taken before generation and held until commit. Because the
guard is in the database, no application-level lock is needed.

**Estimate ≠ actual:**
- *Actual < estimate* (typical): we over-reserve, then commit the smaller actual; the
  difference is freed at commit.
- *Actual > estimate*: the result is already generated, so we honor it, commit the larger
  actual, and **allow `used` to exceed the allowance (overage)**. The next request then
  sees negative remaining and is rejected. This is an intentional product choice: never
  throw away work the user already received, but stop the bleeding immediately.

## 7. Failure handling

| Situation | Behavior | Status |
|-----------|----------|--------|
| User has no quota config | Reject before any work | 404 |
| At/over quota (estimate doesn't fit) | Reject, write `rejected` record | 402 (+ remaining/required) |
| AI fails **before** usage | Release reservation, write `failed` (0 credits) | 502 |
| AI fails **after** partial usage | Commit reported partial usage, write `failed` | 502 |
| Success | Commit actual, write `success` | 200 |

The mock provider exposes `[FAIL]` (fail before usage) and `[FAIL_PARTIAL]` (fail after
partial usage) sentinels so every row of this table is demonstrable and tested.

## 8. Concrete numerical example (matches the implementation)

User **alice**: `monthly_allowance = 100`, `multiplier = 1.5`. Defaults as in §4.

Request: `prompt = "Summarize the meeting notes"` (27 chars → `count_tokens = ceil(27/4) = 7`).

- **Estimate** (no `max_tokens`, so assume 300 completion tokens):
  `weighted = 7*1 + 300*3 = 907` → `907/1000*10*1.5 = 13.605` → **`ceil = 14`**.
- **Reserve 14**: remaining `100 - 0 - 0 = 100 ≥ 14` → reserved, remaining now `86`.
- **Generation** returns `prompt_tokens = 7`, `completion_tokens = 128`.
- **Actual**: `weighted = 7*1 + 128*3 = 391` → `391/1000*10*1.5 = 5.865` → **`ceil = 6`**.
- **Commit**: `reserved 14 → 0`, `used 0 → 6`.

**Decision: ALLOWED.** Estimated 14, actual 6, recorded usage 6, **remaining = 94**.

Overage variant: if the same request had returned 5000 completion tokens, actual would be
`ceil((7 + 5000*3)/1000*10*1.5) = 226`. With a 100 allowance the request still succeeds
(it was already reserved/affordable on estimate), `used` becomes 226, remaining `-126`,
and every subsequent request is rejected with 402 until usage is reset or allowance
raised.

## 9. Testing

`pytest` (37 tests) covers: credit math and multiplier scaling, per-user independence,
quota enforcement (enough vs. not enough), AI-layer failure (before and after partial
usage), estimate-vs-actual (under and overage), usage/remaining retrieval, history
recording, and **near-simultaneous requests** (5 threads against one allowance, asserting
no overspend).

## 10. Deliberate non-goals

Auth, rate limiting, real provider integration, and monthly rollover are out of scope but
each has a clear seam (provider factory, repository layer, quota fields) to add later.
