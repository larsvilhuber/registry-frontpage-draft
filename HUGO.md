# Hugo rebuild — scaffold notes

This is the Hugo rebuild described in `CLAUDE.md`. It has replaced the earlier
Jekyll draft, which is preserved in full at tag
[`v2025`](../../tree/v2025) — `_config.yml`, `_layouts/`, `_includes/`,
`_trials/`, `Gemfile` and the pandas-based generator scripts all live there and
are no longer in the working tree.

## Quick start

```bash
python3 bin/download_data.py            # fetch exports/trials.csv from the registry
python3 bin/export_hugo_data.py         # exports/trials.csv -> data/trials.json
hugo server                             # http://localhost:1313/
```

A 25-trial sample is committed in `data/trials.json`, so `hugo server` works
straight after a clone with no download step. Regenerate the sample with:

```bash
python3 bin/export_hugo_data.py --limit 25 --markdown-out content/md-prototype
```

## Layout

| Path | Purpose |
| --- | --- |
| `bin/download_data.py` | Fetch the registry CSV → `exports/trials.csv` (gitignored). |
| `bin/export_hugo_data.py` | CSV export → `data/trials.json`. Stdlib only, no pandas. |
| `data/trials.json` | The database export. Source of truth for the build. |
| `data/citations.json` | **Stubbed** incoming citations, keyed by DOI. |
| `content/trials/_content.gotmpl` | Content adapter: one page per registration. |
| `content/md-prototype/` | The alternative content model, for comparison. |
| `layouts/_partials/citation-meta.html` | Google Scholar `citation_*` tags. |
| `layouts/_partials/trial-detail.html` | Shared page body for both content models. |
| `static/js/search.js` | Client-side filter (progressive enhancement). |
| `static/img/cc-by-nc.png` | Licence badge, recovered from tag `v2025`. |
| `layouts/_partials/trial-toc.html` | "On this page" navigation for a trial (sidebar + mobile `<details>`). |
| `layouts/_partials/coins.html` | COinS context object for EndNote/RefWorks. |
| `layouts/_partials/citation-bibtex.txt`, `citation-ris.txt` | BibTeX/RIS record bodies. |
| `.github/workflows/hugo.yml` | Download → export → build → deploy, plus a daily cron. |

## Decision: content adapter, not one file per trial

`CLAUDE.md` left this open and asked for both to be prototyped. Both are built
here and render through the same template (`trial-detail.html`), so they are
directly comparable: `/trials/6/` and `/md-prototype/6/` are the same record.

**Recommendation: keep the content adapter** (`content/trials/_content.gotmpl`).

- The export stays a single artifact. Refreshing the site is one regenerated
  JSON file, not ~10,000 rewritten Markdown files — which matters because the
  site rebuilds on a schedule.
- Nothing generated needs committing. The Jekyll draft carried 40 MB of
  generated Markdown in `_trials/`; the equivalent Hugo content directory would
  be the same. In CI the full export is generated fresh and never enters git.
- It still produces *real* Hugo pages: permalinks, taxonomies, pagination and
  sitemap entries all behave normally. Nothing about Scholar indexing is
  weakened by generating pages this way — the emitted HTML is identical.

Keep `content/md-prototype/` only as long as it is useful for comparison. It is
marked `noindex`, excluded from the sitemap, and contributes no taxonomy terms,
because two indexable URLs for one registration would split Scholar's view of
the record.

## Google Scholar

Requirements from `CLAUDE.md`, and where each is handled:

- **Unique, stable, static URL per article** — `/trials/<number>/`, matching the
  numbering the registry itself uses. No query strings, no login wall.
- **Title, first author, year always present** — verified across the full
  export: all 9,823 records have a title, at least one author, and a
  registration year. The content adapter *skips* any record missing one rather
  than publishing a page Scholar would mis-parse.
- **`citation_*` tags, not Dublin Core** — `layouts/_partials/citation-meta.html`.
  One `citation_author` per author in `Last, First` form, no affiliations and no
  email addresses. Names are normalised in Python (`citation_name` in the
  export), not in templates, so the rule lives in one testable place.
- **`citation_pdf_url` only when a PDF exists** — the tag is emitted only if the
  record carries a `pdf_url`; advertising a PDF the crawler cannot fetch is
  penalised. Registrations have no PDFs today, so it is currently never emitted.
- **Full browseability** — `/trials/` is a static, paginated, JavaScript-free
  table, plus `sitemap.xml` listing every record.

Volume/issue/page and ISSN tags are deliberately not emitted: a trial
registration has none, and inventing them invites mis-parsing. `citation_doi`
and `citation_technical_report_number` carry the identifiers instead.

Metadata changes take 6–9 months to surface in Scholar, so treat the tag scheme
as stable from here.

## The landing page, and why async loading is safe

The Jekyll draft renders all ~9,800 rows into one DataTables table, which is
what makes it slow to load. This scaffold splits the two jobs that page was
doing:

**The crawl path is static.** Scholar's crawler does not reliably execute
JavaScript, so it never depends on any of the dynamic behaviour:

- `sitemap.xml` lists all 9,823 record URLs directly. This alone satisfies
  discovery.
- `/trials/` is a server-rendered table, 50 rows per page, with numbered
  pagination including first/last links — so page 197 is two hops away, not 196.
  Works with JavaScript disabled.
- The landing page ships only the 25 most recent records (about 10 KB) and links
  to the full browse.

**The search is an enhancement on top.** `static/js/search.js` reveals a search
box that is `hidden` in the served HTML, so a visitor without JavaScript sees
the static table and never a dead control. On first keystroke — not on page
load — it fetches `/index.json`, a slim index of every registration (short keys,
URL reconstructed from the trial number: ~1.5 MB, ~420 KB gzipped) and filters
in the browser. Clearing the box restores the static table.

This is why an async table is safe here: it is never the only way to reach a
record. Anything that made the dynamic list the *sole* index — replacing
`/trials/` with a JS-only view, or dropping the sitemap — would break Scholar
indexing.

Verified with a headless browser, with JavaScript both enabled and disabled:
lazy fetch, filtering, ID lookup, restore-on-clear, and the no-JS fallback
(50 static rows, hidden search box, intact `citation_*` tags).

## Incoming citations ("cited by")

`data/citations.json` is **placeholder data**. Per `CLAUDE.md` the real dataset
comes from a separate asynchronous process; nothing is fetched from an API at
build time. The template (`layouts/_partials/cited-by.html`) looks records up by
DOI and distinguishes "no data yet" from "zero citations".

The record-to-citation linkage is still the deferred open question. Two things
found while building that bear on it:

- Every one of the 9,823 records has a DOI (`10.1257/rct.<n>-<v>.<r>`), so DOI
  is a viable join key — but it encodes a *version*, so the citations dataset
  must either match the versioned DOI exactly or be keyed on the trial number.
- The export already contains a `Relevant papers` field for 744 trials (933
  papers), with free-text citations and, usually, a URL. These are rendered
  separately as "Papers from this trial". They are *outgoing* links recorded by
  the registry, not incoming citations, but they are the most obvious seed for
  reconciliation: resolving those URLs to DOIs gives a starting set of
  trial↔paper pairs to validate any matching approach against.

## Licence notice

Every page footer carries a CC BY-NC 4.0 notice with the badge recovered from
the Jekyll site, marked up with `rel="license"` so it is machine-readable.

It is scoped on purpose. The notice says *the design and presentation of this
site* is licensed, not the registrations: those records belong to the AEA RCT
Registry and are not this site's to license. Wording, version and badge all live
in `[params.license]` in `hugo.toml`, so changing the scope sentence or moving
to a different licence needs no template edit.

Note that the badge was an orphan in the Jekyll site — the image was committed
but no page ever referenced it, and no licence text was ever stated — so this
notice is new, not a restoration of previous wording.

## Page layout: navigation, citing, and reference-manager export

**"On this page" navigation.** A trial page's sections are listed in a sidebar
fixed to the left of the article on wide viewports (from 84rem/~1344px, where
there is room beside the centered 54rem content column), or in a collapsed
`<details>` just under the title otherwise. Both markups are always in the
DOM -- `layouts/_partials/trial-toc.html` renders both, `static/css/main.css`
switches which is visible by media query -- so this needs no JavaScript and
degrades correctly with it off.

**"How to cite" moved to the top**, directly under the title, as a `<details
open>` block so it is collapsible but visible by default. It now also links a
BibTeX and a RIS download for that one record.

**BibTeX and RIS downloads.** Every trial page gets `citation.bib` and
`citation.ris` as real static files (Hugo output formats registered in
`hugo.toml`, one Kind, `page`, applying only to actual trial detail pages --
list/taxonomy pages are a different Kind and are unaffected). The rendering
logic lives in `layouts/_partials/citation-bibtex.txt` and `citation-ris.txt`,
shared by both content models exactly like the HTML body is.

One non-obvious wrinkle: those two partials are named `.txt`, not `.html`.
Hugo decides html/template-vs-text/template escaping for a **partial** by that
partial's own file extension, independent of the calling page's output format
-- an `.html`-named partial gets HTML-escaped even when called from a plain-text
output format. The first version of this used `.html` partials and silently
corrupted every ampersand into `\&amp;` inside `.bib` files (invalid
BibTeX) before this was caught. Verified with `bibtexparser`/`rispy` against a
random sample of 800 files from the full 9,823-trial export, and specifically
against records containing `&`, `%`, `#`, `$` (66 titles/authors in the full
export have one). BibTeX escapes those five for LaTeX; RIS, being plain text,
does not.

Author names, dates and keywords in these exports reuse the same
`citation_name`/ISO-date fields the Scholar tags use, so all four citation
surfaces (`citation_*` meta tags, the "How to cite" text, BibTeX, RIS) describe
one record consistently.

**Recognition by reference managers**, checked against each tool's own stated
mechanism rather than assumed:
- **Zotero**: reads the `citation_*` (Highwire) meta tags directly via its
  generic embedded-metadata translator -- confirmed working against the live
  site.
- **Mendeley**: its Web Importer documentation states it reads five metadata
  standards including Highwire tags, which this site already emits; nothing
  further was needed.
- **EndNote / RefWorks**: commonly rely on **COinS** (a `<span class="Z3988">`
  carrying an OpenURL 1.0 context object) rather than `citation_*` tags, so this
  was the one true gap. `layouts/_partials/coins.html` adds it, encoded as
  Dublin Core (`info:ofi/fmt:kev:mtx:dc`) since a trial registration has no
  volume/issue to report as a journal article. Not independently verified
  against live EndNote/RefWorks installs -- only that the emitted context
  object is well-formed and matches the documented convention.

The BibTeX/RIS downloads exist for the remaining case: any reference manager
with neither a `citation_*` translator nor COinS support.

## Deployment

`.github/workflows/hugo.yml` downloads the registry CSV, regenerates
`data/trials.json`, builds, and deploys to GitHub Pages — on push to `main`,
daily at 05:23 UTC, and on demand. The full export is never committed; the CSV
download is sanity-checked (a response with fewer than 5,000 rows fails the
build rather than publishing a site missing most of the registry).

Pages *Source* is set to *GitHub Actions*, so this workflow is what publishes
the site.

## Scale

The full export builds in about 40 seconds: 9,823 registration pages plus
taxonomy and browse pages, roughly 30,000 pages total.

Keyword cardinality is high. Keywords are free text entered per registration,
so the raw export holds 11,188 distinct strings across 9,823 trials — more
keywords than trials — and 71% of them occur on exactly one trial.

The exporter folds spellings that differ only in case or spacing
(`canonicalise_keywords`), which brings that down to 9,033 distinct keywords.
The most-used spelling of each wins, so acronyms survive: `COVID-19` beats a
stray `covid-19`, while `behavior` beats `Behavior` on volume.

Note that the winning spelling is decided across whatever set is being exported.
Regenerating the 25-trial sample with `--limit` counts only those 25 records, so
a sample keyword can keep a spelling the full export would fold away. The
deployed site always folds over the complete export.

Even so, roughly two thirds of keyword term pages list a single trial. A page
whose entire content is one link to a record already in the sitemap is filler,
so term pages are excluded from the sitemap (set
`params.sitemapIncludeTerms = true` in `hugo.toml` to include them). They stay
linked from trial pages and remain crawlable; they just do not compete with the
records. This keeps the sitemap at about 9,830 URLs rather than about 20,100.

At the other end of the same distribution, the largest terms are huge: `behavior`
covers 3,429 trials, and one country value covers over a thousand more. The full
export first exposed this once term pages stopped being an afterthought:
`layouts/term.html` and `layouts/taxonomy.html` (the keyword index itself, which
lists ~9,000 terms) render through `.Paginator` for the same reason `/trials/`
does -- an unpaginated `countries/private/` page was 1.6 MB before this. It was
not visible in the 25-trial sample, which is the kind of gap only a full-scale
build catches.

## Known gaps

- Article-to-citation linkage is unresolved (see above) — deliberately deferred.
- Author names come from free-text database fields. 21 authors across the full
  export have single-token names (including one, `NBER`, that is an
  organisation), so `citation_author` for those is a bare token. The source
  records would need cleaning; the exporter does not guess.
- Affiliations are frequently missing or contain a repeated email address in the
  source data. Emails are stripped from both name and affiliation and are never
  published.
- Country names are not case-folded the way keywords are. The 1,363 distinct
  values look cleaner than the keyword field, but they have not been audited.
- The licence notice covers this site's presentation only. Whether the
  registration records carry their own terms is a question for the AEA; the
  notice deliberately does not speak for them.
- Only the lead investigator is shown in list tables, to keep rows scannable.
