# Data pipeline and editorial status

## Editorial authority

`source/mayflower-recipes-v8-edited.json` is the canonical structured source. It contains the completed edited cookbook and must not be modified by website-generation work. Its companion Markdown file is a readable edition of the same material.

The historical PDF is the underlying record. The published site intentionally presents the corrected Version 8 editorial edition rather than recreating known OCR or printing errors.

## Build output

`python tools/build_edition.py` converts Version 8 into these generated artifacts:

- `dist/data/recipes.json` — frontend-readable recipe edition with stable numeric IDs;
- `dist/data/edition.json` — record count and SHA-256 manifest;
- `reports/canonical-ingredient-matches.json` — ingredient match evidence.

The public recipe records retain their historical Mayflower source ID and source metadata alongside the frontend ID. The browser consumes only JSON; there is no runtime database, server API, or editor.

## Ingredient normalization

The builder reads the established Recipe Box R5 SQLite registry:

- `ingredients_canonical`
- `ingredient_aliases`
- `ingredient_canonical_redirects`

It preserves every Version 8 display line, derives search terms from valid registry matches, follows redirects, and records the assigned canonical IDs in the generated data. Registry aliases and Mayflower ingredient parsing now use the same normalization rule, preventing separator differences such as `baking powder` versus `baking-powder` from hiding valid matches. A small, reviewed historical-alias list handles terms with an unambiguous culinary meaning—for example, historical `soda` maps to the R5 baking-soda identity and `gelatine` to the generic gelatin identity.

`config/mayflower-ingredient-extensions.json` is the separate, version-controlled registry for unmistakable Mayflower ingredients absent from R5. It assigns stable IDs above the R5 range and records English, Portuguese, and historical aliases. It never overwrites an existing R5 term and never changes the R5 SQLite file.

The build also emits `reports/ingredient-review-queue.csv`. It groups each unresolved display line by review class and includes every affected source ID and title. Obvious section headings and stray numeric fragments are classified separately; unresolved food identities remain visible for editorial review.

The latest generated report resolves 3,380 ingredient lines through R5 aliases, 126 through explicit historical aliases, and 924 through the Mayflower extension registry. The remaining 266 lines are intentionally marked unmatched rather than silently forced into potentially incorrect canonical identities. Most require either a reviewed historical alias or a genuinely new canonical term. The report is the review queue.

## Validation

Run both checks after every build:

```powershell
node check-edition.mjs
node check-caching.mjs
```

The first validates the 708-record edition, unique numeric IDs, retained source metadata, schema allowlist, and manifest checksum. The second validates the browser’s manifest-first caching behavior.

## Remaining publication work

1. Review the unmatched historical ingredient terms and approve only defensible R5 aliases or new canonical identities.
2. Generate and review Portuguese derived content while leaving Version 8 English source untouched.
3. Add any desired historical images or cover artwork as static site assets.

None of these tasks requires a runtime database or changes to the existing Recipe Box deployment.
