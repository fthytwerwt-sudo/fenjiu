# Seafood Online Acquisition Workstream Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the seafood user's local-sales responsibility with a fact-gated online acquisition workstream connected to a separate supplier sales/fulfilment workstream through explicit lead handoff and outcome feedback contracts.

**Architecture:** Keep the existing seafood product register and content assets, but supersede the old SF-2 route. Use the seafood execution playbook as the dual-workstream router, a new online-acquisition playbook as the user's daily operating manual, and a new lead-handoff contract as the interface between acquisition and local sales.

**Tech Stack:** Markdown, existing Python sync-pack script, existing project validation and regression commands.

---

### Task 1: Replace the conflicting seafood route

**Files:**
- Modify: `docs/strategy/seafood/SEAFOOD_EXECUTION_PLAYBOOK.md`

**Steps:**
1. Preserve the product-candidate register and business-gate warnings.
2. Mark the old `SF-2 B2B Manual Procurement Loop` as `SUPERSEDED`.
3. Add `SF-S1 Supplier Product & Fulfilment Readiness` and `SF-U0`–`SF-U8` routing.
4. Add responsibility matrix, funnel, handoff/feedback connection and current-stage statement.
5. Run the role-conflict search and verify no current user-local-sales wording remains.

### Task 2: Create the user's acquisition operating manual

**Files:**
- Create: `docs/strategy/seafood/SEAFOOD_ONLINE_ACQUISITION_PLAYBOOK.md`

**Steps:**
1. Add implementation-design fields and current-stage daily action.
2. Add ICP evaluation and explicit First ICP decision.
3. Add Route A–E matrix and explicit Primary/Fallback/Later decision.
4. Define SF-U0–U8 with Goal, Entry, User Action, Supplier Dependency, Output/Funnel/Decision Metric, Initial Threshold, Stop, NOT NOW, Done and Next Unlock.
5. Add daily/weekly operating modes, cost metrics, crawler role and A/B route rules.

### Task 3: Create the acquisition-to-supplier interface

**Files:**
- Create: `docs/strategy/seafood/SEAFOOD_LEAD_HANDOFF_CONTRACT.md`

**Steps:**
1. Define Lead, Qualified Lead and Supplier Accepted Lead.
2. Add a minimal, privacy-safe handoff schema and supplier decision states.
3. Add supplier outcome feedback schema, feedback timing hypotheses and lost reasons.
4. Add `attribution_incomplete` handling and no-PII-in-Git rules.

### Task 4: Reposition content and shared scorecards

**Files:**
- Modify: `docs/strategy/seafood/SEAFOOD_CONTENT_PLAYBOOK.md`
- Modify: `docs/strategy/DUAL_BUSINESS_LINE_STAGE_GATE_MATRIX.md`
- Modify: `docs/strategy/DUAL_BUSINESS_LINE_KPI_SCORECARD.md`

**Steps:**
1. Keep hooks, content cards, AI phone-look and QC rules.
2. Change content from a required first route to one candidate acquisition route selected at SF-U2/U6.
3. Extend content attribution through qualified lead, supplier accepted, offered and won/lost.
4. Replace only seafood sections in shared matrices; assert Fenjiu sections are unchanged.

### Task 5: Sync project facts and handoff package

**Files:**
- Modify: `PROJECT_ENTRY.md`
- Modify: `docs/project/PROJECT_GOAL.md`
- Modify: `docs/project/BUSINESS_STATUS.md`
- Modify: `docs/project/CURRENT_STATUS.md`
- Modify: `docs/project/SOURCE_OF_TRUTH.md`
- Modify: `docs/project/SCOPE_AND_BOUNDARIES.md`
- Modify: `docs/project/DECISIONS.md`
- Modify: `docs/project/NEXT_ACTIONS.md`
- Modify: `docs/project/OPEN_QUESTIONS.md`
- Modify: `docs/project/RISKS_AND_BLOCKERS.md`
- Modify: `docs/collaboration/COLLABORATION_STATUS.md`
- Modify: `docs/collaboration/EXECUTION_HISTORY.md`
- Modify: `scripts/build_project_sync_pack.py`
- Regenerate: `project_sync/latest/` and `project_sync/PROJECT_SYNC_MANIFEST.json`

**Steps:**
1. Land P0 as a seafood-only responsibility fact; keep Fenjiu route unchanged.
2. Add the two new files to the strict sync allowlist.
3. Build and verify the handoff package.

### Task 6: Verify, review and complete Git closure

**Steps:**
1. Run role-conflict, business-line, stage, acquisition, handoff, content, link, sensitive-data and local-path checks.
2. Run GPT Project mechanism validation, sync-pack build/verify and `make regression`.
3. Request independent read-only review; fix all high/medium findings and re-review.
4. Path-limit stage; create Lore commit; push `main`; fetch and read back remote core files.
5. Report external/business unknowns separately from planning/Git completion.
