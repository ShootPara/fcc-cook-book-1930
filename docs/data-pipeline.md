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

The build also emits `reports/ingredient-review-queue.csv`. It groups each unresolved display line by review class and includes every affected source ID and title. The queue separates unresolved food identities from underspecified ingredients, proprietary references, textual fragments, structural headings, and stray numeric fragments, so only defensible canonical additions reach the registry.

`check-ingredient-matches.mjs` is the regression guard for that process. It verifies that every source ingredient line has a report row, report totals are derived correctly, matched lines retain canonical IDs, and no unresolved food identity is published.

The latest generated report resolves 3,410 ingredient lines through R5 aliases, 129 through explicit historical aliases, and 1,036 through the Mayflower extension registry. The remaining 121 lines are intentionally marked unmatched rather than silently forced into potentially incorrect canonical identities. No unresolved food identities remain: every outstanding entry is classified as underspecified, proprietary, fragmentary, a prepared component, a structural heading, or a numeric artifact. The report is the review queue.

## Validation

Run all checks after every build:

```powershell
node check-edition.mjs
node check-caching.mjs
node check-ingredient-matches.mjs
node check-accessibility.mjs
```

These validate the 708-record edition, unique numeric IDs, retained source metadata, schema allowlist, manifest checksum, browser caching behavior, ingredient-match coverage, and the accessibility-first catalog controls.

## Remaining publication work

1. Optionally review the documented underspecified, proprietary, fragmentary, prepared-component, heading, and numeric entries; no unresolved food identity remains.
2. Generate and review Portuguese derived content while leaving Version 8 English source untouched.
3. Add any desired historical images or cover artwork as static site assets.

None of these tasks requires a runtime database or changes to the existing Recipe Box deployment.
