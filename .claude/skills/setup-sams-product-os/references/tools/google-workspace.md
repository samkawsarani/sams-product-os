# Email + calendar: Google Workspace

Template. Setup copies this to `knowledge/company-context/tools/email-calendar.md`, removes this
paragraph, fills every `<...>` blank, and sets **Status**. Never ship the copy with a blank left in.

**Status**: <ready | not ready (gws not installed) | not ready (gws not logged in) | not ready (gws skills missing)>
**Access**: command-line tool `gws` (Google Workspace CLI), version <output of `gws --version`>
**Skills**: `gws-shared`, `gws-gmail`, `gws-gmail-triage`, `gws-gmail-read`, `gws-calendar`, `gws-calendar-agenda`
*Last updated: <YYYY-MM-DD>*

gws is pre-1.0 and its commands can change between versions. If a command below fails on a newer
version, check the matching gws skill for the current form and update this file.

## General gotchas

- Every command prints a `Using keyring backend: ...` line before the JSON. Strip everything
  before the first `{` before parsing.
- Request parameters go on `--params`, the request body on `--json` (not `--body`).
- `--dry-run` validates a call without sending it. Use it when changing a write.
- Exit codes: 0 ok, 1 API error, 2 auth (run `gws auth login`), 3 validation.

## Needs

### events-in-range

```bash
gws calendar events list --params '{"calendarId":"<calendar id>","timeMin":"<start, RFC3339>","timeMax":"<end, RFC3339>","singleEvents":true,"orderBy":"startTime"}'
```

Use this, not `gws calendar +agenda`: `+agenda` does not return `attendees[].responseStatus`,
which the declined filter needs.

- **Declined by the user:** the attendee entry with `self: true` has `responseStatus == "declined"`.
- **Optional:** that same entry has `optional: true`.
- **Focus time:** `eventType == "focusTime"`.
- **Cancelled:** `status == "cancelled"`; the organizer is `organizer.email`.
- **All-day:** `start.date` is set instead of `start.dateTime`.

For a quick read-only agenda with no filtering, `gws calendar +agenda --today` is fine.

### create-event

Only after the user has approved the specific change in this conversation.

```bash
gws calendar events insert --params '{"calendarId":"<calendar id>"}' --json '{"summary":"<title>","start":{"dateTime":"<RFC3339>"},"end":{"dateTime":"<RFC3339>"}}'
```

To move an existing event, `events patch` with `"eventId"` in `--params` and the new
`start`/`end` in `--json`.

### unread-to-me

```bash
gws gmail +triage --query '(to:me OR cc:me) is:unread after:<unix seconds>' --max 50 --format json
```

`+triage` is read-only. Keep `(to:me OR cc:me)`: a distribution list delivers to the list's
address, so `to:me` drops list mail, which is the point. Do not use `deliveredto:`.

### read-thread

```bash
gws gmail +read --id <message id> --format json
```

For the whole thread: `gws gmail users threads get --params '{"userId":"me","id":"<thread id>","format":"full"}'`.

### bulk-archive

Select ids first. `messages list` returns ids only:

```bash
gws gmail users messages list --params '{"userId":"me","q":"<query>","maxResults":100}' --format json
```

Then change up to 1000 at once:

```bash
gws gmail users messages batchModify --params '{"userId":"me"}' --json '{"ids":["<id>","<id>"],"removeLabelIds":["UNREAD","INBOX"]}'
```

An empty `messages` array means nothing matched: skip the call, never send an empty `ids` list.
`UNREAD` and `INBOX` are system labels and need no lookup.

## Rules

- **Never write to the calendar** without explicit approval of that specific change.
- **Mailbox writes are limited to** removing `UNREAD` (mark read) and `INBOX` (archive). Never
  trash, delete, or add or remove a user label.
- **Leave tool notifications out of triage** (issue trackers, design tools, code hosts, chat
  digests) unless the user is directly tagged.

## Scope

- **Account**: <email address of the Google account gws is logged in to>
- **Calendar ID**: <`primary` unless the user named another>
- **Time zone**: <IANA name, e.g. America/New_York>
- **Working hours**: <e.g. 9:00 to 17:00>
