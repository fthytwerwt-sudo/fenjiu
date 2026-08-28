# Dual-Business Sales Playbooks Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver fact-gated, separately operable Sales-First execution and content playbooks for Fenjiu Nepal and Nepal seafood without enabling an external action.

**Architecture:** Keep existing Sales-First strategy files as the routing layer. Add two self-contained execution playbooks, two content playbooks, and two shared matrices; each links to the applicable evidence source while preserving `CONFIRMED / HYPOTHESIS / UNKNOWN / BLOCKED` distinctions.

**Tech Stack:** Markdown, existing project validation scripts, Git path-limited staging.

---

### Task 1: Create the fact boundary and execution skeletons

**Files:**
- Create: `docs/strategy/fenjiu/FENJIU_EXECUTION_PLAYBOOK.md`
- Create: `docs/strategy/seafood/SEAFOOD_EXECUTION_PLAYBOOK.md`
- Modify: `docs/project/BUSINESS_STATUS.md`, `docs/project/SOURCE_OF_TRUTH.md`

**Step 1:** State current stage, product/offer evidence required, supplier inputs, current blocks and `NOT NOW`.

**Step 2:** Define separate stages, entry/exit gates, primary/secondary routes, daily/weekly sales activity and human-led follow-up.

**Step 3:** Record the seafood manifest as a source-backed product-list input only; preserve missing cold-chain, price, inventory and compliance facts as `UNKNOWN` or `BLOCKED`.

**Step 4:** Verify every phase has one main result, a stop line, an owner and a next unlock.

### Task 2: Create the fact-gated content playbooks

**Files:**
- Create: `docs/strategy/fenjiu/FENJIU_CONTENT_PLAYBOOK.md`
- Create: `docs/strategy/seafood/SEAFOOD_CONTENT_PLAYBOOK.md`

**Step 1:** Define audiences, content pillars, channel roles, hooks, caption/CTA rules and the AI iPhone Natural Look visual bible.

**Step 2:** Add AI generation constraints that prohibit fake product labels, customers, venues, endorsements, local claims and regulated sales statements.

**Step 3:** Add 24 content cards per business line. The first 12 cards per line contain opening, full script, AI visual prompt/shot list, caption, CTA, proof needed, QC and sales metric.

**Step 4:** Mark every card `publish_blocked_pending_business_gates` until a fact/asset/policy/authorization lock is available.

### Task 3: Add shared gates, metrics and strategy navigation

**Files:**
- Create: `docs/strategy/DUAL_BUSINESS_LINE_STAGE_GATE_MATRIX.md`
- Create: `docs/strategy/DUAL_BUSINESS_LINE_KPI_SCORECARD.md`
- Modify: `docs/strategy/SALES_FIRST_MASTER_PLAN.md`, `docs/strategy/SALES_EXECUTION_PHASES.md`

**Step 1:** Add cross-line phase ordering, channel expansion conditions, manual-first AI/CRM/automation gates and `NOT NOW` controls.

**Step 2:** Add Output, Funnel and Decision metrics, minimal samples and recommended initial test thresholds. Do not label a proposed threshold as historical performance.

**Step 3:** Link the existing Sales-First strategy layer to the six new artifacts, without changing the current business readiness claim.

### Task 4: Update governance records and validate

**Files:**
- Modify: `docs/project/CURRENT_STATUS.md`, `docs/project/NEXT_ACTIONS.md`, `docs/project/OPEN_QUESTIONS.md`, `docs/project/RISKS_AND_BLOCKERS.md`, `docs/project/DECISIONS.md`, `docs/collaboration/EXECUTION_HISTORY.md`

**Step 1:** Record that an execution design and source register exist, not that either line has launched.

**Step 2:** Run `git diff --check`, mechanism validation, focused keyword/structure checks and the relevant regression suite.

**Step 3:** Conduct repository-hygiene, configuration-boundary and data-safety checks before path-limited staging.

**Step 4:** Commit with Lore trailers, push `main`, read back the remote commit and core files, then verify final Git status.
