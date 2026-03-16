# Progress Log

## Completed Phases

### Phase 1: Auth — done (2026-03-15)
- Backend: `auth.py` (JWT verification), migration 006, chat endpoint with optional auth
- Frontend: Supabase SSR, login page, middleware, UserMenu in header, auth headers on all API calls
- Tests: 12 auth tests passing

### Phase 2: Billing — done (2026-03-15)
- Backend: `services/billing.py`, `api/billing.py`, LemonSqueezy webhooks, migrations 007-009
- Frontend: Pricing page, Account/billing page, checkout/subscription/usage API functions
- Tests: 13 billing tests passing

### Phase 3: Protocol Export — done (2026-03-15)
- Backend: `services/protocol_export.py` (DOCX + PDF via WeasyPrint), export endpoint
- Frontend: ExportButton, EndSessionDialog with export
- Tests: 13 protocol export tests passing

**Total: 189 backend tests passing, 0 TypeScript errors**

---

## Remaining Infra (non-code, dashboard/config)
- [ ] Enable Google OAuth in Supabase dashboard
- [ ] Create LemonSqueezy products/variants, wire variant IDs into VARIANT_TIER_MAP
- [ ] Register LemonSqueezy webhook URL
- [ ] Set prod env vars: SUPABASE_JWT_SECRET, LEMONSQUEEZY_API_KEY/STORE_ID/WEBHOOK_SECRET, NEXT_PUBLIC_SUPABASE_URL/ANON_KEY
- [ ] Install WeasyPrint system deps (cairo, pango) on Render

---

## Phase 4: Output Accuracy Validation — in progress

### Done (TDD: RED -> GREEN -> REFACTOR)
- [x] 4.4 Confidence indicator: `BiostatisticsOutput.confidence_level` (high/medium/low), LLM self-assesses
- [x] 4.5 Disclaimers: auto-appended to computed results ("Verify with your biostatistician...")
- [x] 4.6 ConfidenceBadge component: renders on biostatistics message bubbles
- [x] Tests: 12 confidence tests (test_confidence.py) — TDD, all passing
- [x] Prompt updated with confidence assessment instructions

**Total: 201 backend tests passing, 0 TypeScript errors**

### Done (continued)
- [x] 4.1+4.2 Validation benchmarks: 20 scenarios with exact expected N from published formulas
- [x] 4.3 Automated comparison: `validators/sample_size_validator.py` (score_result, compute_concordance)
- [x] 4.7 Validation report generator: `generate_validation_report()` — publishable markdown with concordance table
- [x] 4.8 CI workflow: `.github/workflows/validation.yml` — triggers on agent/evaluation changes
- [x] Tests: 19 validation benchmark tests (schema, scoring, concordance, report) — all passing

**Total: 201 backend + 19 validation = 220 tests passing, 0 TypeScript errors**

---

### Phase 5: Citation Generation — done (2026-03-16)
- Backend: Reference registry (30+ guidelines), citation extractor (regex), Vancouver bibliography formatter
- Backend: Agent prompts updated with citation rules for all phases
- Backend: Protocol export auto-includes References section from extracted citations
- Tests: 23 citation extractor tests passing

### Phase 6: Saved Projects — done (2026-03-16)
- Backend: Migration 010 (name, description, updated_at on sessions)
- Backend: Projects API (list/search/paginate, rename, soft-delete), Messages API (for resume)
- Backend: Auto-name sessions from first user message, link user_id on session upsert
- Frontend: `/projects` dashboard (search, ProjectCard with inline rename, resume, export, delete)
- Frontend: Resume sessions via `?session=` query param loading message history
- Frontend: "My Projects" link in UserMenu
- Tests: 15 project tests passing

**Total: 243 backend tests passing, 0 TypeScript errors**

---

## Phase 6 Complete. Next: Phase 9 (Calculator Validation)
