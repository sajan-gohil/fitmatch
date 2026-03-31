# FitMatch Backend (Phase 1 Scaffold)

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Run API

```bash
uvicorn app.main:app --reload
```

## Run worker

```bash
celery -A app.core.celery_app.celery_app worker --loglevel=info
```

## Tests

```bash
pytest
```
