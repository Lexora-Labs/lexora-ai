# Testing with EPUB sample files

This document is the reference for **which test inputs to use** and **where to put them locally**, so development and manual QA avoid shipping or relying on copyrighted commercial ebooks.

## Canonical source: IDPF EPUB 3 samples

Use the official **EPUB 3 Samples** catalog from the IDPF samples project:

- Catalog index: [https://idpf.github.io/epub3-samples/30/samples.html](https://idpf.github.io/epub3-samples/30/samples.html)
- Bulk downloads: [GitHub Releases for IDPF/epub3-samples](https://github.com/IDPF/epub3-samples/releases)

Per that catalog, **unless otherwise specified**, listed samples are licensed under **CC BY-SA 3.0** ([Creative Commons Attribution-ShareAlike 3.0](http://creativecommons.org/licenses/by-sa/3.0/)). Some entries have **different** terms (for example per-package notes or alternate licenses such as GNU FDL); always check the **package document** or catalog notes for a given file before redistributing it outside your own machine.

## Local folder: `samples/`

Convention for this repository:

- Place downloaded `.epub` files under the repo root folder `**samples/`** (for example `samples/accessible_epub_3.epub`).
- Use these files for **CLI smoke tests**, **Golden EPUB** work, and **regression** checks instead of personal or commercial books.

This keeps test data discoverable and aligned with the IDPF catalog, while still respecting licensing by using known sample publications.

## Primary test fixture (first)

For **initial** smoke tests, regressions, and docs examples, standardize on:

- **File:** `samples/accessible_epub_3.epub`
- **Publication:** *Accessible EPUB 3* (IDPF sample catalog)
- **Typical download:** [accessible_epub_3.epub](https://github.com/IDPF/epub3-samples/releases/download/20230704/accessible_epub_3.epub) (same artifact linked from the [catalog table](https://idpf.github.io/epub3-samples/30/samples.html))

Use other catalog titles only when you need coverage for a specific feature (fixed layout, vertical writing, MathML, and so on). Expand the Golden EPUB set over time; do not replace this as the default “first run” book without updating this doc and the README.

## Repository note: `*.epub` and `.gitignore`

The project `.gitignore` ignores `***.epub`** to reduce the risk of accidentally committing **copyright-sensitive** user books.

Implications:

- EPUBs you place under `samples/` are **normally not tracked** by Git unless you intentionally force-add them (for example after verifying license and team policy).
- For everyday development, that is **expected**: keep IDPF samples locally in `samples/` and run commands against those paths.

If maintainers decide to **commit** specific IDPF samples under `samples/`, that is a separate policy decision (license review + possible `.gitignore` exception). Do not commit arbitrary ebooks.

## Suggested quick smoke-test command

After copying `.env` and installing the package, from the repo root (example paths):

```powershell
lexora translate .\samples\accessible_epub_3.epub .\samples\out-accessible_epub_3.epub --target vi --service openai --limit-docs 1
```

Adjust `--service`, languages, and `--limit-docs` / `--start-doc` / `--end-doc` as needed.

**Automated smoke test:** `test_basic.py` includes an EPUB structured-batch check that uses `samples/hefty-water.epub` when that file is present (skipped otherwise). Keep that sample locally for full test coverage.

## Related docs

- [translation-logic.md](translation-logic.md) — canonical EPUB pipeline behavior
- [provider-api-key-guide.md](provider-api-key-guide.md) — API keys and `.env` for providers

