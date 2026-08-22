#!/usr/bin/env python3
"""Convert the AEA Registry CSV export into the JSON that the Hugo site consumes.

The registry CSV (`_data/trials.csv`, produced by `bin/download_data.py`) is the
database export.  This script normalises it into `data/trials.json`, which is the
single source of truth for the Hugo build:

    python3 bin/export_hugo_data.py                     # full export
    python3 bin/export_hugo_data.py --limit 25          # small sample
    python3 bin/export_hugo_data.py --markdown-out content/md-prototype

Stdlib only -- no pandas -- so the GitHub Actions workflow needs no pip install.
"""

import argparse
import collections
import csv
import datetime
import json
import os
import re
import sys

csv.field_size_limit(10**9)

# Name suffixes that must not be mistaken for a surname when building the
# "Last, First" form that Google Scholar's citation_author tag expects.
SUFFIXES = {"jr", "jr.", "sr", "sr.", "ii", "iii", "iv", "v", "phd", "ph.d.", "md", "m.d."}

EMAIL_RE = re.compile(r"\S+@\S+")
# "Name (email) Affiliation" -- the shape the registry uses for co-PIs.
INVESTIGATOR_RE = re.compile(r"^(?P<name>.*?)\s*\((?P<email>[^)]*)\)\s*(?P<affiliation>.*)$")


def clean(value):
    """Collapse whitespace and normalise the CSV's empty-ish values to ''."""
    if value is None:
        return ""
    value = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    return "" if value.lower() in ("nan", "none", "null") else value


def citation_name(name):
    """Render a person's name as "Last, First Middle" for citation_author.

    Google Scholar mis-parses author lists that mix formats, so every author --
    lead and co-investigator alike -- goes through this one function.
    """
    name = EMAIL_RE.sub("", name or "").strip().strip(",")
    if not name:
        return ""
    if "," in name:  # already "Last, First"
        return re.sub(r"\s+", " ", name)
    parts = name.split()
    if len(parts) == 1:
        return parts[0]
    last_idx = len(parts) - 1
    # Walk back past any trailing suffix so "Alan Krueger Jr." -> "Krueger, Alan Jr."
    while last_idx > 0 and parts[last_idx].lower().strip(",") in SUFFIXES:
        last_idx -= 1
    last = parts[last_idx]
    rest = parts[:last_idx] + parts[last_idx + 1:]
    return f"{last}, {' '.join(rest)}" if rest else last


def person(name, affiliation=""):
    display = re.sub(r"\s+", " ", EMAIL_RE.sub("", name or "").strip().strip(","))
    if not display:
        return None
    # Emails are deliberately dropped: the site never renders them, and keeping
    # them out of the build artefact avoids publishing a scrapeable address list.
    # Some rows repeat the address in the affiliation slot, so scrub that too.
    affiliation = re.sub(r"\s+", " ", EMAIL_RE.sub("", clean(affiliation))).strip(" ,;")
    return {
        "name": display,
        "citation_name": citation_name(display),
        "affiliation": affiliation,
    }


def parse_investigators(raw):
    """Split the co-PI field into structured people.

    Entries are separated by ';'.  Some rows omit the separator between a
    trailing affiliation and the next name, so a missing ';' yields one entry
    rather than a crash -- the display name is still correct.
    """
    people = []
    for chunk in (clean(raw) or "").split(";"):
        chunk = chunk.strip()
        if not chunk:
            continue
        match = INVESTIGATOR_RE.match(chunk)
        if match:
            entry = person(match.group("name"), match.group("affiliation"))
        else:
            entry = person(chunk)
        if entry:
            people.append(entry)
    return people


def parse_keywords(raw):
    """Keywords arrive as a JSON array literal; fall back to comma splitting."""
    raw = clean(raw)
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return [re.sub(r"\s+", " ", k).strip() for k in raw.split(",") if k.strip()]
    if isinstance(parsed, list):
        return [re.sub(r"\s+", " ", str(k)).strip() for k in parsed if str(k).strip()]
    return []


def parse_papers(raw):
    """Parse the semi-structured "Relevant papers" blob into records.

    The registry serialises each paper as a run of `Abstract:` / `Citation:` /
    `URL:` labels.  A new `Abstract:` (or a second `Citation:`) starts the next
    paper.  Anything unlabelled is treated as a continuation of the current
    field, since abstracts wrap across lines.
    """
    raw = clean(raw)
    if not raw:
        return []
    papers, current, field = [], {}, None

    def flush():
        if current and any(current.values()):
            papers.append({k: re.sub(r"\s+", " ", v).strip() for k, v in current.items() if v.strip()})

    for line in raw.split("\n"):
        match = re.match(r"^\s*(Abstract|Citation|URL|DOI)\s*:\s*(.*)$", line, re.IGNORECASE)
        if match:
            label = match.group(1).lower()
            if label in ("abstract",) or (label == "citation" and "citation" in current):
                flush()
                current, field = {}, None
            field = label
            current[field] = current.get(field, "") + match.group(2) + "\n"
        elif field:
            current[field] = current.get(field, "") + line + "\n"
    flush()
    return papers


def canonicalise_keywords(records):
    """Fold keyword spellings that differ only in case or spacing.

    Keywords are free text entered per registration, so the same concept
    arrives as "Behavior", "behavior" and "EDUCATION". Hugo already merges
    these into one taxonomy page (it normalises the term for the URL), but the
    trial pages still displayed whichever spelling that record happened to use.

    For each case-folded group the most frequently used spelling wins, so
    acronyms survive: "HIV" beats a stray "hiv", while "behavior" beats
    "Behavior" on volume. Ties prefer the all-lowercase spelling, then the
    lexicographically smallest, so the result does not depend on row order.
    """
    spellings = collections.defaultdict(collections.Counter)
    for record in records:
        for keyword in record["keywords"]:
            spellings[keyword.casefold()][keyword] += 1

    canonical = {}
    for key, counter in spellings.items():
        canonical[key] = min(
            counter,
            key=lambda word: (-counter[word], not word.islower(), word),
        )

    for record in records:
        seen, folded = set(), []
        for keyword in record["keywords"]:
            preferred = canonical[keyword.casefold()]
            # Merging can make one record list the same keyword twice.
            if preferred.casefold() not in seen:
                seen.add(preferred.casefold())
                folded.append(preferred)
        record["keywords"] = folded
    return records


def iso_date(value):
    """Normalise the CSV's "October 25, 2023" dates to ISO so templates never
    have to parse two formats.  Values already ISO are passed through."""
    value = clean(value)
    if not value:
        return ""
    if re.match(r"^\d{4}-\d{2}-\d{2}", value):
        return value[:10]
    for fmt in ("%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            continue
    return ""


def build_record(row):
    rct_id = clean(row.get("RCT_ID"))
    digits = re.search(r"\d+", rct_id)
    if not digits:
        return None
    number = str(int(digits.group()))

    lead = person(row.get("Primary Investigator"))
    others = parse_investigators(row.get("Other Primary Investigators"))
    # The lead PI is frequently repeated in the co-PI field; de-duplicate so the
    # citation_author tags don't list the same person twice.
    seen = {lead["name"].lower()} if lead else set()
    authors = ([lead] if lead else []) + [p for p in others if p["name"].lower() not in seen
                                          and not seen.add(p["name"].lower())]

    registered = clean(row.get("First registered on"))
    return {
        "rct_id": rct_id,
        "number": number,
        "title": clean(row.get("Title")),
        "doi": clean(row.get("DOI Number")),
        "registered": registered,
        "year": registered[:4],
        "last_update": iso_date(row.get("Last update date")),
        "status": clean(row.get("Status")),
        "start_date": clean(row.get("Start date")),
        "end_date": clean(row.get("End date")),
        "jel": [j.strip() for j in clean(row.get("Jel code")).split(",") if j.strip()],
        "keywords": parse_keywords(row.get("Keywords")),
        "countries": [c.strip() for c in clean(row.get("Country names")).split(";") if c.strip()],
        "authors": authors,
        "abstract": clean(row.get("Abstract")),
        "intervention": clean(row.get("Intervention")),
        "experimental_design": clean(row.get("Experimental design")),
        "randomization_method": clean(row.get("Randomization method")),
        "randomization_unit": clean(row.get("Randomization unit")),
        "sample_size_clusters": clean(row.get("Sample size number clusters")),
        "sample_size_observations": clean(row.get("Sample size number observations")),
        "sample_size_arms": clean(row.get("Sample size number arms")),
        "primary_outcomes": clean(row.get("Primary outcome end points")),
        "secondary_outcomes": clean(row.get("Secondary outcome end points")),
        "sponsors": clean(row.get("Sponsors")),
        "partners": clean(row.get("Partners")),
        "secondary_ids": clean(row.get("Secondary IDs")),
        "public_data_url": clean(row.get("Public data url")),
        "program_files_url": clean(row.get("Program files url")),
        "registry_url": clean(row.get("Url")),
        "papers": parse_papers(row.get("Relevant papers for csv")),
    }


def yaml_scalar(value):
    return json.dumps(value, ensure_ascii=False)  # JSON strings are valid YAML


def write_markdown(records, directory):
    """Emit one Markdown file per trial -- the alternative to the content adapter.

    The whole record is nested under `params.trial` so these pages render through
    exactly the same template as the content-adapter pages.  Taxonomy terms are
    deliberately NOT emitted here: the prototype duplicates records that already
    exist under /trials/, and listing them twice would pollute the taxonomy pages.

    Kept so both content models in CLAUDE.md can be built and compared from the
    same export.  See HUGO.md for the trade-off.
    """
    os.makedirs(directory, exist_ok=True)
    for record in records:
        path = os.path.join(directory, f"{record['number']}.md")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("---\n")
            handle.write(f"title: {yaml_scalar(record['title'])}\n")
            handle.write(f"date: {yaml_scalar(record['registered'])}\n")
            handle.write(f"lastmod: {yaml_scalar(record['last_update'] or record['registered'])}\n")
            handle.write(f"slug: {yaml_scalar(record['number'])}\n")
            handle.write("params:\n")
            # A JSON object is valid YAML flow mapping, so the record round-trips
            # without hand-rolling a YAML emitter.
            handle.write(f"  trial: {json.dumps(record, ensure_ascii=False, sort_keys=True)}\n")
            handle.write("---\n")
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--input", default="exports/trials.csv", help="registry CSV export")
    parser.add_argument("--out", default="data/trials.json", help="JSON consumed by Hugo")
    parser.add_argument("--limit", type=int, default=0, help="export only the first N trials")
    parser.add_argument("--markdown-out", default="", help="also write one Markdown file per trial")
    parser.add_argument("--indent", type=int, default=1, help="JSON indent (0 for compact)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        sys.exit(f"error: {args.input} not found -- run bin/download_data.py first")

    records = []
    with open(args.input, newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            record = build_record(row)
            if record:
                records.append(record)
            if args.limit and len(records) >= args.limit:
                break

    canonicalise_keywords(records)
    records.sort(key=lambda r: int(r["number"]))
    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False,
                  indent=args.indent or None, sort_keys=True)
        handle.write("\n")
    print(f"wrote {len(records)} trials to {args.out}")

    if args.markdown_out:
        count = write_markdown(records, args.markdown_out)
        print(f"wrote {count} Markdown files to {args.markdown_out}")


if __name__ == "__main__":
    main()
