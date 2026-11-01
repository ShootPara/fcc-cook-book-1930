import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';

const sourcePath = path.resolve('source/mayflower-recipes-v8-edited.json');
const reportPath = path.resolve('reports/canonical-ingredient-matches.json');
const source = JSON.parse(fs.readFileSync(sourcePath, 'utf8'));
const report = JSON.parse(fs.readFileSync(reportPath, 'utf8'));
const recipes = new Map(source.recipes.map(recipe => [recipe.id, recipe]));
const expectedLines = source.recipes.reduce((total, recipe) => total + recipe.ingredients.length, 0);

assert.equal(source.recipes.length, 708, 'Expected the immutable V8 source');
assert.equal(report.source, path.basename(sourcePath), 'Report source must name V8');
assert.equal(report.matches.length, expectedLines, 'Every source ingredient line needs one report row');

const summary = {};
const reviewSummary = {};
for (const row of report.matches) {
  const recipe = recipes.get(row.recipe_id);
  assert.ok(recipe, `Unknown source recipe ${row.recipe_id}`);
  assert.equal(row.recipe_title, recipe.title, `Title mismatch for ${row.recipe_id}`);
  assert.ok(recipe.ingredients.includes(row.display_text), `Unknown ingredient line for ${row.recipe_id}`);
  assert.ok(typeof row.match_kind === 'string' && row.match_kind, 'Missing match kind');
  summary[row.match_kind] = (summary[row.match_kind] ?? 0) + 1;

  if (row.match_kind === 'unmatched') {
    assert.ok(typeof row.review_class === 'string' && row.review_class, 'Unmatched line needs a review class');
    reviewSummary[row.review_class] = (reviewSummary[row.review_class] ?? 0) + 1;
  } else {
    assert.ok(Number.isInteger(row.ingredient_id) && row.ingredient_id > 0, 'Matched line needs a canonical ID');
    assert.ok(typeof row.canonical_name === 'string' && row.canonical_name, 'Matched line needs a canonical name');
  }
}

assert.deepEqual(report.summary, summary, 'Match summary must be derived from report rows');
assert.deepEqual(report.review_summary, reviewSummary, 'Review summary must be derived from unmatched rows');
assert.equal(reviewSummary.unresolved_food_identity ?? 0, 0, 'No unresolved food identities may be published');
console.log(`Verified ${expectedLines} ingredient lines; no unresolved food identities remain.`);
