# Inbox Hygiene

One class of mail the user does not want to open by hand: meeting-invite receipts. Hygiene runs
**before** the Step 3 triage query, so what it clears never reaches the Email column, and it
reports what it did in one line at the foot of that column.

**This is the only part of the gather that writes.** Everything else in the skill reads. Two
consequences: the mutations are deliberately narrow, and they are auditable.

Add your own classes here (a noisy list you only want marked read, an automated report whose
numbers you query elsewhere). Give each one a selection query, a verdict, and a count in the
audit line, and keep it inside the safety envelope.

## The safety envelope

| Allowed | Never |
|---------|-------|
| remove `UNREAD` (mark read) | `trash`, `delete`, `batchDelete` |
| remove `INBOX` (archive) | add or remove a user label |
| | touch a message outside the classes below |

Archive is recoverable (`in:anywhere` still finds it, and adding `INBOX` back restores it).
Mark-read is not reversible in any useful sense, but it destroys nothing.

Set `BRIEFING_NO_MUTATE=1` to run the whole gather read-only: hygiene still selects and counts,
still reports, and skips every `batchModify`. Use it when changing the rules here, and say
`(dry run)` in the audit line.

## Mechanics

`gws gmail users messages batchModify` takes the ids inline and does up to 1000 at a time:

```bash
gws gmail users messages batchModify --params '{"userId":"me"}' \
  --json '{"ids":["<id>","<id>"],"removeLabelIds":["UNREAD"]}'
```

The request body goes on `--json`, not `--body`. Add `--dry-run` to validate without sending.
`UNREAD` and `INBOX` are system label IDs and need no lookup; user labels are matched by **name**
in the query instead, which is why nothing here resolves a `Label_<id>`.

Select the ids with `gws gmail users messages list`, which returns ids and nothing else:

```bash
gws gmail users messages list --params '{"userId":"me","q":"<query>","maxResults":100}' --format json
```

An empty `messages` array means nothing matched. Do not call `batchModify` with an empty `ids`
array; skip the class and report `0`.

---

## Class 1: Meeting Invites, no action needed

Calendar has already applied the event; the invite email is a receipt. Archive **and** mark
read.

This assumes a Gmail filter that labels invites `Meeting Invites`. If the user has no such label,
select on the subject prefixes below with `from:calendar-notification@google.com` instead of the
label, and say so once in the audit line.

Select on subject prefix, because Google writes these subjects and they are stable:

| Subject begins | Verdict |
|----------------|---------|
| `Proposed new time:` | **keep** — someone is asking the user to move |
| `Updated invitation:` / `Updated invitation with note:` | **keep** if the event is today or later |
| `Canceled invitation:` / `Cancelled invitation:` | **keep** if the event is today or later |
| `Invitation with note:` | **keep** if the event is today or later |
| `Accepted:` / `Declined:` / `Tentative:` | archive + read — an RSVP to their own meeting |
| `Invitation:` | archive + read — already on the calendar, and Step 1 lists it |
| anything above, event date in the past | archive + read |

The event date is in the subject (`… @ Thu Sep 10, 2026 2pm - 3pm (EDT) …`). Parse it; when it
will not parse, **keep** the message. Hygiene fails toward leaving mail alone.

Select everything under the label that is unread or in the inbox, classify each subject, and
batch the archive set:

```bash
gws gmail users messages list --params '{"userId":"me","q":"label:\"Meeting Invites\" (is:unread OR in:inbox)","maxResults":100}'
# then, for the archive set:
--json '{"ids":[...],"removeLabelIds":["UNREAD","INBOX"]}'
```

The kept ones go in the Email column under their own line, as calendar changes rather than as
mail:

```html
<p><strong>Calendar changes</strong> &middot; <span class="b warn">new time proposed:</span>
  Roadmap Sync, organizer wants Thu 3pm</p>
```

**Known cost.** A plain `Invitation:` for something the user has not answered gets archived.
That is deliberate: Google has already put it on the calendar, so Step 1 shows it, and the RSVP
is a calendar action rather than an inbox one. If they start missing RSVPs, move `Invitation:`
to keep.

**Unknown prefixes are left alone.** Old mailboxes carry subjects that match none of the table
(`Appointment booked:`, `Tentatively Accepted:` with a capital A, forwards like `Fwd: ...`).
Leave them untouched rather than guessing. Add them as explicit prefixes when they recur rather
than widening a fallback bucket: a mis-swept live invite is the exact failure this rule exists to
avoid.

---

## The audit line

Last line of the Email column, always, even at zero. A hygiene pass that silently did nothing
looks identical to one that silently broke.

```html
<p class="note">Hygiene &middot; 4 invites archived, 1 kept</p>
```

When a class fails, say which and quote the error rather than dropping it from the line:
`invites &lt;unavailable: 403 insufficient scope&gt;`. A failed class never stops the brief, and
never stops any other class you have added.
