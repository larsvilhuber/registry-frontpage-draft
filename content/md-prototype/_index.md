---
title: "Prototype: one Markdown file per trial"
---

This section holds the **alternative content model** described in CLAUDE.md: one
Markdown file per registration, front matter written by the export script,
instead of pages generated at build time from `data/trials.json`.

It renders through exactly the same templates as `/trials/`, so the two models
can be compared directly. Only a small sample is committed, the pages are marked
`noindex` and kept out of the sitemap (they duplicate records that already live
under `/trials/`), and they contribute no taxonomy terms.

See `HUGO.md` for the trade-off and the recommendation.

Regenerate with:

    python3 bin/export_hugo_data.py --limit 25 --markdown-out content/md-prototype
