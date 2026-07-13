# NexForexAI

A Telegram bot that sends AI-explained forex trading signals (BUY/SELL/HOLD) to users in Uzbek, with Free/Premium/Pro subscription plans, Telegram Payments checkout, and promo codes. The pnpm workspace also hosts an unrelated API server and a Canvas (mockup sandbox) artifact.

## Run & Operate

- `NexForexAI Bot` workflow — runs `cd nexforexai-bot && python bot.py` (Telegram long-polling bot, console output, no port)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000; unrelated to the bot)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages
- `pnpm --filter @workspace/api-spec run codegen` — regenerate API hooks and Zod schemas from the OpenAPI spec
- `pnpm --filter @workspace/db run push` — push DB schema changes (dev only)
- Required env: `DATABASE_URL` — Postgres connection string (shared, provisioned by Replit)
- Bot secrets: `TELEGRAM_BOT_TOKEN`, `TWELVE_DATA_API_KEY` (required); `ANTHROPIC_API_KEY`, `PAYMENT_PROVIDER_TOKEN` (optional — bot degrades gracefully without them)

## Stack

- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5
- DB: PostgreSQL + Drizzle ORM
- Validation: Zod (`zod/v4`), `drizzle-zod`
- API codegen: Orval (from OpenAPI spec)
- Build: esbuild (CJS bundle)
- Bot: Python 3.12, aiogram 3, async SQLAlchemy + asyncpg, Anthropic SDK, Twelve Data API — lives in `nexforexai-bot/` at the workspace root (standalone Python project, not a pnpm package)

## Where things live

- `nexforexai-bot/` — the Telegram bot (`bot.py` entrypoint, `services/` for market data + AI + payments + subscription logic, `db/` for SQLAlchemy models and engine setup, `config.py` for env-driven settings)
- Everything else under `artifacts/` and the workspace root is the unrelated pnpm monorepo scaffold (API server, Canvas mockup sandbox)

## Architecture decisions

- The bot was ported in verbatim from a user-supplied MVP zip, not rewritten. Only infra-glue lines were changed in `config.py` (see Gotchas) to adapt Replit's managed Postgres connection string to what the bot's async SQLAlchemy stack expects.
- Runs as a plain workflow (`configureWorkflow`), not a registered artifact — it's a long-polling bot with no HTTP port, so it doesn't fit the artifact/preview-path model.

## Product

Telegram users pick a currency pair; the bot fetches candles from Twelve Data, computes RSI/EMA20/50/MACD, derives a BUY/SELL/HOLD signal, and (if `ANTHROPIC_API_KEY` is set) asks Claude to explain it in Uzbek. Free/Premium/Pro plans gate daily signal quotas; Premium/Pro can be purchased via Telegram Payments or activated with promo codes; admins (via `ADMIN_IDS`) can `/grant` plans manually.

## User preferences

- When porting a user-supplied codebase, make no code changes beyond what's strictly required to run it in this environment, and call out each such change explicitly.

## Gotchas

- See `.agents/memory/nexforexai-db-connection.md` for the two Postgres connection-string gotchas needed to make Replit's managed `DATABASE_URL` work with a Python async SQLAlchemy + asyncpg stack.

## Pointers

- See the `pnpm-workspace` skill for workspace structure, TypeScript setup, and package details
