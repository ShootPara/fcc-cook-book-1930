# First Congregational Church of Kalamazoo Mayflower Guild Cookbook (1930)

An accessible, static website for the corrected 1930 Mayflower Guild cookbook. It is published at <https://shootpara.github.io/fcc-cook-book-1930/> and deploys automatically from `main` through GitHub Pages.

## What is in this repository

- `source/` — immutable Version 8 editorial source: 708 recipes in 31 chapters.
- `dist/` — the published static site and its versioned JSON edition.
- `tools/build_edition.py` — reproducibly generates the public data and matching report.
- `reports/canonical-ingredient-matches.json` — every ingredient-line matching decision.
- `reports/ingredient-review-queue.csv` — unresolved terms grouped with affected recipe IDs and titles.
- `docs/` — site use, accessibility, build, and data-status documentation.

## Build and verify

```powershell
python tools/build_edition.py
node check-edition.mjs
node check-caching.mjs
```

The build requires the existing R5 SQLite registry at `D:\Projects\Online\recipes\generated\backups\live-20261027-r5-descriptions.sqlite`. The source dataset is never modified by the build.

## Publishing

Push a verified change to `main`. The GitHub Actions workflow uploads `dist/` and deploys it to GitHub Pages. It does not interact with or modify `recipes.slopcopy.com`.

See [site guide](docs/site-guide.md) and [data pipeline](docs/data-pipeline.md) for details.
