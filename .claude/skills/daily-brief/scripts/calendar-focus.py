#!/usr/bin/env python3
"""Build the CALENDAR and FOCUS sections. Pure interval arithmetic, no model needed.

Fetches today's primary-calendar events via the `gws` CLI and emits both sections
to stdout. All the fiddly rules -- declined-filter, all-day handling, gap math,
density, conflicts, focus counting, fix proposals -- live here so they cannot
drift between mornings.

    calendar-focus.py [--html] [--date YYYY-MM-DD] [--json FILE]
                      [--tz-hours N] [--now HH:MM | --now none]

--html emits the two `<section>` blocks the brief wants (see
references/brief-html.md); the default is plain text for the terminal.

--json reads a saved `gws calendar events list` payload instead of calling gws,
for checking a change without waiting on the real calendar.

Rules encoded (from SKILL.md steps 1 and 2):
  * drop events where the self-attendee responseStatus == "declined"
  * the CALENDAR table lists meetings only: no focus blocks, no personal items,
    no all-day markers. They stay busy for gap and density math
  * drop all-day events entirely ("Home", "OOO"): they are markers, not meetings
  * workday is 09:00-17:00 local
  * focus = eventType "focusTime", or title containing "focus" / "deep work"
  * countable focus = labeled blocks + open gaps >= 60min in the workday,
    excluding lunch and personal events
  * daily target 2h minimum
  * fix order: (1) move the focus block to the next open >=60min slot,
    (2) else flag the conflicting meeting and note if you are optional on it
"""
import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys

WORK_START, WORK_END = 9 * 60, 17 * 60
FOCUS_TARGET_MIN = 120
GAP_FOCUS_MIN = 60
GAP_FREE_MIN = 30
DENSITY_RUN_MIN = 90  # a back-to-back stretch worth naming
DENSITY_GAP_MIN = 15  # <= this between meetings counts as back-to-back

FOCUS_RE = re.compile(r"\b(focus|deep work)\b", re.I)
SKIP_RE = re.compile(
    r"\b(lunch|ooo|out of office|pto|vacation|school|dentist|doctor|"
    r"appointment|personal|commute|break)\b", re.I)


def hhmm(mins):
    h, m = divmod(int(mins) % (24 * 60), 60)
    ampm = "am" if h < 12 else "pm"
    h12 = h % 12 or 12
    return "{}:{:02d}{}".format(h12, m, ampm) if m else "{}{}".format(h12, ampm)


def dur(mins):
    h, m = divmod(int(mins), 60)
    if h and m:
        return "{}h{}m".format(h, m)
    return "{}h".format(h) if h else "{}min".format(m)


def resolve_now(raw, date):
    """Cutoff in minutes from midnight. 0 means "nothing has passed yet"."""
    if raw == "none":
        return 0
    if raw:
        h, _, m = raw.partition(":")
        return int(h) * 60 + int(m or 0)
    local = dt.datetime.now().astimezone()
    if local.strftime("%Y-%m-%d") != date:
        return 0          # briefing for another day: no cutoff applies
    return local.hour * 60 + local.minute


def fetch(date, tz_hours):
    """Call gws for the given local date. Strips the keyring prefix line."""
    start = dt.datetime.fromisoformat(date + "T00:00:00")
    off = dt.timedelta(hours=tz_hours)
    params = {
        "calendarId": "primary",
        "timeMin": (start - off).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "timeMax": (start - off + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "singleEvents": True,
        "orderBy": "startTime",
    }
    out = subprocess.run(
        ["gws", "calendar", "events", "list", "--params", json.dumps(params)],
        capture_output=True, text=True, timeout=90)
    if out.returncode != 0:
        raise RuntimeError((out.stderr or out.stdout).strip()[:300])
    body = out.stdout[out.stdout.index("{"):]  # drop "Using keyring backend: ..."
    return json.loads(body)


def parse(payload, date):
    """-> (timed events, all-day context lines, cancelled notes, declined count)"""
    timed, allday, cancelled, declined = [], [], [], 0

    for ev in payload.get("items", []):
        title = ev.get("summary") or "(no title)"
        me = next((a for a in ev.get("attendees") or [] if a.get("self")), None)

        if me and me.get("responseStatus") == "declined":
            declined += 1
            continue

        if ev.get("status") == "cancelled":
            who = (ev.get("organizer") or {}).get("email", "someone")
            cancelled.append("{} was cancelled (by {})".format(title, who))
            continue

        start, end = ev.get("start") or {}, ev.get("end") or {}
        if "date" in start:  # all-day
            if start.get("date") == date and _one_day(start, end):
                allday.append(title)
            continue

        if "dateTime" not in start or "dateTime" not in end:
            continue
        s = dt.datetime.fromisoformat(start["dateTime"])
        e = dt.datetime.fromisoformat(end["dateTime"])
        timed.append({
            "title": title,
            "s": s.hour * 60 + s.minute,
            "e": e.hour * 60 + e.minute,
            "optional": bool(me and me.get("optional")),
            "focus": ev.get("eventType") == "focusTime" or bool(FOCUS_RE.search(title)),
            "skip": bool(SKIP_RE.search(title)),
        })

    timed.sort(key=lambda x: (x["s"], x["e"]))
    return timed, allday, cancelled, declined


def _one_day(start, end):
    try:
        s = dt.date.fromisoformat(start["date"])
        e = dt.date.fromisoformat(end.get("date", start["date"]))
        return (e - s).days <= 1
    except ValueError:
        return False


def free_gaps(busy, lo=WORK_START, hi=WORK_END):
    """Open intervals inside [lo, hi) not covered by `busy`, merged."""
    merged = []
    for b in sorted(busy, key=lambda x: x["s"]):
        if merged and b["s"] <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b["e"])
        else:
            merged.append([b["s"], b["e"]])
    gaps, cur = [], lo
    for s, e in merged:
        if s > cur:
            gaps.append((cur, min(s, hi)))
        cur = max(cur, e)
        if cur >= hi:
            break
    if cur < hi:
        gaps.append((cur, hi))
    return [(s, e) for s, e in gaps if e > s]


def calendar_data(timed, allday, cancelled, declined, now=0):
    """Everything the CALENDAR section needs, renderer-agnostic.

    The table lists MEETINGS only. The user already has their calendar open; a
    second copy of it is noise. Focus blocks belong to the FOCUS section, and
    lunch, school runs and OOO are things they put there themselves and do not
    need read back to them. They still count as busy for every gap and density calculation
    below -- excluded from the list, not from the day.
    """
    meetings = [e for e in timed if not e["focus"] and not e["skip"]]
    past = [e for e in meetings if e["e"] <= now]
    ahead = [e for e in meetings if e["e"] > now]

    rows = [(hhmm(ev["s"]), hhmm(ev["e"]), ev["title"], ev["optional"],
             ev["s"], ev["e"]) for ev in ahead]
    empty = None
    if not ahead:
        empty = ("No meetings left today." if past else "No meetings today.")

    notes = list(cancelled)
    if past:
        notes.append("Earlier today: {} meeting{} through {}".format(
            len(past), "" if len(past) == 1 else "s",
            hhmm(max(e["e"] for e in past))))

    # Overlaps worth a decision: both real meetings, neither optional.
    # Focus-block conflicts are reported by the FOCUS section, not duplicated here.
    real = [e for e in ahead if not e["optional"]]
    for i, a in enumerate(real):
        for b in real[i + 1:]:
            if b["s"] < a["e"]:
                notes.append("{} and {} overlap at {} - you'll need to pick one".format(
                    a["title"], b["title"], hhmm(b["s"])))

    # Free blocks in what's left of the workday. Labeled focus blocks are
    # committed time, so they count as busy -- otherwise a "free block" would
    # overlap deep work.
    lo = max(WORK_START, now)
    for s, e in free_gaps(timed, lo=lo):
        if e - s >= GAP_FREE_MIN:
            notes.append("Free block {}-{} ({})".format(hhmm(s), hhmm(e), dur(e - s)))

    # Back-to-back density in what's left of the workday. Lunch and personal
    # events break a run.
    run_start = run_end = None
    dense = [e for e in ahead if e["e"] > lo and e["s"] < WORK_END]
    for ev in dense:
        if run_end is not None and ev["s"] - run_end <= DENSITY_GAP_MIN:
            run_end = max(run_end, ev["e"])
        else:
            if run_end and run_end - run_start >= DENSITY_RUN_MIN:
                notes.append("Back-to-back from {} to {}".format(
                    hhmm(run_start), hhmm(run_end)))
            run_start, run_end = ev["s"], ev["e"]
    if run_end and run_end - run_start >= DENSITY_RUN_MIN:
        notes.append("Back-to-back from {} to {}".format(
            hhmm(run_start), hhmm(run_end)))

    if declined:
        notes.append("Hid {} declined meeting{}".format(
            declined, "" if declined == 1 else "s"))

    return {"sub": "remaining today" if past else None, "allday": list(allday),
            "rows": rows, "empty": empty, "notes": notes}


def focus_data(timed, now=0):
    """Everything the FOCUS section needs, renderer-agnostic."""
    lo = max(WORK_START, now)
    countable = [e for e in timed if not e["focus"] and not e["skip"]]
    # Only blocks with time left on them. A block that already ended is history,
    # not something to protect or propose moving.
    labeled = [e for e in timed if e["focus"] and e["e"] > now]

    def left(ev):
        return max(0, ev["e"] - max(ev["s"], now))

    # One entry per focus block, with whatever is booked over its remaining part.
    blocked = []
    for f in labeled:
        over = [m for m in countable
                if m["e"] > now and m["s"] < f["e"] and max(f["s"], now) < m["e"]]
        blocked.append((f, over))

    clear_min = sum(left(f) for f, over in blocked if not over)
    # Every event is busy for gap purposes -- lunch and personal events are
    # excluded from *counting as* focus, not from occupying the day.
    gaps = [(s, e) for s, e in free_gaps(timed, lo=lo) if e - s >= GAP_FOCUS_MIN]
    protected = clear_min + sum(e - s for s, e in gaps)
    labeled_min = sum(left(f) for f in labeled)
    conflicts = [(f, over) for f, over in blocked if over]
    partial = now > WORK_START

    if protected >= FOCUS_TARGET_MIN and not conflicts:
        return {"ok": True, "partial": partial, "protected": protected,
                "lead": "{} {}".format(dur(protected),
                                       "left today" if partial else "secured"),
                "proposals": [], "fallback": None}

    # Labeled is not the same as protected. Say both, or the number lies.
    lead = "{} actually protected".format(dur(protected) if protected else "0h")
    if labeled_min and labeled_min != protected:
        lead += " ({} labeled, {} booked over)".format(
            dur(labeled_min), len(conflicts))
    if partial:
        lead += " in what's left of the day"
    if protected < FOCUS_TARGET_MIN:
        lead += " - below the 2h target"

    proposals = []
    for f, over in conflicts:
        need = left(f)
        # A slot has to be in the future, and at or after the block it replaces.
        slot = next(((s, e) for s, e in free_gaps(timed, lo=lo)
                     if e - s >= need and s >= max(f["s"], now)), None)
        names = ", ".join(m["title"] for m in over)
        if slot:
            proposals.append('Move "{}" ({}-{}) to {}-{} - {} booked over it'.format(
                f["title"], hhmm(max(f["s"], now)), hhmm(f["e"]),
                hhmm(slot[0]), hhmm(slot[0] + need), names))
        else:
            opt = [m for m in over if m["optional"]]
            proposals.append(
                'No open {} slot left for "{}" - {} booked over it{}'.format(
                    dur(need), f["title"], names,
                    "; you're optional on " + ", ".join(m["title"] for m in opt)
                    if opt else ""))

    if not conflicts and gaps:
        best = max(gaps, key=lambda g: g[1] - g[0])
        proposals.append("Book focus {}-{} ({} open)".format(
            hhmm(best[0]), hhmm(best[1]), dur(best[1] - best[0])))

    fallback = None
    if not proposals and protected < FOCUS_TARGET_MIN:
        fallback = "No open >={} block left today.".format(dur(GAP_FOCUS_MIN))

    return {"ok": False, "partial": partial, "protected": protected,
            "lead": lead, "proposals": proposals, "fallback": fallback}


# ---- renderers ------------------------------------------------------------

def render_text(cal, foc):
    out = ["CALENDAR" + (" - remaining today" if cal["sub"] else "")]
    if cal["empty"]:
        out.append(cal["empty"])
    else:
        out += ["| Time | Event |", "|------|-------|"]
        for s, e, title, optional, _s, _e in cal["rows"]:
            out.append("| {}-{} | {}{} |".format(
                s, e, title, " *(you're optional)*" if optional else ""))
    if cal["notes"]:
        out += ["", "A few things to note:"] + ["- " + n for n in cal["notes"]]

    out.append("")
    if foc["ok"]:
        out.append("FOCUS  " + chr(10003) + " " + foc["lead"])
        return "\n".join(out)
    out += ["FOCUS", "! " + foc["lead"]]
    if foc["proposals"]:
        out.append("Proposed fixes:")
        out += ["{}. {}".format(i, p) for i, p in enumerate(foc["proposals"], 1)]
        out.append("Approve all, pick numbers, or skip?")
    elif foc["fallback"]:
        out.append(foc["fallback"])
    return "\n".join(out)


def esc(text):
    """Escape for the brief. Only the standalone dash becomes an em dash entity --
    hyphens inside words ("back-to-back") must survive intact."""
    return html.escape(str(text), quote=False).replace(" - ", " &mdash; ")


def _split(*columns):
    """Two labelled columns inside one card, per references/brief-html.md."""
    out = ['<div class="split">']
    for label, lines in columns:
        out.append("<div>")
        out.append('<p class="lbl">{}</p>'.format(html.escape(label)))
        out += lines
        out.append("</div>")
    out.append("</div>")
    return out


def _section(sid, icon, name, sub, body):
    head = "{} {}".format(icon, name)
    if sub:
        head += ' <span class="sub">{}</span>'.format(html.escape(sub))
    return ('<section id="{}"><h2>{}</h2><div class="body">\n{}\n'
            "</div></section>".format(sid, head, "\n".join(body)))


def render_html(cal, foc):
    """One `calendar` section, two columns: the meetings, and what they left
    you. They are one question about the day, and a focus conflict is caused by
    a row in the meeting table, so they have to be read together. See
    references/brief-html.md for the contract this satisfies."""
    left = []
    if cal["empty"]:
        left.append("<p>{}</p>".format(html.escape(cal["empty"])))
    else:
        left.append('<div class="scroll"><table>')
        left.append("<tr><th>Time</th><th>Event</th></tr>")
        for s, e, title, optional, smin, emin in cal["rows"]:
            name = html.escape(title)
            if optional:
                name += " <em>(you&rsquo;re optional)</em>"
            # data-s/data-e are minutes from midnight. The page uses them to
            # move a "you are here" line through the rows as the day passes.
            left.append(
                '<tr data-s="{}" data-e="{}"><td>{}&ndash;{}</td>'
                "<td>{}</td></tr>".format(smin, emin, esc(s), esc(e), name))
        left.append("</table></div>")
    if cal["notes"]:
        left.append('<div class="note">{}</div>'.format(
            " &middot; ".join(esc(n) for n in cal["notes"])))

    if foc["ok"]:
        right = ['<p><span class="b good">✓ {}</span></p>'.format(
            esc(foc["lead"]))]
    else:
        right = ['<p><span class="b warn">⚠</span> {}</p>'.format(
            esc(foc["lead"]))]
        if foc["proposals"]:
            right.append("<p>Proposed fixes:</p><ol>")
            right += ["<li>{}</li>".format(esc(p)) for p in foc["proposals"]]
            right.append("</ol>")
            right.append("<p>Approve all, pick numbers, or skip?</p>")
        elif foc["fallback"]:
            right.append("<p>{}</p>".format(esc(foc["fallback"])))

    return _section("calendar", "📅", "Calendar", cal["sub"], _split(
        ("Meetings", left), ("Focus", right)))


def unavailable(reason, as_html):
    if not as_html:
        return "CALENDAR\n<unavailable: {}>\n\nFOCUS\n<unavailable>".format(reason)
    return _section("calendar", "📅", "Calendar", None, _split(
        ("Meetings", ["<p>&lt;unavailable: {}&gt;</p>".format(html.escape(reason))]),
        ("Focus", ["<p>&lt;unavailable&gt;</p>"])))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--json", help="read a saved gws payload instead of calling gws")
    ap.add_argument("--html", action="store_true",
                    help="emit the two <section> blocks for the daily brief "
                         "instead of plain text")
    ap.add_argument("--tz-hours", type=int, default=None,
                    help="local UTC offset; default is this machine's")
    ap.add_argument("--now", default=None,
                    help='cutoff as HH:MM, or "none" for the whole day; '
                         "default is the current local time")
    a = ap.parse_args()

    if a.tz_hours is None:
        off = dt.datetime.now().astimezone().utcoffset() or dt.timedelta()
        a.tz_hours = int(off.total_seconds() // 3600)

    try:
        payload = json.load(open(a.json)) if a.json else fetch(a.date, a.tz_hours)
    except Exception as exc:                      # noqa: BLE001 - degrade, never abort
        print(unavailable(str(exc), a.html))
        return 1

    now = resolve_now(a.now, a.date)
    timed, allday, cancelled, declined = parse(payload, a.date)
    cal = calendar_data(timed, allday, cancelled, declined, now)
    foc = focus_data(timed, now)
    print(render_html(cal, foc) if a.html else render_text(cal, foc))
    return 0


if __name__ == "__main__":
    sys.exit(main())
