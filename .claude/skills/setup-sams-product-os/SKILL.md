---
name: setup-sams-product-os
description: Sets up or repairs the Sams Product OS workspace. Creates the knowledge folders, seeds starter files from templates, writes GOALS.md from a short interview, optionally installs QMD search and the recommended plugins, then verifies. Safe to re-run; it only fills gaps. Invoked via /setup-sams-product-os.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

## Your Task

Set up this product OS workspace, or repair a partial one. Flow: **look, ask, show the plan, confirm, write, verify.**

Announce at start: **"Running setup-sams-product-os."**

Rules for the whole run:
- **Never overwrite a file that exists.** Report it as skipped. The one exception is a file the user explicitly asks you to regenerate.
- **Never delete user content.** `.gitkeep` cleanup is the only deletion, and only with a yes.
- **Ask one question at a time.** Skip any question the workspace already answers.
- **Nothing is written before Step 3 is confirmed.**
- Paths below are relative to the repo root (`$CLAUDE_PROJECT_DIR`, or the directory holding `AGENTS.md`).

---

## Step 1: Look (read only)

Gather the current state. Run checks in parallel where you can.

**Tooling**
- `command -v claude`, `command -v npm`, `command -v qmd`
- If qmd exists: `qmd collection list` and look for `product-os`
- If claude exists: `claude plugin marketplace list` and `claude plugin list`, and look for `sams-product-plugins`, `write-doc`, `write-comms`. If a command fails, record "unknown" and move on.

**Folders.** Expected:
- `knowledge/` subfolders: `about-me`, `company-context`, `product-strategy`, `processes`, `product-analytics`, `references`, `voice-samples`, `decisions`, `people`, `opportunities`, `domains`
- `projects/`, `meetings/`, `tasks/_archived/`, `thinking/`, `_temp/`

**Seed files.** Each one is created from its template if missing:

| Target | Template |
|--------|----------|
| `knowledge/INDEX.md` | `templates/knowledge-index-template.md` |
| `knowledge/about-me/about-me.md` | `templates/about-me-template.md` |
| `knowledge/company-context/company-overview.md` | `templates/company-overview-template.md` |
| `knowledge/company-context/glossary.md` | `templates/glossary-template.md` |
| `GOALS.md` | `templates/goals-template.md` |
| `tasks/TASKS.md` | `templates/tasks-template.md` |

For each target that exists, note whether it is **still the raw template** (it still contains placeholder text such as `[Name]`, `YYYY-MM-DD`, or empty `**Current Role**:`). A raw template counts as unanswered for Step 2.

**Leftovers.** List `.gitkeep` files under `knowledge/`, `tasks/`, `meetings/`, `projects/`.

Report the findings as a short table: item, status (present / missing / raw template / unknown). If everything is present and filled in, say so and offer to stop or re-run only the optional steps (QMD, plugins).

---

## Step 2: Ask

One question per message. Give an example with each. Skip a question when Step 1 already answers it.

1. **Role.** "What's your current role?" (e.g. Senior PM, Founder, VP Product). Skip if `about-me.md` has a filled `**Current Role**:`.
2. **Focus.** "What's your main professional focus this quarter?" (e.g. launching a new product, hitting activation OKRs). Skip if `about-me.md` has a filled `**This Quarter's Focus**:`.
3. **Goals.** "What are your 2 to 4 goals this quarter? A line each is fine." Skip if `GOALS.md` exists and is not a raw template. For each goal, ask nothing more: fill what you can and leave the rest blank for the user.
4. **Glossary (optional).** "Any codenames, acronyms, or internal terms you use daily? Give me 3 to 5 with a short meaning, or say skip." Skip if `glossary.md` already has rows.
5. **QMD.** Only if npm exists and qmd or its collection is missing: "Install QMD semantic search? It speeds up context lookup. The agent falls back to Grep without it." Default yes. If yes, also ask: "Generate embeddings now? Takes a few minutes on a large knowledge base." Default no.
6. **Plugins.** Only if claude exists and the marketplace or the two skills are missing: "Install the Sams Product Plugins marketplace plus `write-doc` and `write-comms`? `weekly-review` uses `write-comms` for the Friday update." Default yes.
7. **Cleanup.** Only if `.gitkeep` files were found under data folders: "Remove the `.gitkeep` placeholders? They're only there so git keeps empty folders." Default yes.

---

## Step 3: Show the plan

Show one list of exactly what will happen, grouped:
- **Create** (folders and files)
- **Fill** (which fields in `about-me.md`, `GOALS.md`, `glossary.md` get the user's answers, with the drafted text)
- **Install** (QMD, plugins, with the commands)
- **Remove** (`.gitkeep` files)
- **Skip** (what already exists)

Ask: "Go ahead?" Apply any edits the user asks for, then proceed only on a yes.

---

## Step 4: Write

Do the work in this order. Report each item as done, skipped, or failed. A failure does not stop the run.

1. **Folders.** `mkdir -p` each missing folder from Step 1.
2. **Seed files.** Copy each missing target from its template. Then:
   - If the copy has a `Save to \`...\`` line, remove it and the `---` under it, since the file is now in place.
   - Replace `YYYY-MM-DD` in `Last updated` lines with today's date.
3. **Fill answers.**
   - `about-me.md`: set `**Current Role**:` and the first item under `**This Quarter's Focus**:`. Edit those lines only.
   - `GOALS.md`: one `### Goal N: [Name]` section per goal, following the template's shape. Put the user's line in the name and description. Delete unused goal sections. Leave other fields blank.
   - `glossary.md`: one table row per term. Leave the placeholder row only if no terms were given.
   - Never invent content the user didn't give.
4. **QMD** (if approved):
   - `npm install -g @tobilu/qmd` if qmd is missing
   - `qmd skill install --global --yes`
   - `qmd collection add "<repo root>" --name product-os`, then `qmd context add qmd://product-os "Personal PM operating system: tasks, projects, knowledge base, meetings, and references"`
   - `qmd embed` only if the user said yes to embeddings
5. **Plugins** (if approved):
   - `claude plugin marketplace add samkawsarani/sams-product-plugins`
   - `claude plugin install write-doc@sams-product-plugins` and `claude plugin install write-comms@sams-product-plugins`
   - If the marketplace route fails: `npx skills add samkawsarani/sams-product-plugins --skill write-doc write-comms --yes --global`
   - On failure, print the manual command and continue.
6. **Cleanup** (if approved): delete the listed `.gitkeep` files. Nothing else.

---

## Step 5: Verify

Re-run the Step 1 checks and print a pass/fail table:
- claude CLI (required), npm (optional), qmd (optional)
- every expected folder
- every seed file
- `.claude/skills/` present

For any failure, give the one command or action that fixes it.

---

## Step 6: Next steps

Keep it short:
1. Fill in `knowledge/about-me/about-me.md` and `knowledge/company-context/company-overview.md` (15 to 20 minutes, biggest payoff).
2. Brain dump into `tasks/TASKS.md`.
3. Run `/start-my-day` each morning and `/weekly-review` on Friday to promote backlog items into `## Active`.
4. Add writing samples to `knowledge/voice-samples/` when you want drafts in your voice.
5. **Back up your data.** Everything personal (`knowledge/`, `tasks/`, `projects/`, `meetings/`, `thinking/`, `GOALS.md`, `VOICE-GUIDE.md`) is gitignored, so git does not save it. Use Time Machine, or whatever backup you already run.

Re-run `/setup-sams-product-os` any time; it only fills gaps.

Skip wrap-up for this skill. Setup creates no domain knowledge.
