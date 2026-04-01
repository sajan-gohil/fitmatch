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

## Platform extensions (Phase 11 scaffold)

- Configure optional settings in `.env`:
  - `FITMATCH_SLACK_WEBHOOK_URL`
  - `FITMATCH_PHASE11_FEATURE_FLAGS_ENABLED`
  - `FITMATCH_PHASE11_SALARY_CACHE_TTL_SECONDS`
  - `FITMATCH_PHASE11_QUEUE_BATCH_SIZE`
- Available platform routes:
  - `GET /api/platform/feature-flags`
  - `GET /api/platform/feature-flags/admin`
  - `PUT /api/platform/feature-flags/admin`
  - `PUT /api/platform/feature-flags/overrides`
  - `GET /api/platform/slack/preferences`
  - `PUT /api/platform/slack/preferences`
  - `POST /api/platform/slack/alerts/test`
  - `GET /api/platform/slack/events`
  - `GET /api/platform/referrals/code`
  - `POST /api/platform/referrals/track`
  - `GET /api/platform/referrals/summary`
  - `GET /api/platform/performance/salary-benchmark`
  - `GET /api/platform/performance/queue-controls`
