# backend

FastAPI + PostgreSQL. Python 3.13.

## Layout

```
app/
  main.py            FastAPI app + router wiring + CORS
  core/config.py     pydantic-settings (env / .env)
  db/
    base.py          DeclarativeBase + TimestampMixin
    session.py       engine, SessionLocal, get_db() dependency
  models.py          ORM: User, Topic, Story, Subscription, UsageEvent
  schemas.py         Pydantic request/response models
  api/routes/
    health.py        GET /health
    topics.py        GET /topics
    stories.py       GET /stories, POST /stories/generate (501 until Fase 2)
alembic/             migrations (0001_initial = full schema)
scripts/seed_topics.py
```

## Commands

```bash
alembic upgrade head                 # apply schema
alembic revision --autogenerate -m x # after model changes (needs live DB)
alembic upgrade head --sql           # render SQL without a DB (sanity check)
python -m scripts.seed_topics        # load the topic catalogue
uvicorn app.main:app --reload
```

## Auth (Fase 1 stap 4 — done)

- `app/core/security.py`: `get_current_user` verifies the Supabase JWT and
  upserts a `users` row (+ a `free` `subscriptions` row) on first sight.
- **This project signs tokens asymmetrically (ES256)** — verification uses the
  public JWKS at `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`
  (`SUPABASE_URL` required; `SUPABASE_JWT_SECRET` is the unused legacy HS256
  fallback). `verify_supabase_jwt` picks the path from the token's `alg` header.
- Needs `PyJWT[crypto]` + `certifi` (the python.org macOS build has no system
  CA roots, so the JWKS fetch gets an explicit `certifi` bundle).
- Protected: `GET /me`, `GET /stories`, `POST /stories/generate`.
- Tests: `tests/test_security.py` (HS256 path, no DB) and
  `tests/test_api_auth.py` (401/503 guards). End-to-end ES256 + upsert is
  verified against the live Supabase project on the simulator.

## Notes for later phases

- **Fase 2 (generation):** `POST /stories/generate` builds the prompt, calls the
  LLM, runs moderation (system prompt + moderation API + blocklist; regenerate
  once, else HTTP 422), then persists with `moderation_status = approved`.
- **Fase 5 (limits):** count `usage_events` in a rolling 7-day window against the
  free-tier cap before allowing generation.
