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

## Billing (Phase 6 scaffold)

- Configure Stripe-related settings in `.env`:
  - `FITMATCH_STRIPE_SECRET_KEY`
  - `FITMATCH_STRIPE_WEBHOOK_SECRET`
  - `FITMATCH_STRIPE_PRO_PRICE_ID`
  - `FITMATCH_STRIPE_LIFETIME_PRICE_ID`
- Available billing routes:
  - `POST /api/billing/checkout-session`
  - `POST /api/billing/portal-session`
  - `POST /api/billing/webhook`
  - `GET /api/billing/entitlements`
