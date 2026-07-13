---
name: Replit managed Postgres + Python async SQLAlchemy/asyncpg connection gotchas
description: Two DATABASE_URL rewrites needed when pointing a Python async SQLAlchemy (asyncpg) app at Replit's built-in Postgres.
---

Replit's managed `DATABASE_URL` env var is a plain libpq-style connection string. Two mismatches surface when a Python app uses async SQLAlchemy with the `asyncpg` driver:

1. **Driver scheme**: Replit provides `postgresql://...`; SQLAlchemy's async engine requires the driver marker `postgresql+asyncpg://...`. Fix: rewrite the scheme prefix at startup (in whatever module reads `DATABASE_URL`) rather than trying to set a different `DATABASE_URL` yourself — it's a runtime-managed secret and can't be overridden via normal env var tools.

2. **`sslmode` query param**: If the connection string carries `?sslmode=require` (libpq/psycopg naming), SQLAlchemy's asyncpg dialect passes it straight through as a kwarg to `asyncpg.connect()`, which has no `sslmode` parameter (only `ssl`) — this raises `TypeError: connect() got an unexpected keyword argument 'sslmode'`. Fix: rewrite `sslmode=` to `ssl=` in the query string before creating the engine.

**Why:** Both failures only show up at runtime once real secrets are wired in (they don't show up from reading the code), and the second one is easy to misdiagnose as a network/SSL config problem rather than a param-naming mismatch between psycopg-style and asyncpg-style connection kwargs.

**How to apply:** Any time you wire a Python app using SQLAlchemy async + asyncpg to Replit's built-in `DATABASE_URL`, apply both string rewrites where the URL is first read (e.g. a config module), before passing it to `create_async_engine`.

Separately: when installing a pinned `anthropic` SDK version (e.g. `anthropic==0.39.0`) alongside a modern `httpx`, watch for `TypeError: AsyncClient.__init__() got an unexpected keyword argument 'proxies'` — older anthropic releases pass a `proxies` kwarg that recent httpx versions removed. Fix by upgrading anthropic to a current release rather than pinning httpx down.
