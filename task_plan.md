# ProtoCol: Market Analysis Implementation Plan

**Goal:** Implement product recommendations from the market analysis to prepare ProtoCol for monetization.

**Source:** Market analysis document

**Current State:** Working chatbot with 3 phases, auth (Supabase JWT), billing (LemonSqueezy), protocol export (DOCX/PDF), account page, 189 backend tests passing, 0 TS errors. Remaining: dashboard/infra config (non-code).

---

## Phase 1: Authentication & User Accounts (CRITICAL)
**Priority:** P0 | **Status:** `done` | **Completed:** 2026-03-15

### Tasks
- [x] 1.1 Backend: Auth module (`backend/app/auth.py`) — JWT verification, get_current_user, get_optional_user
- [x] 1.2 Backend: Migration 006 — `user_id` column on sessions
- [x] 1.3 Backend: Chat endpoint updated with optional auth
- [x] 1.4 Frontend: Supabase client/server wrappers (`lib/supabase/`)
- [x] 1.5 Frontend: Login page (email + Google OAuth) + server actions
- [x] 1.6 Frontend: Auth middleware (`middleware.ts`) + OAuth callback route
- [x] 1.7 Frontend: UserMenu component + added to header
- [x] 1.8 Frontend: All API calls include auth headers
- [x] 1.9 Tests: 12 auth tests (JWT validation, expired/invalid/missing, optional user)
- [ ] 1.10 **INFRA**: Enable Google OAuth in Supabase dashboard (non-code)
- [ ] 1.11 **INFRA**: Set SUPABASE_JWT_SECRET in production (non-code)

---

## Phase 2: Usage Metering & Billing (CRITICAL)
**Priority:** P0 | **Status:** `done` | **Completed:** 2026-03-15
**Note:** Switched from Stripe to LemonSqueezy (handles tax/compliance automatically)

### Tasks
- [x] 2.1 Backend: Billing service (`services/billing.py`) — checkout, subscriptions, usage metering
- [x] 2.2 Backend: Billing API (`api/billing.py`) — checkout, subscription, usage, LemonSqueezy webhooks
- [x] 2.3 Backend: Migrations 007 (subscriptions), 008 (usage_tracking), 009 (webhook_events)
- [x] 2.4 Backend: Chat endpoint updated with usage metering
- [x] 2.5 Frontend: Pricing page with tier comparison + annual toggle
- [x] 2.6 Frontend: Account/billing page (subscription, usage bar, manage links)
- [x] 2.7 Frontend: API functions (getSubscription, getUsage, createCheckout)
- [x] 2.8 Tests: 13 billing tests (tier mapping, auth gates, webhook signatures)
- [ ] 2.9 **INFRA**: Create LemonSqueezy products/variants + wire variant IDs (non-code)
- [ ] 2.10 **INFRA**: Register webhook URL in LemonSqueezy dashboard (non-code)
- [ ] 2.11 **INFRA**: Set LEMONSQUEEZY_* env vars in production (non-code)

---

## Phase 3: Protocol/Report Export (CRITICAL)
**Priority:** P0 | **Status:** `done` | **Completed:** 2026-03-15

### Tasks
- [x] 3.1 Backend: Protocol export service (`services/protocol_export.py`) — DOCX + PDF (WeasyPrint)
- [x] 3.2 Backend: Export endpoint `GET /api/sessions/{id}/export?format=docx|pdf`
- [x] 3.3 Frontend: ExportButton component (format selector)
- [x] 3.4 Frontend: EndSessionDialog updated with protocol export
- [x] 3.5 Tests: 13 protocol export tests (section building, DOCX generation, format routing)
- [ ] 3.6 **INFRA**: Install WeasyPrint system deps (cairo, pango) on Render (non-code)

---

## Phase 4: Output Accuracy Validation (CRITICAL)
**Priority:** P0 | **Status:** `done` | **Completed:** 2026-03-15

### What
- Systematic evaluation framework (already partially built in `evaluation/`)
- Validate sample size calculations against known benchmarks (nQuery/PASS)
- Publish accuracy metrics
- Add disclaimer/confidence indicators to outputs

### Tasks
- [x] 4.1 Expand test cases — 20 validation benchmarks in `validation_benchmarks.json`
- [x] 4.2 Validation dataset — exact expected N from published formulas (Chow, Machin, Julious, statsmodels)
- [x] 4.3 Automated comparison — `validators/sample_size_validator.py` (scoring: exact, 5%, 10%, deviation%)
- [x] 4.4 Add confidence indicator to agent outputs (high/medium/low) — `BiostatisticsOutput.confidence_level`
- [x] 4.5 Add disclaimers to statistical outputs — auto-appended to computed results
- [x] 4.6 Frontend: ConfidenceBadge component displayed on biostatistics messages
- [x] 4.7 Validation report generator — `generate_validation_report()` produces publishable markdown
- [x] 4.8 CI validation suite — `.github/workflows/validation.yml` triggers on agent/evaluation changes

### Files Created/Modified (4.4-4.6)
- `backend/app/agents/state.py` — Added `ConfidenceLevel` type, `confidence_level` to `BiostatisticsOutput` + `ResearchState`
- `backend/app/agents/biostatistics.py` — Propagate confidence, disclaimer on execution results
- `backend/app/agents/prompts.py` — Confidence level assessment instructions
- `backend/app/api/chat.py` — SSE streams confidence in message events
- `backend/tests/test_confidence.py` — 12 tests (TDD)
- `frontend/src/components/ConfidenceBadge.tsx` — New component
- `frontend/src/components/MessageBubble.tsx` — Renders ConfidenceBadge
- `frontend/src/lib/api.ts` — `confidence` field on ChatMessage + ChatEventData
- `frontend/src/app/HomeClient.tsx` — Passes confidence through SSE events

---

## Phase 5: Citation Generation (HIGH PRIORITY)
**Priority:** P1 | **Status:** `done` | **Completed:** 2026-03-16

### What
- Every recommendation references its source guideline (CONSORT, STROBE, SPIRIT, etc.)
- Inline citations in agent responses
- Bibliography section in exports

### Tasks
- [x] 5.1 Create citation database (guidelines, textbooks, key references per topic)
- [x] 5.2 Modify agent prompts to include citation instructions
- [x] 5.3 Add citation formatting (APA/Vancouver style)
- [x] 5.4 Include bibliography in protocol export (Phase 3)
- [x] 5.5 Tests: 23 citation extractor tests

### Files Created/Modified
- `backend/app/data/reference_registry.py` (new — 30+ guideline references)
- `backend/app/services/citation_extractor.py` (new — regex extraction + Vancouver formatter)
- `backend/app/agents/prompts.py` (modified — citation rules for all phases)
- `backend/app/services/protocol_export.py` (modified — References section)
- `backend/tests/test_citation_extractor.py` (new — 23 tests)

---

## Phase 6: Saved Projects (HIGH PRIORITY)
**Priority:** P1 | **Status:** `done` | **Completed:** 2026-03-16
**Depends on:** Phase 1 (auth)

### What
- Users can save, name, revisit, and iterate on research plans
- Project dashboard (list, search, resume)
- Simplified: project = named session (no separate table needed yet)

### Tasks
- [x] 6.1 Backend: Migration 010 — name, description, updated_at columns on sessions
- [x] 6.2 Backend: Projects API (list/search/paginate, rename, soft-delete)
- [x] 6.3 Backend: Messages API (GET /sessions/{id}/messages for resume)
- [x] 6.4 Backend: Auto-name sessions from first user message
- [x] 6.5 Backend: Link user_id to sessions on upsert (chat.py)
- [x] 6.6 Frontend: /projects dashboard (search, project list)
- [x] 6.7 Frontend: ProjectCard (inline rename, resume, export, delete)
- [x] 6.8 Frontend: Resume sessions via ?session= query param
- [x] 6.9 Frontend: "My Projects" link in UserMenu
- [x] 6.10 Tests: 15 project tests (auth isolation, CRUD, messages)

### Files Created/Modified
- `backend/migrations/010_session_metadata.sql` (new)
- `backend/app/api/projects.py` (new)
- `backend/app/api/sessions.py` (modified — messages endpoint)
- `backend/app/api/chat.py` (modified — auto-name, user_id linking)
- `backend/app/main.py` (modified — register projects router)
- `backend/app/models.py` (modified — project/message models)
- `backend/tests/test_projects.py` (new — 15 tests)
- `frontend/src/app/projects/page.tsx` (new)
- `frontend/src/app/projects/ProjectsClient.tsx` (new)
- `frontend/src/components/ProjectCard.tsx` (new)
- `frontend/src/app/HomeClient.tsx` (modified — session resume)
- `frontend/src/app/page.tsx` (modified — Suspense wrapper)
- `frontend/src/components/UserMenu.tsx` (modified — My Projects link)
- `frontend/src/lib/api.ts` (modified — project/message API functions)

---

## Phase 7: Multi-Language Support (HIGH PRIORITY)
**Priority:** P1 | **Status:** `not_started` | **Estimate:** 2-3 weeks

### What
- Thai language first (Mac's home market)
- Then Mandarin, Japanese, Korean
- UI localization + agent response language

### Tasks
- [ ] 7.1 Frontend: Set up next-intl or next-i18next
- [ ] 7.2 Frontend: Extract all UI strings to translation files
- [ ] 7.3 Frontend: Language switcher component
- [ ] 7.4 Backend: Accept `language` parameter in chat requests
- [ ] 7.5 Backend: Modify agent prompts to respond in requested language
- [ ] 7.6 Create Thai translations (UI + medical terminology)
- [ ] 7.7 Tests: Language switching, Thai response generation

---

## Phase 8: Collaboration (HIGH PRIORITY)
**Priority:** P1 | **Status:** `not_started` | **Estimate:** 2 weeks
**Depends on:** Phase 1 (auth), Phase 6 (projects)

### What
- Share projects between PI and resident
- Role-based access (owner, editor, viewer)
- Activity feed / comments

### Tasks
- [ ] 8.1 Backend: `project_members` table (project_id, user_id, role)
- [ ] 8.2 Backend: Invitation system (email invite, accept/decline)
- [ ] 8.3 Backend: Permission checks on project access
- [ ] 8.4 Frontend: Share dialog with email invite
- [ ] 8.5 Frontend: Member list with role management
- [ ] 8.6 Tests: Permission checks, invitation flow

---

## Phase 9: Calculator Validation (HIGH PRIORITY)
**Priority:** P1 | **Status:** `in_progress` | **Started:** 2026-03-16

### What
- Run every sample size scenario against nQuery/PASS published results
- Publish comparison table
- This is the #1 trust-building asset

### Tasks
- [x] 9.1 Compile 50+ common sample size scenarios with published results (V01-V50)
- [ ] 9.2 Build automated test runner against ProtoCol's biostatistics agent
- [x] 9.3 Score concordance (exact match, within 5%, within 10%) — already built in Phase 4
- [ ] 9.4 Fix any calculation discrepancies found
- [x] 9.5 Report generator — already built in Phase 4
- [ ] 9.6 Add validation results to marketing site / benchmark page

### Benchmark Coverage (50 scenarios)
| Category | Count | IDs |
|----------|-------|-----|
| Two-sample t-test | 8 | V01,V02,V14,V19,V23,V24,V40,V41 |
| One-sample t-test | 2 | V21,V22 |
| Paired t-test | 4 | V03,V33,V34,V47(crossover) |
| Two proportions | 7 | V04,V05,V18,V35,V36,V37,V38,V39 |
| Single proportion | 3 | V20,V44,V45 |
| ANOVA | 4 | V06,V07,V31,V32 |
| Survival (Schoenfeld) | 5 | V08,V09,V25,V26,V27,V49 |
| Correlation | 3 | V11,V42,V43 |
| Non-inferiority | 3 | V10,V28,V29 |
| Equivalence | 2 | V16,V30 |
| Cluster RCT | 2 | V15,V50 |
| McNemar | 2 | V13,V46 |
| Logistic regression | 1 | V12 |
| Repeated measures | 1 | V17 |
| Chi-square | 1 | V48 |
| Crossover 2x2 | 1 | V47 |

---

## Phase 10: Nice-to-Have Features (6-12 Months)
**Priority:** P2 | **Status:** `not_started`

### 10a. Reference Manager Integration
- Zotero, Mendeley, EndNote export of cited references
- RIS/BibTeX file generation from session citations

### 10b. IRB/Ethics Template Generation
- Auto-generate ethics application methodology sections
- Template library for common IRB formats

### 10c. Statistical Code Expansion
- Expand R/Python/STATA code coverage
- Validate generated code runs correctly
- Add SAS support

### 10d. ClinicalTrials.gov Integration
- Pre-populate NCT registration fields from designed methodology
- Export study record draft

---

## Implementation Sequence

```
Month 1-2:  Phase 1 (Auth) → Phase 3 (Export) → Phase 4 (Validation)
Month 2-3:  Phase 2 (Billing) → Phase 5 (Citations)
Month 3-4:  Phase 6 (Projects) → Phase 9 (Calculator Validation)
Month 4-6:  Phase 7 (Multi-Language) → Phase 8 (Collaboration)
Month 6-12: Phase 10 (Nice-to-Have features)
```

## Errors Encountered
| Error | Attempt | Resolution |
|-------|---------|------------|
| (none yet) | | |
