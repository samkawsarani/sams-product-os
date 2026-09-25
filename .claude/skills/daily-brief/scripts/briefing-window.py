#!/usr/bin/env python3
"""Emit the briefing window as JSON. No date math left to the model.

Briefs are dated files under `thinking/daily-briefs/`, one per run:
`daily-brief-YYYY-MM-DD.html`. The window source is the newest brief dated BEFORE
today, whose `<meta name="generated">` stamp (written by build-brief.py) says when
the last run happened.

**A brief dated today is ignored entirely.** It is the file this run is about to
overwrite -- this morning's draft of the very page being rebuilt -- not evidence
that today has been covered. That makes a brief reproducible: regenerating day D
covers the same span however many times it runs.

Window start = the EARLIER of:
  * the `generated` stamp in the newest brief dated before today
  * local start of today

Both cases fall out of that:
  * Monday 8:30am -> Friday's stamp is earlier than Monday 00:00, so the window
    covers the weekend automatically.
  * A second run the same Monday -> still Friday's stamp, so the re-run covers the
    weekend too instead of shrinking to the last hour.

`first_run_of_week` is true when no brief dated before today falls on or after this
week's Monday.
It is the hook for any week-opening extra you add (a prior-week metrics block, say)
WITHOUT testing for literal Monday, so a stat holiday, a sick day, or a manual
Saturday run all fall out correctly: the first weekday you actually run gets the
week's catch-up, and only one run gets it.

    {"since_iso": "2026-08-28T12:30:09Z", "since_human": "Fri 8:30am",
     "iso_duration": "-P5D", "days": 5, "source": "last-briefing",
     "file": "thinking/daily-briefs/daily-brief-2026-08-28.html",
     "first_run_of_week": true, "week_start": "2026-08-31",
     "last_week": {"start": "2026-08-24", "end": "2026-08-30",
                   "prior_start": "2026-08-17", "prior_end": "2026-08-23"}}

`last_week` is present only when `first_run_of_week` is true, and always names two
complete Mon-Sun weeks: the one that just ended and the one before it. It is there so
a week-over-week query is never assembled from date math done by hand.

The repo root is derived from this file's own location, so a clone anywhere
works; BRIEFING_REPO overrides it.

Prefer `since_iso` wherever the API takes an absolute timestamp (Linear list_* do).
`iso_duration` rounds UP to whole days, so it over-covers rather than missing items.
"""
import datetime as dt
import glob
import json
import os
import re
import sys

# <repo>/.claude/skills/daily-brief/scripts/briefing-window.py -> <repo>
_DEFAULT_REPO = os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), *[os.pardir] * 4))
REPO = os.environ.get("BRIEFING_REPO", _DEFAULT_REPO)
BRIEFS_REL = os.path.join("thinking", "daily-briefs")
BRIEFS_DIR = os.path.join(REPO, BRIEFS_REL)
# daily-brief-YYYY-MM-DD.html. The date is in the name, so "newest" is a string
# sort and never depends on mtime, which a copy or a restore would scramble.
NAME_RE = re.compile(r"^daily-brief-(\d{4}-\d{2}-\d{2})\.html$")
STAMP = re.compile(r'<meta\s+name="generated"\s+content="([^"]+)"', re.I)


def briefs():
    """[(date, path)] for every well-named brief, newest first."""
    out = []
    for path in glob.glob(os.path.join(BRIEFS_DIR, "daily-brief-*.html")):
        m = NAME_RE.match(os.path.basename(path))
        if not m:
            continue
        try:
            out.append((dt.date.fromisoformat(m.group(1)), path))
        except ValueError:
            continue                     # a plausible name, not a real date
    return sorted(out, reverse=True)


def newest_stamp(existing):
    """(datetime, repo-relative path) from the newest brief, or (None, None).

    Walks newest-first rather than trusting the first file: a brief truncated by a
    crash has no parseable stamp, and the run before it is still a valid window.
    """
    for _, path in existing:
        try:
            with open(path) as fh:
                m = STAMP.search(fh.read(4096))
        except OSError:
            continue
        if not m:
            continue
        try:
            stamp = dt.datetime.fromisoformat(m.group(1).replace("Z", "+00:00"))
        except ValueError:
            continue
        return stamp, os.path.join(BRIEFS_REL, os.path.basename(path))
    return None, None


def human(ts):
    local = ts.astimezone()
    hour = local.strftime("%I").lstrip("0") or "12"
    return "{} {}:{}{}".format(
        local.strftime("%a"), hour, local.strftime("%M"),
        local.strftime("%p").lower())


def main():
    now = dt.datetime.now(dt.timezone.utc)
    local_now = now.astimezone()
    today = local_now.date()
    start_of_today = local_now.replace(
        hour=0, minute=0, second=0, microsecond=0)

    existing = briefs()
    # A brief dated TODAY is the file this run is about to overwrite, so it is not
    # evidence that today has been covered -- it is this morning's draft of the
    # very page being rebuilt. Counting it made a same-day re-run produce a
    # STRICTLY WORSE brief than the 8:30am one: the window shrank to the last few
    # hours and `first_run_of_week` flipped to false, so a Monday re-run silently
    # dropped everything that happened over the weekend.
    #
    # Excluding it makes a brief REPRODUCIBLE: regenerating day D covers the same
    # span however many times it runs. Everything that follows is computed from
    # `prior` for that reason.
    prior = [(d, p) for d, p in existing if d < today]
    stamp, source_file = newest_stamp(prior)

    if stamp is None:
        since, source = now - dt.timedelta(days=1), "fallback"
    else:
        # min() is a floor against a future-dated stamp, not the same-day fix it
        # used to be: `prior` already excludes today, so the stamp is normally the
        # earlier of the two and a re-run keeps the full window.
        since = min(stamp, start_of_today)
        source = "last-briefing" if since == stamp else "start-of-today"

    secs = (now - since).total_seconds()
    days = max(1, -(-int(secs) // 86400))  # ceil, never under-cover

    # Monday of the current week, and the two complete weeks before it.
    week_start = today - dt.timedelta(days=today.weekday())
    first_run = not any(d >= week_start for d, _ in prior)

    out = {
        "since_iso": since.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "since_human": human(since),
        "iso_duration": "-P{}D".format(days),
        "days": days,
        "source": source,
        "file": source_file,
        "first_run_of_week": first_run,
        "week_start": week_start.isoformat(),
    }
    if first_run:
        last_end = week_start - dt.timedelta(days=1)        # yesterday's Sunday
        last_start = last_end - dt.timedelta(days=6)
        out["last_week"] = {
            "start": last_start.isoformat(),
            "end": last_end.isoformat(),
            "prior_start": (last_start - dt.timedelta(days=7)).isoformat(),
            "prior_end": (last_end - dt.timedelta(days=7)).isoformat(),
        }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
