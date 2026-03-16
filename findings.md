# Findings

## Codebase Analysis for Market Analysis Implementation (2026-03-15)

### What Already Exists
- **Evaluation framework:** Comprehensive benchmark suite in `evaluation/` with test cases, collectors, judges, and analysis. Phase 4 (validation) is partially done.
- **Summary export:** Basic .txt download via `downloadSummary()` in `frontend/src/lib/api.ts`. Phase 3 (protocol export) will replace this with DOCX/PDF.
- **Token logging:** `token_logs` table tracks prompt/completion tokens per node per session. Can be repurposed for usage metering.
- **Session evaluation:** Star rating (1-5) + comment already implemented (`session_evaluations` table, `EvaluationDialog.tsx`).
- **File processing:** PDF/DOCX/image upload with text extraction already works. Not persisted to DB.
- **`python-docx` already in deps:** Can be used for DOCX export without new dependency.
- **Supabase already in stack:** Auth can be enabled without infrastructure changes.

### Architecture Constraints
- **No user identity:** Sessions are anonymous UUIDs. Auth (Phase 1) must come first before billing, projects, or collaboration.
- **Fire-and-forget logging:** `log_message()` and `log_tokens()` use `asyncio.create_task`. Usage metering needs guaranteed persistence (not fire-and-forget).
- **20-message sliding window:** Session memory is limited. Saved projects (Phase 6) need full history access.
- **Frontend is 900+ lines (HomeClient.tsx):** Will need refactoring as features grow. Extract into smaller components.
- **No SSR auth:** Currently pure client-side. Adding Supabase Auth will need middleware for protected routes.

### Decisions Made
1. **Auth:** Supabase Auth (email + Google OAuth)
2. **Billing:** LemonSqueezy (handles tax/compliance automatically)
3. **DOCX library:** `python-docx` (already installed)
4. **PDF library:** WeasyPrint (HTML->PDF, good formatting)
5. **i18n approach:** next-intl (App Router native) — for future Phase 7

### Integration Research (2026-03-15)

#### Supabase Auth
- **Frontend packages:** `@supabase/supabase-js` + `@supabase/ssr`
- **Backend packages:** `PyJWT` (HS256 local validation, zero latency)
- **Pattern:** Client components use `createBrowserClient`, server components use `createServerClient`
- **Critical rule:** Never trust `getSession()` in server code, always use `getUser()`
- **JWT claims:** `sub` = user UUID, `email`, `role` = "authenticated", `aud` = "authenticated"
- **Middleware:** `middleware.ts` guards all routes except /login, /signup, /auth
- **OAuth flow:** PKCE via `/auth/callback/route.ts` that calls `exchangeCodeForSession()`
- **Backend:** `PyJWT` decodes with `audience="authenticated"`, extracts `sub` as user_id
- **Future:** Supabase migrating to ES256/JWKS (mandatory late 2026), plan upgrade later

#### LemonSqueezy Billing
- **Frontend:** Load `lemon.js` script, use overlay checkout or redirect
- **Backend packages:** `httpx` for API calls
- **User mapping:** Pass `user_id` via `checkout_data.custom.user_id`, arrives in `meta.custom_data.user_id` in webhooks
- **Webhook verification:** HMAC-SHA256 on raw body bytes, `X-Signature` header, `X-Event-Name` header
- **Key events:** subscription_created, subscription_updated, subscription_cancelled, subscription_payment_failed
- **Customer portal:** `urls.customer_portal` from subscription object — hosted by LemonSqueezy, no custom UI
- **Env vars needed:** `LEMONSQUEEZY_API_KEY`, `LEMONSQUEEZY_STORE_ID`, `LEMONSQUEEZY_WEBHOOK_SECRET`

#### WeasyPrint for PDF Export
- Converts HTML -> PDF with CSS support
- Install: `uv add weasyprint` (has system deps: cairo, pango, gdk-pixbuf)
- Pattern: Generate HTML template with Jinja2, convert to PDF bytes
- Good for: formatted protocol sections with tables, headings, citations

### Market Analysis Key Numbers
- TAM: $1.2B-$1.9B (all medical researchers)
- SAM: $120M-$240M (junior clinical researchers)
- SOM Year 1: $120K-$480K (500-2,000 paying users)
- Target ARPU: ~$20/month
- LLM COGS: $0.05-0.30 per query
- Competitor pricing: Elicit $12-79/mo, nQuery $925-7,495/yr

---

## Previous Findings: Expertise Level Feature (preserved)

### Architecture Analysis
All 7 agent nodes follow identical pattern with `SystemMessage(content=PROMPT_CONSTANT)` as the injection point for expertise-level-aware prompts. Style directive prefix approach chosen over duplicate prompts.
