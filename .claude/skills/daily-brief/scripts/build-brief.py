#!/usr/bin/env python3
"""Assemble one dated daily brief from a content fragment. No markdown anywhere.

    build-brief.py --content fragment.html
    ... | build-brief.py                       (fragment on stdin)

Writes `thinking/daily-briefs/daily-brief-YYYY-MM-DD.html`, then rewrites the
sidebar index beside it and prunes briefs older than --keep-days. One run, one
dated file, so the briefs are a log rather than a single overwritten page.

The model writes only the <section> fragment. This fills in the page chrome from
brief-template.html: title, both timestamps, and the jump nav (derived from the
section ids, so the model never hand-writes nav links that can drift out of sync).
It also owns the index and the prune for the same reason: navigation the model
hand-writes drifts out of sync with what is actually on disk.

Writes atomically -- an open browser tab never sees a half-written page.

The `generated` <meta> is the machine-readable stamp `briefing-window.py` reads to
derive the next run's window and to decide whether this is the first run of the
week. It is written here, not by the model, so it cannot be forgotten or malformed.

`index.html` is the page to keep open in a tab: a sidebar of every retained date
beside an <iframe> showing one brief, newest on load. The sidebar links carry
target="brief", so they work with scripting off, and nothing in the shell needs to
reach into the frame -- each brief is its own opaque file:// origin.
"""
import argparse
import datetime as dt
import glob
import html
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "brief-template.html")
INDEX_TEMPLATE = os.path.join(HERE, "index-template.html")
# <repo>/.claude/skills/daily-brief/scripts/build-brief.py -> <repo>
REPO = os.environ.get(
    "BRIEFING_REPO",
    os.path.abspath(os.path.join(HERE, *[os.pardir] * 4)))
BRIEFS_DIR = os.path.join(REPO, "thinking", "daily-briefs")
# Must stay in step with briefing-window.py, which reads the same names.
NAME_RE = re.compile(r"^daily-brief-(\d{4}-\d{2}-\d{2})\.html$")
KEEP_DAYS = 30
SECTION_RE = re.compile(
    r'<section[^>]*\bid="([^"]+)"[^>]*>\s*<h2[^>]*>(.*?)</h2>',
    re.S | re.I)
TAGS = re.compile(r"<[^>]+>")
def nav_from(content):
    """Jump links, derived from the fragment's own section ids and headings."""
    out = []
    for sid, heading in SECTION_RE.findall(content):
        # Drop any <span class="sub"> subtitle: nav wants the bare name.
        name = re.sub(r'<span class="sub".*?</span>', "", heading, flags=re.S | re.I)
        name = TAGS.sub("", name).strip()
        name = re.sub(r"\s+", " ", name)
        # The heading is already HTML. Decode it before re-escaping, or an
        # entity in the name ("&amp;", an emoji reference) gets double-escaped.
        name = html.unescape(name)
        if name:
            out.append('<a href="#{}">{}</a>'.format(html.escape(sid),
                                                     html.escape(name)))
    return "".join(out)


def dated_briefs():
    """[(date, filename)] for every well-named brief in the dir, newest first."""
    out = []
    for path in glob.glob(os.path.join(BRIEFS_DIR, "daily-brief-*.html")):
        name = os.path.basename(path)
        m = NAME_RE.match(name)
        if not m:
            continue
        try:
            out.append((dt.date.fromisoformat(m.group(1)), name))
        except ValueError:
            continue                     # a plausible name, not a real date
    return sorted(out, reverse=True)


def prune(keep_days, today):
    """Delete briefs older than keep_days. Returns how many went.

    Deletion here is permanent: thinking/ is gitignored, so there is no history
    to recover from. That is the intended lifetime of a brief -- it describes one
    morning and is stale by the afternoon.
    """
    if keep_days <= 0:
        return 0
    cutoff = today - dt.timedelta(days=keep_days)
    gone = 0
    for date, name in dated_briefs():
        if date < cutoff:
            try:
                os.remove(os.path.join(BRIEFS_DIR, name))
                gone += 1
            except OSError:
                pass                     # a brief we cannot delete is not fatal
    return gone


def write_index(existing):
    """Rewrite index.html from what is actually on disk. Returns its path."""
    try:
        tpl = open(INDEX_TEMPLATE).read()
    except OSError as exc:
        print("cannot read index template: {}".format(exc), file=sys.stderr)
        return None

    items, month = [], None
    for date, name in existing:
        label = date.strftime("%B %Y")
        if label != month:
            month = label
            items.append('<div class="mo">{}</div>'.format(html.escape(month)))
        items.append(
            '<a class="d" href="{}" target="brief">{} {}<span class="day">{}</span></a>'
            .format(html.escape(name), date.strftime("%b"), date.day,
                    date.strftime("%a")))

    if existing:
        body = "".join(items)
        count = "{} brief{}".format(len(existing), "" if len(existing) == 1 else "s")
        newest = existing[0][1]
    else:
        body = '<div class="empty">No briefs yet.</div>'
        count = "none yet"
        newest = "about:blank"

    page = (tpl
            .replace("{{ITEMS}}", body)
            .replace("{{COUNT}}", html.escape(count))
            .replace("{{NEWEST}}", html.escape(newest)))
    left = re.findall(r"\{\{[A-Z_]+\}\}", page)
    if left:
        print("index placeholders unfilled: {}".format(sorted(set(left))),
              file=sys.stderr)
        return None

    out = os.path.join(BRIEFS_DIR, "index.html")
    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(page)
    os.replace(tmp, out)                 # atomic; an open tab never sees a gap
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", help="file holding the <section> fragment; "
                                      "omit to read stdin")
    ap.add_argument("--out", default=None,
                    help="default is thinking/daily-briefs/daily-brief-<today>"
                         ".html, resolved from this script's own location, so "
                         "the caller's cwd does not matter")
    ap.add_argument("--date", default=None, metavar="YYYY-MM-DD",
                    help="date the brief is for; defaults to today. Only for "
                         "testing -- a run always writes today's file")
    ap.add_argument("--keep-days", type=int, default=KEEP_DAYS,
                    help="prune briefs older than this many days (0 disables)")
    ap.add_argument("--no-index", action="store_true",
                    help="skip the index rewrite and the prune")
    ap.add_argument("--title", default=None,
                    help='defaults to "Daily Brief — <today, long form>"')
    a = ap.parse_args()

    content = (open(a.content).read() if a.content else sys.stdin.read()).strip()
    if not content:
        print("refusing to write an empty brief", file=sys.stderr)
        return 1

    try:
        for_date = (dt.date.fromisoformat(a.date) if a.date
                    else dt.date.today())
    except ValueError:
        print("--date must be YYYY-MM-DD", file=sys.stderr)
        return 1

    os.makedirs(BRIEFS_DIR, exist_ok=True)
    out = a.out or os.path.join(
        BRIEFS_DIR, "daily-brief-{}.html".format(for_date.isoformat()))

    try:
        tpl = open(TEMPLATE).read()
    except OSError as exc:
        print("cannot read template: {}".format(exc), file=sys.stderr)
        return 1

    now_utc = dt.datetime.now(dt.timezone.utc)
    local = now_utc.astimezone()
    hour = local.strftime("%I").lstrip("0") or "12"
    local_str = "{}, {} {}, {} · generated {}:{}{} {}".format(
        local.strftime("%A"), local.strftime("%B"),
        str(int(local.strftime("%d"))), local.strftime("%Y"),
        hour, local.strftime("%M"), local.strftime("%p").lower(),
        local.strftime("%Z"))

    title = a.title or "Daily Brief — {} {}".format(
        for_date.strftime("%b"), for_date.day)

    chrome = (tpl
              .replace("{{GENERATED_ISO}}", now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
              .replace("{{GENERATED_LOCAL}}", html.escape(local_str))
              .replace("{{TITLE}}", html.escape(title))
              .replace("{{NAV}}", nav_from(content)))

    # Check the chrome BEFORE the content goes in: a stray {{...}} inside a
    # quoted message is not an unfilled placeholder.
    left = re.findall(r"\{\{[A-Z_]+\}\}", chrome.replace("{{CONTENT}}", ""))
    if left:
        print("template placeholders unfilled: {}".format(sorted(set(left))),
              file=sys.stderr)
        return 1

    page = chrome.replace("{{CONTENT}}", content)

    tmp = out + ".tmp"
    with open(tmp, "w") as fh:
        fh.write(page)
    os.replace(tmp, out)            # atomic
    note = "wrote {} ({:,} bytes, {} sections)".format(
        os.path.relpath(out, REPO), len(page),
        len(SECTION_RE.findall(content)))

    # The index and the prune run off the directory listing, so they are correct
    # even after a manual delete or a brief written for a back-date.
    if not a.no_index and not a.out:
        gone = prune(a.keep_days, for_date)
        if write_index(dated_briefs()):
            note += ", index rewritten"
        if gone:
            note += ", pruned {} over {}d".format(gone, a.keep_days)
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
