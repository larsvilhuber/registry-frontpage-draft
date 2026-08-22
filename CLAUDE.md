# Project: Hugo-based journal website

## Background

This is a new, standalone website — separate from Lars's existing personal
academic site (which runs Jekyll + jekyll-scholar via GitHub Actions on
GitHub Pages; that setup is fine and is NOT being replaced).

The existing site being replaced is a journal currently running on an
idiosyncratic, ~2015-era custom design. The goal is to rebuild it as a much
simpler, static, database-driven site.

## Core requirements

1. **Content is entirely database-driven.** All "articles" are already
   structured records in an existing database, all following the same
   uniform schema/format. This is not a blog — there is no need for a CMS,
   authoring workflow, or submission system. The site is a *presentation
   layer* over an export from that database.

2. **No submission system needed.** Articles are added to the database
   through an existing separate process, not through the website.

3. **Google Scholar indexing is a hard requirement.** The generator choice
   (Jekyll vs Hugo, etc.) is irrelevant to Scholar indexing — Scholar's
   crawler cares only about page structure and metadata, not the tech stack.
   Key Scholar inclusion requirements to bake into the article page template:
   - Each article must be on its own static page with a unique, stable URL
     (no session params, no login wall).
   - Minimum required fields: article title, first author's full name,
     year of publication. Missing any of these causes mis-parsing.
   - Use `citation_*` meta tags in `<head>` (preferred over Dublin Core):
     - `citation_title`
     - `citation_author` (one tag per author, "Last, First" format, no
       affiliations — repeat the tag for multiple authors)
     - `citation_publication_date` (YYYY/MM/DD or YYYY)
     - `citation_journal_title`
     - `citation_issn` / `citation_volume` / `citation_issue` /
       `citation_firstpage` / `citation_lastpage` as available
     - `citation_pdf_url` if a PDF exists per article
   - A sitemap or fully browseable index so the crawler can discover every
     article page.
   - New/changed metadata can take 6–9 months to be reflected in Scholar, so
     get the tag scheme right early rather than iterating live.

4. **Incoming citations ("cited by"), not outgoing references.**
   - We do NOT need to render bibliographies/reference lists the way
     jekyll-scholar or al-folio do (those solve *outgoing* citation
     rendering from a local .bib file — not needed here, since we're not
     using BibTeX as the source of truth).
   - What we DO need: displaying which other works cite each article
     (incoming citations), sourced from an **separate, already-existing
     async process** that maintains a citations table/dataset. This is
     NOT computed live at build time via API calls (OpenCitations etc. were
     discussed as a possible data source, but the linkage/sourcing decision
     is deferred — build the template assuming a pre-computed data file is
     available, keyed by article ID/DOI).
   - Exact linkage between article records and the citations dataset (DOI
     matching, ID reconciliation, etc.) is an open question, deliberately
     deferred to a later stage. Don't block the initial build on it — stub
     it with placeholder/sample data.

## Why Hugo, not Jekyll

- Jekyll is what Lars's *personal* site uses, with jekyll-scholar for
  BibTeX-driven bibliography rendering via GitHub Actions. That plugin
  ecosystem is irrelevant here since this project's records come from a
  database export, not a .bib file, and we explicitly don't need
  jekyll-scholar or al-folio's complexity.
- Once the jekyll-scholar/al-folio angle is off the table, this becomes a
  generic "flat data export → many uniform templated pages" problem, which
  Hugo handles natively and fast (via `data/` files or generated per-page
  front matter) without needing Ruby/Bundler.
- Hugo builds are dramatically faster at scale (seconds vs. minutes for
  1,000+ pages), which matters since the site will presumably rebuild on a
  schedule (cron via GitHub Actions) as the citations dataset updates.
- Searches did not turn up strong real-world examples of established
  multi-article *journals* running on Hugo (most "Hugo Academic" examples
  are personal CV/publication-list sites, not journals hosting their own
  articles) — so there's no existing "Hugo journal theme" to adopt. The
  plan is to build a minimal custom setup rather than search further for
  a template that likely doesn't exist. This is fine: the pattern needed
  (one content type, one list page, custom meta tags) is simple and
  well-trodden in Hugo generally.

## Hosting / deployment

- GitHub Pages + GitHub Actions, matching the existing site's deployment
  pattern (Lars is already comfortable with this from the Jekyll site).
- Hugo + GitHub Actions requires no Ruby/Bundler step — just download the
  Hugo binary in the workflow, run `hugo`, deploy `public/`.

## Suggested initial build plan (not yet started)

1. Scaffold a new Hugo site (`hugo new site .`).
2. Define a single content type for articles (e.g. `content/articles/`),
   populated either via:
   - a `data/articles.json` (or `.yaml`) file consumed by a list/detail
     template, or
   - one generated Markdown file per article (front matter written by an
     export script from the database).
   Decide based on how naturally the DB export maps to Hugo's data vs.
   content model — worth prototyping both on a small sample before
   committing.
3. Build the article detail template:
   - Renders the article content/metadata.
   - Injects all required `citation_*` meta tags.
   - Includes a "Cited by" section reading from the (initially stubbed)
     incoming-citations data file, keyed by article ID/DOI.
4. Build an index/list page enumerating all articles (for crawlability and
   basic browsing).
5. Add a sitemap (Hugo generates one by default — verify it includes all
   article pages).
6. Set up the GitHub Actions workflow: checkout → install Hugo → build →
   deploy to Pages. Add a scheduled (cron) trigger since the citations
   dataset updates on its own cadence, independent of code changes.
7. Once basic build works, do a Scholar-indexing sanity check per their
   guidelines (test with `site:` search after articles are indexed, expect
   the 6-9 month lag).
8. Revisit the article-to-citation-record linkage problem (DOI matching or
   other reconciliation) once the base site is working end to end.

## Explicitly out of scope / deferred

- Submission system / peer review workflow — not needed, out of scope.
- Outgoing bibliography rendering (jekyll-scholar-style) — not needed.
- Live API calls to citation indexes (OpenCitations etc.) at build time —
  not needed; citations data is precomputed elsewhere.
- Precise mechanism for linking DB article records to the citations
  dataset — deferred.
