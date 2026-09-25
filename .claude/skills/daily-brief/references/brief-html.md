# Daily Brief — HTML Contract

The brief is **HTML, generated directly**. There is no markdown step. You write a
fragment of `<section>` elements; `scripts/build-brief.py` wraps it in the page chrome.
The page is the skill's only output, so the fragment must be complete every run.

```bash
.claude/skills/daily-brief/scripts/build-brief.py --content /tmp/brief-content.html
# or:  cat fragment | .claude/skills/daily-brief/scripts/build-brief.py
```

The output path takes no argument: the script writes
`thinking/daily-briefs/daily-brief-<today>.html`, resolved from its own location, so it does not
matter where you run it from. It then rewrites `thinking/daily-briefs/index.html` (the sidebar
shell the user keeps open) and prunes briefs older than 30 days.

The `calendar` section is never hand-written: `calendar-focus.py --html` emits it in exactly
this shape. Paste its output into the fragment as-is.

The script owns, and you must not write yourself:

- the `<!doctype>`, `<head>`, `<style>`, `<header>`, `<footer>` — all of it lives in
  `scripts/brief-template.html`
- `<title>` and the human timestamp line
- `<meta name="generated" content="...">` — the machine stamp `briefing-window.py` parses
- the jump `<nav>`, derived from your section `id`s and headings
- `index.html`, the dated sidebar, and the prune of anything past 30 days
- the light/dark toggle and the stored preference behind it

So never hand-write nav links, a stamp, or CSS. Emit sections only.

`--title "..."` overrides the default (`Daily Brief` plus the brief's date). The script refuses to
write an empty brief and fails if a placeholder is left unfilled.

`--date`, `--out`, `--keep-days`, and `--no-index` are for testing the script by hand. Passing
`--out` writes wherever you point it and skips both the index and the prune, so it is never the
right flag for a real run.

---

## Section skeleton

Every section takes this exact shape. The `id` is what nav links to, so keep it a stable
kebab-case slug of the name.

```html
<section id="initiatives"><h2>🚀 Initiatives <span class="sub">since Fri 8:30am</span></h2><div class="body">
  ...content...
</div></section>
```

Headings go into the jump nav as written, so keep them short. Entities in a heading survive
(the nav decodes before re-escaping), but a literal emoji reads better there than a numeric
reference.

The `<span class="sub">` is the right-aligned subtitle: use it to qualify what the section
covers (`remaining today`, `since Fri 8:30am`, the task tally). Never use it for a generation
time: every section is written in the same run, and the header already carries that timestamp.

**Omit any section that would be empty.** Do not emit a header with no body.

## Section order and icons

| # | id | Heading | Icon | Split |
|---|----|---------|------|-------|
| 1 | `calendar` | Calendar | 📅 | Meetings + Focus |
| 2 | `meeting-prep` | Meeting Prep | 📋 | |
| 3 | `inbox` | Inbox | 📥 | Email + Slack |
| 4 | `initiatives` | Initiatives | 🚀 | |
| 5 | `today` | Today | 🗺️ | |
| 6 | `up-next` | Up Next | ▶️ | |
| 7 | `waiting-on` | Waiting On | ⏸️ | |
| 8 | `you-owe` | You Owe | ⏳ | |

**Layout is one column.** Two sections carry a 50/50 internal split instead of being two cards:

- `calendar` is **Meetings + Focus**. A focus conflict is caused by a row in the meeting table,
  and since that table lists meetings only, the focus block itself is not in it. Side by side
  you can see the meeting and the conflict it causes at once. `calendar-focus.py --html` emits
  the whole thing.
- `inbox` is **Email + Slack**. One question, "who needs a reply", asked of two places. You
  write that split yourself with `<div class="split">` (see Available markup).

Both stack to one column under 760px and in print.

The order follows how the morning is actually read, in four blocks:

1. **Where am I today** (1-2): the shape of the day, whether any of it is protected, and which
   meetings need something from you before they start.
2. **Who needs me** (3): the two reply queues.
3. **What changed while I was gone** (4): initiative movement since the last brief.
4. **So what do I do** (5-8): the plan, then the queues you act from.

Add your own "what changed" sections (a metrics read, a customer-feedback digest) between
`inbox` and `today`, and give each one a subtitle naming its window.

The page reads as an argument that ends in its conclusion: context first, then what to do about
it. `today` sits at 5 rather than at the top because it is read *after* forming a view, not
instead of forming one. It carries the Active tally as its subtitle.

**The one risk this order carries:** on a rushed morning the user reads the top and closes the
tab, so the plan is what gets missed. That is why anything genuinely urgent has to be badged red
where it is *found* (Steps 7-8), not held back for `today` to mention. `today` synthesizes; it is
not the only place a flag appears.

**`inbox` always renders**, even when clear, with a one-line all-clear in each column.
Everything else is omitted when empty. The difference: "no email needs a reply" is a thing the
user wants to know, and a missing section cannot be told apart from a broken source. "Nothing
moved on initiatives" is not worth a card.

`today` carries the Active-section checkbox tally as its subtitle:

```html
<section id="today"><h2>🗺️ Today <span class="sub">Active 5 of 14 done · In Progress 2/5 · Up Next 3/9</span></h2>
```

The brief never mirrors the raw task list — see Step 6 in SKILL.md for why.

## Available markup

Only these. The template styles nothing else.

| Markup | Use |
|--------|-----|
| `<p>` | a line of prose |
| `<ul><li>` / `<ol><li>` | list items; `<ol>` for the plan and priorities |
| `<div class="note">` | a dimmed sub-line under a bullet (detail, context) |
| `<blockquote>` | a verbatim quote from a message, or a `diffMarkdown` line from Linear |
| `<div class="split"><div>…</div><div>…</div></div>` | two halves of one question inside one card, 50/50, divided by a rule. Each half opens with a `<p class="lbl">` naming it. Stacks under 760px |
| `<div class="scroll"><table>` | **always** wrap a table; header row is a plain `<tr><th>`, no `<thead>`/`<tbody>`. Cells wrap their text, so a long cell makes a taller row, not a scrollbar. The first column stays on one line (a name, a time range), and `<span class="nw">` keeps anything else from breaking |
| `<code>` | file paths, identifiers, field names |
| `<strong>` / `<em>` | emphasis; `<em>` for "you're optional" |
| `<a href>` | **link every Linear item by name** (see below); add `target="_blank" rel="noreferrer"` yourself, the template does not |
| `<tr data-s="570" data-e="585">` | meeting rows only, minutes from midnight; the page dims past rows and marks the next one against the reader's clock. `calendar-focus.py` emits these |

## Linking out

The page is read to decide what to open next, so anything with a URL is a link on its **name**,
never a bare URL and never a trailing "(link)".

| What | Link to | Source of the URL |
|------|---------|-------------------|
| An initiative in `initiatives` or `you-owe` | its Linear page | `url` field on `list_initiatives` |
| A project | its Linear page | `url` field on `list_projects` |
| A named issue | its Linear page | `url` field on `list_issues` |
| A meeting note in `you-owe` | the note file | its repo-relative path under `meetings/` |

```html
<li><a href="https://linear.app/acme/initiative/checkout-redesign-1a2b3c" target="_blank" rel="noreferrer">Checkout Redesign</a> <span class="b good">onTrack</span></li>
```

`url` is a valid field on `list_initiatives`, `list_projects`, and `list_issues`; request it in
the `fields` array or it does not come back. Never hand-build a Linear URL from a name or a
slug: take the `url` the API returned.

## Urgency badges

Wrap the urgent token, not the whole line.

```html
<span class="b bad">flag:</span>      <!-- red:   act on this -->
<span class="b warn">watch:</span>    <!-- amber: keep an eye -->
<span class="b good">✓ 2h secured</span>
<span class="b muted">(tracked)</span>
```

| Class | Use for |
|-------|---------|
| `b bad` | `flag:`, `atRisk`, `offTrack`, `never posted`, overdue past threshold |
| `b warn` | `watch:`, `⚠`, approaching a threshold |
| `b good` | `onTrack`, `✓ Xh secured`, resolved items |
| `b muted` | `(tracked)`, `(you're optional)`, counts and asides |

Escape content that is not markup: `&amp;`, `&lt;`, `&mdash;`, `&rarr;`. Quoted messages and
email subject lines are the usual offenders.
