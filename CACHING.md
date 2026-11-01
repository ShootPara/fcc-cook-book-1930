# Recipe download caching

The page revalidates `/data/edition.json` on each visit using `cache: 'no-cache'`.
It fetches `/data/recipes.json?v=<sha256>` using `cache: 'force-cache'`, allowing
the browser to reuse even a stale HTTP cache entry for that exact version.
The host's existing ETag headers support revalidation of the small manifest.

When publishing recipe edits, update `edition.json`'s `files["recipes.json"]`
to the SHA-256 of the exact published recipe file, as required by the existing
edition check. Publish both files together. A changed hash makes the browser
download the new edition. Do not change recipe bytes without updating the hash.

Browsers may evict cached data or disable caching; those visitors download again.
This change does not provide offline support.

Verification: `node check-caching.mjs` and `node check-edition.mjs`.
