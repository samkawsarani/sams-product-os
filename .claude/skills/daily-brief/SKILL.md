---
name: daily-brief
model: sonnet
description: Writes the dated morning briefing as an HTML page, combining calendar agenda, focus-time protection check, email and Slack triage with an inbox hygiene pass, meeting prep, Linear initiative movement, comms owed, and active task priorities. Scheduled headless on weekdays via launchd; also runs on demand. Invoked via /daily-brief or "daily brief", "write my brief", "regenerate my brief". For the lighter terminal briefing or the week overview, use start-my-day instead.
---

# Daily Brief

Gathers the morning briefing and writes it to `thinking/daily-briefs/daily-brief-YYYY-MM-DD.html`,
one dated file per run. **That page is the only output.**

The tab the user keeps open is `thinking/daily-briefs/index.html`: a sidebar of every retained
date beside a frame showing one brief, newest on load. `build-brief.py` regenerates it every run,
so a reload lands on today. The briefs are a log, kept 30 days and then pruned. Read
`thinking/AGENTS.md` once before writing there.

There is one mode. Every invocation runs the full gather. A second run the same day overwrites
that day's file rather than adding one. Nothing is cached, nothing is refreshed in place, and
nothing is printed to the terminal but a one-line confirmation. Scheduled runs and manual runs do
exactly the same thing.

**The gather writes in exactly two places:** Step 3's inbox hygiene pass (marks read and archives
meeting-invite receipts) and Step 6a's effort tags in `tasks/TASKS.md`. Nothing else mutates
anything, and hygiene never trashes or deletes. `BRIEFING_NO_MUTATE=1` makes hygiene read-only.

**Relationship to `start-my-day`:** that skill is the interactive terminal briefing and owns the
week overview. This one is the scheduled page. They cover the same ground; pick one per morning.

## Requirements

- **macOS only** for scheduling: `run.sh` installs a launchd agent. The skill itself runs anywhere
  a manual `/daily-brief` does.
- `python3` (standard library only) for the scripts.
- The `gws` CLI, authenticated, for Calendar and Gmail.
- Optional: a Slack MCP and a Linear MCP. A source that is not connected emits its section as
  unavailable, quoting the error; the brief still writes.

## Context

Today's date: $TODAY

## Scheduling

The 8:30am run is a `claude -p` invocation of this skill, wrapped by `scripts/run.sh` so the
headless session gets a login PATH, the repo as its working directory, pre-approved tools, and
a log:

```bash
.claude/skills/daily-brief/scripts/run.sh              # run it now
.claude/skills/daily-brief/scripts/run.sh --install    # schedule it, 8:30am Mon-Fri
.claude/skills/daily-brief/scripts/run.sh --uninstall
```

**Weekdays only.** The plist carries five `StartCalendarInterval` entries, one per weekday, so
nothing fires on a Saturday or Sunday. A manual weekend run still works and behaves identically.
Change `HOUR` and `MINUTE` at the top of `run.sh` to move it, then re-run `--install`.

`--install` generates its launchd plist from the script's own location, so a clone in another
directory installs correctly and no path is duplicated. It is idempotent. Do not check a plist
into the repo. Logs go to `~/Library/Logs/com.<user>.daily-brief/`, kept 14 days.

A headless run cannot answer a permission prompt, so every tool the gather needs is pre-allowed
in `run.sh`. The default grants `mcp__linear-server` and `mcp__slack` (the server names in
`.mcp.json.example`) plus the built-in file and shell tools. If your MCP servers are named
differently, set `BRIEFING_ALLOWED_TOOLS` to the full space-separated list. If a section comes back
`<unavailable>` at 8:30am but works by hand, that list is where to look first.

The calendar goes stale over the day; that is accepted. This is a morning briefing, not a live
dashboard. For the afternoon view, run the skill again.

---

## The Gather

Steps 0-10. Every run does all of them. A step that fails still emits its section, saying so.

### Saying a source is unavailable

`<unavailable: reason>` is a report of something that happened, not a guess about what might.
Write it **only after a call actually failed**, and quote the error you got. Never infer that a
tool is ungranted, a server is down, or a permission is missing without having tried: a run that
reports "denied" when the tool was there produces a blank section and sends you looking in the
wrong place. If you have not called it, you do not know.

### The window

`scripts/briefing-window.py` returns the span since the last brief as JSON (`since_iso`,
`since_human`, `first_run_of_week`, and more). Steps 7 and 8 use it. **Never do the date math
yourself.**

It reads the newest brief dated **before** today, never today's own file, because today's file is
the one this run is about to overwrite. That makes a brief reproducible: a 2pm re-run of a Monday
gets the same window as the 8:30am run did, so it rebuilds the same page rather than a thinner
one. **Never reintroduce a window that narrows on a second run.** Counting today's file made a
Monday re-run silently drop everything that happened over the weekend.

`first_run_of_week` is true when no brief dated before today exists on or after this week's
Monday, which is **not** the same as "today is Monday": a stat holiday, a sick day, or a week that
starts with a manual Saturday run all still get exactly one week-opening run. Nothing in the
default gather branches on it; it is the hook for any week-opening section you add (a prior-week
metrics block, say), together with `last_week`. Never test the weekday yourself.

### Step 0: Refresh Index

If qmd is installed, run `qmd update && qmd embed`. If qmd is unavailable, skip and note it.

### Steps 1–2: Calendar Agenda and Focus Check → `calendar`

```bash
.claude/skills/daily-brief/scripts/calendar-focus.py --html
```

`--html` emits the exact `<section>` block the fragment wants. Paste it verbatim.
**Do not recompute or restyle any of it.** (Without the flag it prints the same content as plain
text, which is there for checking the script by hand, not for the brief.)
The script owns every calendar rule: the declined-attendee filter, all-day exclusion, optional
markers, real-overlap detection, free blocks, back-to-back density, focus counting, and the fix
proposals. It fetches via `gws` itself, so there is no separate calendar call to make.

Behaviour worth knowing:

- **The table is meetings only.** No focus blocks, no lunch or school runs, no all-day markers
  like `Home` or `OOO`. The user has their calendar open already; a second copy of it is noise,
  and they put those entries there themselves. They are excluded from the *list*, not from the
  day: they still count as busy for every free block, gap, and back-to-back calculation, and focus
  blocks are reported in the Focus column beside it. Do not add them back.
- **Labeled focus is not protected focus.** Output reads `0h actually protected (2h labeled,
  2 booked over)` when meetings sit on the blocks. Never restate the labeled number as if it were
  secured time.
- Lunch and personal events do not *count as* focus, but they do occupy the day, so they never
  show up inside a free block or a focus gap.
- Focus-block conflicts appear only in the Focus column. Real meeting-vs-meeting overlaps appear
  under Meetings, and only when both are non-optional real meetings.
- On failure it prints `<unavailable: reason>` (in whichever form was asked for) and exits
  non-zero. Pass that through; do not fall back to hand-rolling the section.
- **Everything is computed from now forward.** Read at 1:50pm you get the rest of the day:
  the table shows only what is left, with `Earlier today: N meetings through 1:30pm` as a note,
  and Focus counts only remaining time. It never proposes moving a block whose hour has passed.
  Run at 8:30am nothing has elapsed, so the output is the whole workday.
- A focus block already underway counts only its remaining minutes: at 3:30pm a 3–4:30 block
  is `1h labeled`, not `1h30m`.
- `--date YYYY-MM-DD`, `--json FILE`, and `--now HH:MM` exist for testing; `--now none` disables
  the cutoff. A `--date` other than today applies no cutoff.
- Workday (9am–5pm), the 2h daily focus target, and the personal-event keywords are constants at
  the top of the script. Edit them there, not here.

The script proposes fixes but never writes to the calendar, and neither does a run. The
proposals go into the page as proposals. The user approves them by asking, in a normal session.

### Steps 3-4: Gmail and Slack Triage → `inbox`

Both channels answer one question, "who needs a reply", so they share one section: an `Email`
column and a `Slack` column, side by side. See `references/brief-html.md` for the `split` markup.

#### Email

**Hygiene runs first.** Meeting-invite receipts with nothing to answer get cleared before the
triage query, so the column never shows what was just swept. This is the only mailbox write in the
gather. Follow `references/inbox-hygiene.md` for the selection query, the `batchModify` calls,
the safety envelope, and the audit line that closes the column. Run it before step 1 below, and
never let a hygiene failure stop the triage.

0. **Addressed to the user only.** Mail that reached them through a group alias or distribution
   list (`product@`, `eng-all@`, `everyone@`, any team alias) is broadcast, not a request, and is
   noise in the brief. Only surface mail where the user is in `To:` or `Cc:` by their own address.
   Enforce it in the query with `(to:me OR cc:me)` - a list alias delivers to the alias, so `to:me`
   does not match it, which is exactly the cut we want. Do **not** use `deliveredto:` and do not
   widen this to `is:unread` alone.
   The one exception: a thread the user is already on (they have replied in it) stays even if
   list-addressed.
1. Surface unread email needing a reply, time-sensitive items, emails from key people, action
   items, meeting threads.
2. Ignore newsletters, automated notifications, FYI-only, read-only updates.
3. **Exclude tool notifications** (Linear, Figma, GitHub, Notion, Slack digests, etc.) **unless
   the user is directly tagged** - then surface it.
4. **Kept meeting invites are calendar changes, not mail.** Hygiene archives the invite receipts
   and keeps the ones that need an answer - a proposed new time, an update or cancellation on a
   future event. Render those as their own line in the column, not as inbox items. See the
   reference.
5. **For emails with metrics/data**, extract key numbers inline rather than just listing the
   subject.
6. Cap at 5 most actionable if >10 unread.
7. **Close the column with the hygiene audit line**, always, even when every count was zero.

**Always fill the Email column**, even when nothing needs a reply. An omitted column cannot be
told apart from a broken Gmail call, and "nothing needs you" is worth knowing. When clear, one
line naming what was looked at: `2 unread addressed to you, neither needs a reply (a digest,
a Linear notification).` Say "addressed to you" so a quiet column is not mistaken for a broken
call: list traffic was filtered out by design, not missed. The hygiene audit line then says what
was swept, so a quiet column and a cleared one are also told apart.

#### Slack

0. **Directed at the user only.** Channel chatter the user merely has access to is noise.
   Something qualifies on exactly three grounds: (a) a DM or group DM, (b) an explicit `@` mention
   of the user (or a group they are in, like `@product`, where the message asks for something),
   (c) a thread the user has already posted in and someone replied after them. Everything else in
   a channel is skipped, however interesting — including channel-wide `@here`/`@channel`
   broadcasts that name no action for them.
1. Within those three, surface unanswered DMs, mentions not yet replied to, and thread replies
   awaiting them.
2. Needs-response only — not just reading. Cap at 5.

**Always fill the Slack column**, for the same reason. When clear, name the scope so the filter is
visible: `DMs, mentions, and your own threads clear across 6 channels.`

The whole `inbox` section is therefore always present: two columns, each carrying either what
needs a reply or an all-clear.

### Step 5: Meeting Prep → `meeting-prep`

1. For each meeting on today's calendar, check:
   - Is there an agenda or prep doc? Search `projects/` and `meetings/` by event name.
   - Is a decision or output expected from this meeting?
   - Are there open tasks in `TASKS.md` directly tied to this meeting's topic?
2. Flag meetings that look under-prepped (no agenda, decision-heavy, involves key stakeholders).
3. For flagged meetings, offer a one-line prep suggestion.

Omit the section if there are no meetings or all look prepared.

### Step 6a: Tag Untriaged Tasks (write-back)

The user dumps tasks as plain text and rarely types tags. This step assigns them so the
block-debt number in Step 6 is believable.

Every checkbox item in `## Active` and `## Backlog` carries one effort tag:

| Tag | Meaning |
|-----|---------|
| `#block` | Needs the user alone at a desk for 60min+ |
| `#meeting` | Closes inside a meeting already on the calendar |
| `#quick` | Under an hour, fits any gap |

For each **untagged** item, classify it and write the tag back into `tasks/TASKS.md`,
immediately after the `- [ ] ` and before the item text.

Use the calendar already gathered in Steps 1-2. An item naming people who appear on a meeting
today or this week is `#meeting`, not `#block` — that is a lookup, not a guess.

**Hard rules on the write-back. This edits the user's own notes, so it is append-only:**
- Insert the tag. Never edit, reword, reorder, split, merge, or delete their prose.
- Never overwrite or change a tag already present. A tag the user typed wins permanently.
- Low confidence leaves the item untagged. Untagged is a legal state.
- Never tag anything under `## Parking Lot`. That section is deliberately untriaged.
- Never tick or untick a checkbox.

Report the count of items left untagged; Step 6 surfaces it.

### Step 6: Active Task Priorities → `today`, `up-next`, `waiting-on`

Count the checkboxes in the `## Active` section only (Backlog is an inbox, not work in flight,
so folding it in makes the ratio meaningless) and put the tally in the `<span class="sub">` of
the `today` section:

```
Active 5 of 14 done · In Progress 2/5 · Up Next 3/9 · Waiting On 3, oldest 21d (Design)
2 #block open · 1 block on calendar · 2 untriaged
```

The second line is the **block debt** and it is the number that predicts the week. Count open
(unticked) `#block` items in `## Active` against the real focus blocks on today's calendar from
Steps 1-2. When `#block` items outnumber blocks, say so plainly in `today`: those are the items
that will not move, and they are the ones that slip for weeks. Omit the `untriaged` clause when
Step 6a left nothing untagged.

Waiting On ages come from the `Since` column of that table against today.

**Do not mirror the checkbox list into the brief.** `TASKS.md` is edited directly, so a read-only
copy of `In Progress` / `Up Next` / `Backlog` in the page would be a second source of truth that
goes stale. Those sections carry the *interpretation*: `today` is the three things that matter and
why, `up-next` is prose about what is queued and what is blocking it. Never the raw checkboxes,
never the backlog contents.

The backlog gets exactly one line in `up-next` and no more: `Backlog 4 · 2 #block`. It is an
inbox, not work in flight. `weekly-review` is where it gets decided, not here.

`waiting-on` is the one exception and it is a table, because each row gains an age and a next
step that `TASKS.md` does not carry. Badge an age past 14 days with `<span class="b bad">`.

1. Read `tasks/TASKS.md`
2. Extract:
   - Items in the **In Progress** section
   - Items in the **Up Next** section
   - Any items in the **Waiting On** table that look overdue (based on the "Since" date vs. today)
3. Read `GOALS.md` for goal alignment context

### Step 7: Linear Initiative Movement → `initiatives`

What moved on the core initiatives since the last briefing. **Only work that belongs to a Linear
initiative** — a project with an empty `initiatives` array is out of scope regardless of activity.
Skip the section silently if no Linear MCP is connected and none is configured; if one is
configured and the call fails, say so.

Follow `references/linear-initiatives.md` for the window, the scope tiers, the queries, and the
roll-up rules.

Key points:

- Initiatives the user owns and has not Completed get full detail; other owners' Active
  initiatives collapse to one line each and only when something moved.
- Issue movement can be large, so query `state="completed"` and `state="started"` separately and
  **paginate both**.
- `health` is not a valid field on `list_projects`. Requesting it errors.
- **Request `url`** on `list_initiatives`, `list_projects`, and `list_issues`, and link every
  named initiative, project, and issue on its name. It comes back only when asked for.
- `diffMarkdown` on status updates is pre-written exec-language movement. Quote it, don't
  paraphrase.
- Use `since_iso` from the window for Linear filters; `iso_duration` rounds up to whole days and
  over-covers rather than missing items.

### Step 8: Follow-Ups and Comms Owed → `you-owe`

What the user owes other people, which is not the same as what needs a reply today. Four sources
merged into one ranked list: status-update debt on initiatives they own, commitments recorded in
`meetings/` notes inside the window, Linear threads awaiting their reply, and `Waiting On`
inverted.

Follow `references/comms-owed.md` for the sources, the overdue thresholds, and the ranking.
Use the same window from `briefing-window.py`; do not recompute dates.

Overdue threshold is 14 days, tightened to 7 when an initiative is at-risk or its target date is
inside 30 days. **An initiative with no status update ever posted is the strongest signal in this
section** — report it as "never posted", never as an empty or zero value.

**Never name who is owed unless the note you read says so.** When attribution is unclear, write
the commitment and the meeting and drop the name.

Link each initiative on its name (the `url` from Step 7) and each commitment on its meeting note.
This is the section the user acts on, so the jump has to be one click.

### Step 9: Synthesize → `today`

Combine every section into a unified briefing.

**Omit any section that would be empty — don't show headers or placeholder text for empty
sections.** `inbox` is the exception: it always renders.

See `references/brief-html.md` for the full output structure and section examples.

`today` is the conclusion the sections above it argue for. Write it last, from everything the
other steps found, and place it at position 5 (see the order table in `references/brief-html.md`):
after the day's shape, the reply queues, and what moved, and before the queues the user acts from.

- Be opinionated. A recommended sequence, interleaving task work, replies, and meeting prep.
  Three items, not everything.
- Pull anything urgent into it: an at-risk initiative overdue a status update, a commitment due
  today, a meeting that needs prep before it starts.
- **But never rely on `today` alone to carry a flag.** It sits below four other sections, and a
  rushed morning ends before it. Anything urgent must also be badged red where it was found, in
  its own section. `today` synthesizes; it is not the only place a problem appears.

### Step 10: Write

Write `thinking/daily-briefs/daily-brief-YYYY-MM-DD.html`. One dated file per day, gitignored,
pruned after 30 days.

**Run `.claude/skills/daily-brief/scripts/briefing-window.py` BEFORE writing** — it reads the
newest existing brief dated *before* today, which is the window source for Steps 7 and 8. Run it
before writing anyway: that is the order the script documents, and nothing downstream should
depend on when today's file appeared.

**The brief is HTML, generated directly — there is no markdown step.** Write a fragment of
`<section>` elements to a temp file, then:

```bash
.claude/skills/daily-brief/scripts/build-brief.py --content /tmp/brief-content.html
```

No path argument. The script derives `thinking/daily-briefs/daily-brief-<today>.html` from its own
location, so the working directory does not matter. It owns the page chrome, the `<title>`, the
timestamp, the `<meta name="generated">` machine stamp, the jump nav, the atomic write, **the
`index.html` sidebar, and the 30-day prune**.

**Never write the index or delete an old brief yourself.** Navigation the model writes drifts out
of sync with what is on disk. The script rebuilds both from the directory listing every run, so a
manual delete or a back-dated brief self-corrects.

`--date`, `--out`, `--keep-days`, and `--no-index` exist for testing. `--out` also suppresses the
index and prune, so it is never right for a real run.
**Do not hand-write CSS, nav links, or a timestamp** — see `references/brief-html.md` for the
section skeleton, the allowed markup, and the urgency badge classes.

Then print one line to the terminal naming the file and the section count, and stop. Do not
print the briefing itself: the page is the briefing.

If the focus check proposed calendar fixes, they are written into the page as proposals and
nothing is moved. **Never write to the calendar during a run.** The user approves them by asking.

---

## Extending the brief

Add a data source (a metrics query, a customer-call digest, a revenue read) as its own step and
section:

1. Put the query, thresholds, and section shape in a new `references/<name>.md`.
2. Add the section to the order table in `references/brief-html.md`, between `inbox` and `today`.
3. Label its window in the subtitle (`yesterday`, `7-day`, `since Fri 8:30am`), and badge anything
   urgent in place.
4. Add its MCP server prefix to the tool list in `run.sh` (or `BRIEFING_ALLOWED_TOOLS`), or the
   8:30am run cannot call it.
5. For a week-opening extra, branch on `first_run_of_week` and take dates from `last_week`, never
   from the weekday.

---

## Best Practices

- Never let a slow source block the briefing. A failed step still emits its section, with
  `<p>&lt;unavailable: reason&gt;</p>` as the body, rather than aborting the run.
  A section that is empty because there was nothing to say is omitted entirely; a section that
  is empty because the source broke says so, quoting the error it actually got (see "Saying a
  source is unavailable" above).
