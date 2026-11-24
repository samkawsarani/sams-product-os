# Inbox Hygiene

One class of mail the user does not want to open by hand: meeting-invite receipts. Hygiene runs
**before** the Step 3 triage, so what it clears never reaches the Email column, and it reports
what it did in one line at the foot of that column.

**This is the only part of the gather that writes.** Everything else in the skill reads. Two
consequences: the mutations are deliberately narrow, and they are auditable.

How to select and change messages lives in the user's
`knowledge/company-context/tools/email-calendar.md`, under the `invite-receipts` and
`bulk-archive` needs. This file holds the rules that apply whatever the email tool is.

**If `invite-receipts` is `not supported` or missing**, skip hygiene and close the column with
`Hygiene · not set up for <tool>`.

Add your own classes here (a noisy list you only want marked read, an automated report whose
numbers you query elsewhere). Give each one a selection rule, a verdict, and a count in the audit
line, keep it inside the safety envelope, and add its tool mechanics to the category file.

## The safety envelope

| Allowed | Never |
|---------|-------|
| mark read | trash or delete |
| archive (remove from inbox) | add or remove a user label or folder |
| | touch a message outside the classes below |

Archive is recoverable. Mark-read is not reversible in any useful sense, but it destroys nothing.

Set `BRIEFING_NO_MUTATE=1` to run the whole gather read-only: hygiene still selects and counts,
still reports, and skips every write. Use it when changing the rules here, and say `(dry run)` in
the audit line.

Never call `bulk-archive` with an empty selection; skip the class and report `0`.

---

## Class 1: Meeting invites, no action needed

The calendar has already applied the event; the invite email is a receipt. Archive **and** mark
read.

Select with `invite-receipts`, and classify each message with the verdict table in the category
file. The principle behind every table, whatever the tool:

| Kind | Verdict |
|------|---------|
| Someone proposes a new time | **keep** |
| An update, cancellation, or invitation with a note, for an event today or later | **keep** |
| An RSVP (accepted, declined, tentative) to the user's own meeting | archive + read |
| A plain invitation, already on the calendar | archive + read |
| Anything above for an event in the past | archive + read |

**Fail toward leaving mail alone.** When the event date will not parse, keep. When a message
matches no known pattern, leave it untouched. Add patterns explicitly when they recur rather than
widening a fallback bucket: a mis-swept live invite is the exact failure this rule exists to
avoid.

The kept ones go in the Email column under their own line, as calendar changes rather than as
mail:

```html
<p><strong>Calendar changes</strong> &middot; <span class="b warn">new time proposed:</span>
  Roadmap Sync, organizer wants Thu 3pm</p>
```

**Known cost.** A plain invitation the user has not answered gets archived. That is deliberate: it
is already on the calendar, so Step 1 shows it, and the RSVP is a calendar action rather than an
inbox one. If they start missing RSVPs, move plain invitations to keep.

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
