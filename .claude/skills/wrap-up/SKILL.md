---
name: wrap-up
model: sonnet
description: Runs the session wrap-up — captures domain learnings, updates hypothesis tracking, and ensures knowledge persists across sessions. Invoked when Sam says "done", "wrap up", or "that's it for now". Also wired as the final step in weekly-review, process-backlog, and weekly-update.
allowed-tools: Read, Edit, Write, Bash
---

## Your Task

Run the session wrap-up for this product OS workspace. Takes 2-3 minutes. Ensures learnings persist.

Announce at start: **"Running wrap-up."**

---

## Step 1: Identify touched domains

Based on this session's work, identify which domains under `knowledge/domains/` were relevant. If unclear, infer from session context. List the domains identified before proceeding.

---

## Step 2: Hypothesis scan

For each touched domain, read `hypotheses.md`. For each non-retired hypothesis:

- **Confirming evidence this session?** → Increment `Confirmations` count, add inline dated note: `*(YYYY-MM-DD: [source/reason])*`
- **Contradicting evidence?** → Increment `Contradictions` count, add inline dated note
- **3+ confirmations?** → Surface to Sam: "H[N] in [domain] has 3 confirmations. Proposed move to `knowledge.md`: [draft text]. Approve?"

**Never auto-promote.** Sam approves all promotions.

---

## Step 3: New knowledge

Did this session surface new confirmed facts or rules not already in `knowledge.md`?

**Rule of thumb — fact vs hypothesis:** If it requires future validation to know if it's true, it's a hypothesis (goes to `hypotheses.md`). If it's already evidenced in this session — a decision was made, a number was stated, a process was confirmed — it's a fact (goes to `knowledge.md`).

- **New fact** → append under `## What we know (facts)` with `*(added YYYY-MM-DD)*` tag if time-sensitive
- **New confirmed rule** → append under `## Rules (apply by default)` with Confirmed by + Apply when
- **Cross-domain rule?** → Check if it belongs in `knowledge/domains/shared.md` instead

---

## Step 4: Corrections

Did Sam correct the agent on anything this session?

- **Agent behavior correction** → update relevant `AGENTS.md` (root or `knowledge/`) with the corrected behavior
- **Domain fact correction** → update the relevant `knowledge.md` entry
- **Fact about Sam** → update `knowledge/about-me/about-me.md`

---

## Step 5: Housekeeping

- Update `*Last updated: YYYY-MM-DD*` header on any modified files
- Flag (don't fix) any domain where `*Last updated:*` is older than 90 days: "Note: [domain]/knowledge.md last updated YYYY-MM-DD — may be worth a review"

---

## Output

End with a brief summary (1-3 bullets):
- What was updated
- Any hypothesis promotion candidates surfaced
- Any stale domains flagged

If nothing needed updating, say: "Wrap-up complete — nothing to capture this session."
