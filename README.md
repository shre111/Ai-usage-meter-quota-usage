# AI Usage Metering & Quota Service

A small FastAPI service that exposes an AI text-generation endpoint and meters token
usage against configurable per-user credit quotas.

## Status

Work in progress. See [task.md](task.md) for the assignment and `DESIGN.md` (added in a
later PR) for the architecture and quota model.

## Requirements

- Python 3.11–3.13

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

The service exposes a health check at `GET /health`.

## Test

```bash
pytest
```
