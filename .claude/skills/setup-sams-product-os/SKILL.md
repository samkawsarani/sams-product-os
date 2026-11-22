---
name: setup-sams-product-os
description: Sets up or repairs the Sams Product OS workspace. Creates the knowledge folders, seeds starter files from templates, writes GOALS.md from a short interview, records which work tools the user has (email, calendar, messaging, tracking, meeting notes, metrics, CRM, call recordings, docs) and how the agent reaches each, optionally installs QMD search and the recommended skills, then verifies. Safe to re-run; it only fills gaps. Invoked via /setup-sams-product-os.
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Glob, Grep, Bash(qmd:*), Bash(npx skills:*), Bash(command -v:*), Bash(mkdir -p:*)
---

## Your Task

Set up this product OS workspace, or repair a partial one. Flow: **look, ask, show the plan, confirm, write, verify.**

Announce at start: **"Running setup-sams-product-os."**

Rules for the whole run:
- **Never overwrite a file that exists.** Report it as skipped. The one exception is a file the user explicitly asks you to regenerate.
- **Never delete user content.** `.gitkeep` cleanup is the only deletion, and only with a yes.
- **Ask one question at a time.** Skip any question the workspace already answers.
- **Nothing is written before Step 3 is confirmed.**
- Paths below are relative to the repo root (the directory holding `AGENTS.md`).
- **Work with any agent.** Use what you can see in this session (your own tools, MCP servers, skills) rather than an agent-specific command. Where a command needs the agent's name, use your own `skills` agent id (e.g. `claude-code`, `codex`, `cursor`).
- **Every `npx skills add` installs globally and links into your agent's skills folder:** always `--global --agent <your agent id> --yes`, never `--copy`.
- **Never install or log in to a work tool.** Setup records tools and installs skills. Tool accounts, API projects, and logins are the user's to set up.

---

## Step 1: Look (read only)

Gather the current state. Run checks in parallel where you can.

**Tooling**
- `command -v npm`, `command -v qmd`
- If qmd exists: `qmd collection list` and look for `product-os`
- Skills: check your own skills list for `write-doc` and `write-comms`. If you cannot see a skills list, record "unknown".

**Work tools.** Read `references/tool-categories.md`, then:
- List the MCP servers and tools available to you in this session. Match each against the **Detection** table. Names alone are enough; you do not need to load a tool's full definition.
- Run `command -v` for each command in the **Command-line tools** table.
- For each detected tool that has a template (see **Templates** in `references/tool-categories.md`), run the checks in the template's **Setup** section: its requirements, its ready check, and whether its skills are in your skills list. Run nothing for a template the scan did not detect.
- Note whether `meetings/` holds any notes.
- If `knowledge/company-context/tools/INDEX.md` exists, read it. A category already listed there counts as answered.

Record one detected tool (or none) per category, with how it was found.

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

Report the findings as a short table: item, status (present / missing / raw template / unknown). Add a second table for work tools: category, detected tool, how found (MCP server name, command, folder, or none). If everything is present and filled in, say so and offer to stop or re-run only the optional steps (QMD, skills, tools).

---

## Step 2: Ask

One question per message. Give an example with each. Skip a question when Step 1 already answers it.

1. **Role.** "What's your current role?" (e.g. Senior PM, Founder, VP Product). Skip if `about-me.md` has a filled `**Current Role**:`.
2. **Focus.** "What's your main professional focus this quarter?" (e.g. launching a new product, hitting activation OKRs). Skip if `about-me.md` has a filled `**This Quarter's Focus**:`.
3. **Goals.** "What are your 2 to 4 goals this quarter? A line each is fine." Skip if `GOALS.md` exists and is not a raw template. For each goal, ask nothing more: fill what you can and leave the rest blank for the user.
4. **Glossary (optional).** "Any codenames, acronyms, or internal terms you use daily? Give me 3 to 5 with a short meaning, or say skip." Skip if `glossary.md` already has rows.
5. **Work tools.** One category per message, in the order of the categories table in `references/tool-categories.md`. Skip a category already in `INDEX.md` unless its status is `not ready`; for those, only re-run the template's **Setup** checks or the Step 5 verify call.
   - **Detected:** "Found Linear (MCP server `linear-server`) for work tracking. Correct?" A yes moves on.
   - **Not detected:** "Where do you track initiatives and projects? Linear, Jira, Asana, something else (describe it), or skip." Use the category's common answers.
   - **Something else:** ask how the agent reaches it (an MCP server, a command-line tool, a folder, or not at all), then one question: "How do you use it for <the category's needs>?" Keep the answer as written.
   - For every confirmed tool, ask only for **Scope** blanks the tool needs and the scan did not answer (Slack channels that matter, a Jira project key). Skip if the user says skip.
   - **Meeting notes:** also ask where finished notes land (e.g. synced into `meetings/`).
   - **Picked a tool with a template:** read the template's **Setup** section and run its checks if Step 1 did not. Report each requirement as met or missing. For anything under **User does** that is not done, say what it is and that the user sets it up themselves, and record the tool as not ready until then. If the template lists **Skills to offer** and any are missing, ask: "Install the skills <tool> needs?" Default yes.
6. **QMD.** Only if npm exists and qmd or its collection is missing: "Install QMD semantic search? It speeds up context lookup. The agent falls back to Grep without it." Default yes. If yes, also ask: "Generate embeddings now? Takes a few minutes on a large knowledge base." Default no.
7. **Skills.** Only if `write-doc` or `write-comms` is missing or unknown: "Install `write-doc` and `write-comms` from Sams Product Plugins? `weekly-review` uses `write-comms` for the Friday update." Default yes.
8. **Cleanup.** Only if `.gitkeep` files were found under data folders: "Remove the `.gitkeep` placeholders? They're only there so git keeps empty folders." Default yes.

---

## Step 3: Show the plan

Show one list of exactly what will happen, grouped:
- **Create** (folders and files)
- **Fill** (which fields in `about-me.md`, `GOALS.md`, `glossary.md` get the user's answers, with the drafted text)
- **Tools** (one line per category: tool, access, status, file to write)
- **Install** (QMD, skills, with the commands)
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
4. **Work tools.** `mkdir -p knowledge/company-context/tools`. For each answered category:
   - **Template exists** (see **Templates** in `references/tool-categories.md`): copy it to `knowledge/company-context/tools/<category file>`, remove the template paragraph and the `## Setup` section, fill every `<...>` blank from Step 1 and Step 2, and set **Status**. A blank you cannot fill becomes `ask the user` with the question, never a guess.
   - **No template:** write the file in the **User file shape**. One `###` heading per need for the category. For an MCP tool, name the server and the tool that meets each need when the name makes it plain; otherwise write what the user said. A need nobody answered is `not supported`.
   - **Skipped:** write nothing.
   - Never overwrite an existing category file. The one change allowed is its **Status** line, set from this run's checks, so a re-run can flip `not ready` to `ready`. Report anything else about it as skipped.
   - Then write `knowledge/company-context/tools/INDEX.md`, one row per category, skipped ones included:

     ```markdown
     # Tools

     Which work tools this workspace uses and how the agent reaches them. Skills read the category file before using a tool.

     *Last updated: YYYY-MM-DD*

     | Category | Tool | Access | Status | File |
     |----------|------|--------|--------|------|
     | Email + calendar | <tool> | <MCP server, command, or folder> | ready | `email-calendar.md` |
     | CRM | none | | skipped | |
     ```

     If `INDEX.md` exists, add missing rows and update rows for files written this run. Leave other rows alone.
5. **Tool skills** (if approved): run each template's **Skills to offer** command, with `--global --agent <your agent id> --yes`. Then set that tool file's **Status** from the result.
6. **QMD** (if approved):
   - `npm install -g @tobilu/qmd` if qmd is missing
   - `qmd skill install --global --yes`
   - `qmd collection add "<repo root>" --name product-os`, then `qmd context add qmd://product-os "Personal PM operating system: tasks, projects, knowledge base, meetings, and references"`
   - `qmd embed` only if the user said yes to embeddings
7. **Skills** (if approved): `npx skills add samkawsarani/sams-product-plugins --skill write-doc write-comms --global --agent <your agent id> --yes`. On failure, print the command and continue.
8. **Cleanup** (if approved): delete the listed `.gitkeep` files. Nothing else.

---

## Step 5: Verify

Re-run the Step 1 checks and print a pass/fail table:
- npm (optional), qmd (optional)
- every expected folder
- every seed file
- `.claude/skills/` present
- every category file listed in `INDEX.md`, plus one cheap read-only call per ready tool: the template's **Ready check** when it has one, otherwise the smallest list call the MCP tool offers (one item). A failed call sets that file's **Status** to `not ready (<error>)` and updates `INDEX.md`
- each installed skill appears in your skills list (it may need a new session to show up; say so rather than failing it)

For any failure, give the one command or action that fixes it.

---

## Step 6: Next steps

Keep it short:
1. Fill in `knowledge/about-me/about-me.md` and `knowledge/company-context/company-overview.md` (15 to 20 minutes, biggest payoff).
2. Brain dump into `tasks/TASKS.md`.
3. Any tool marked not ready: finish the steps its status names, then re-run `/setup-sams-product-os` to flip it to ready. Edit files in `knowledge/company-context/tools/` directly any time.
4. Run `/start-my-day` each morning and `/weekly-review` on Friday to promote backlog items into `## Active`.
5. Add writing samples to `knowledge/voice-samples/` when you want drafts in your voice.
6. **Back up your data.** Everything personal (`knowledge/`, `tasks/`, `projects/`, `meetings/`, `thinking/`, `GOALS.md`, `VOICE-GUIDE.md`) is gitignored, so git does not save it. Use Time Machine, or whatever backup you already run.

Re-run `/setup-sams-product-os` any time; it only fills gaps.

Skip wrap-up for this skill. Setup creates no domain knowledge.
