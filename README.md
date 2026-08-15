# ReproClip Autonomous Company

The separate Pioneer and Terac growth system for [ReproClip](https://github.com/KaushikSiva/repro-clip). The product remains open source; this service owns growth decisions, Terac human-work studies, founder approvals, campaign memory, referral creation, and the operations console. ReproClip itself owns Stripe Checkout and writes verified payments into the shared Supabase database.

```text
Pioneer CEO → Terac creators/testers → referral distribution
      ↑                                      ↓
business memory ← Stripe $5 support ← ReproClip
```

No marketing employees. No seeded revenue. No automatic creator payout approval.

## Local setup

Create `.env` first. For a real local-to-production test, paste your Supabase URLs as described below. If `SUPABASE_DATABASE_URL` is blank, the backend deliberately falls back to a local SQLite file.

```bash
cp .env.example .env

cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload

# separate terminal
cd web
npm install
npm run dev
```

Open `http://localhost:3001/company`. The backend is `http://localhost:8000`.

## Supabase database

1. Create a Supabase project and open **Connect** in the project dashboard.
2. For `SUPABASE_DATABASE_URL`, copy the **Session pooler** connection string on port `5432`. This works from Render's persistent FastAPI service over IPv4.
3. For `SUPABASE_MIGRATION_URL`, use the direct connection string when your machine/deployment has IPv6. Otherwise use the same Session pooler URL.
4. URL-encode special characters in the database password.
5. Apply the checked-in Alembic schema:

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/alembic current
```

Expected head:

```text
1a81ff1d16b5 (head)
```

Supabase is accessed only by the FastAPI server. No database password or service-role credential is sent to the Next.js client. Alembic remains the one schema-migration authority; do not make production schema edits manually in Supabase's Table Editor.

For Render, prefer the Supavisor Session pooler. If transaction mode on port `6543` is intentionally selected, the backend automatically disables prepared statements and SQLAlchemy connection pooling as required by that mode.

## Safety boundaries

- Stripe revenue appears only after a signature-verified webhook.
- Pioneer output is validated against a strict Pydantic schema; only concise business rationale is stored.
- Terac status changes only after a real MCP response.
- Creator work requires `FOUNDER_APPROVAL_TOKEN`; AI recommendations cannot approve payment.
- Human, social, and financial metrics remain zero or unavailable until persisted results exist.

## Stripe signal ownership

Stripe credentials, `/support`, `/thanks`, Checkout creation, and webhook verification live in the main ReproClip application. Both services use the same `SUPABASE_DATABASE_URL`; growth-engine reads `stripe_payments` and `visits` as business signals but does not execute payments. Configure Stripe's webhook as `https://YOUR-REPROCLIP-HOST/api/stripe/webhook`.

## Terac

Create a Terac organization API key (`tk_…`) and set `TERAC_API_KEY`. The integration connects to `https://terac.com/api/mcp`, discovers tools, requests feasibility, waits for a real quote, and exposes a separate founder action to launch spend. Creator and general-population studies are separate records.

## Pioneer

Set `PIONEER_API_KEY` and a supported open-weight model in `PIONEER_MODEL` (or use `Qwen/Qwen3-8B`). The CEO receives only persisted business state and returns schema-validated JSON. Missing credentials leave the CEO explicitly unavailable.

## Render

Create a Blueprint from `render.yaml`. The Blueprint intentionally does not create a Render Postgres database—Supabase is the only production database. After Render assigns URLs, set:

- API `SUPABASE_DATABASE_URL` to the Session pooler URL.
- API `SUPABASE_MIGRATION_URL` to the direct or Session pooler migration URL.
- API `APP_BASE_URL` to the company web URL.
- API `PRODUCT_BASE_URL` to the deployed ReproClip product URL.
- API `CORS_ORIGINS` to both URLs.
- Web `NEXT_PUBLIC_API_URL` and `COMPANY_API_URL` to the API URL.
- Product `REPROCLIP_COMPANY_URL` to the company web URL.

Then add Pioneer, Terac, and optional Linq secrets in Render. `alembic upgrade head` runs against Supabase as the pre-deploy migration command already defined in the Blueprint. Configure Stripe only on the main ReproClip service.

## Tests

```bash
cd backend && .venv/bin/pytest -q
cd web && npm run typecheck && npm run lint && npm run build
```

## Exact demo flow

1. Open `/company`; verify Supabase is connected and revenue plus all unavailable integrations are honest zero-state values.
2. Add keys in Render, set a nonzero `TERAC_BUDGET_USD`, and open the main ReproClip app's `/support` page in a second window.
3. In the company console, run the Pioneer CEO with the founder token. A schema-validated decision and next campaign draft are persisted.
4. Open that campaign and request creator feasibility. The screen shows only the real Terac request ID/status/cost.
5. When Terac prices it, click **Approve spend & launch**. Sync submissions from the real opportunity.
6. Ingest a creator submission from the Terac result, review its media, and manually approve or reject it. No payout approval is automated.
7. With at least two approved creatives, request the separate general-population study and ingest the real per-creative scores.
8. Share the campaign or creator `/r/<code>` URL. The redirect records the visit and preserves campaign/creator attribution through ReproClip.
9. Click **Support ReproClip — $5** in the main app and complete real Stripe Checkout. ReproClip's signed webhook persists $5 and attribution into shared Supabase.
10. Return to `/demo`: the payment appears. Run the next Pioneer review to use that revenue signal in the next Terac campaign decision.

## Result ingestion and optional services

- `POST /api/submissions/ingest` accepts a real Terac creator result for founder review.
- `POST /api/human-tests/ingest` accepts structured scores from the real general-population study.
- `POST /api/social-posts` records a creator-submitted public URL and only metrics actually provided.
- `POST /api/company/qa/replay` stores a Replay run URL and its real PASS/FAIL checks; the UI never invents QA status.
- Linq sends founder review notifications when configured. ReproClip itself can also send the public YouTube link to your phone.

These mutation routes require `X-Founder-Token` except public referrals and visits. Checkout and the signed Stripe webhook are served by the main ReproClip application.
