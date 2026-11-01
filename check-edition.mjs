import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
const root=path.resolve('dist/data'),edition=JSON.parse(fs.readFileSync(path.join(root,'edition.json'),'utf8')),data=JSON.parse(fs.readFileSync(path.join(root,'recipes.json'),'utf8'));
assert.equal(data.schema_version,3);assert.equal(edition.schema_version,3);assert.ok(!data.preview&&!edition.preview,'Preview data must not be published');assert.equal(data.recipes.length,708);assert.equal(edition.recipes,708);assert.equal(new Set(data.recipes.map(r=>r.id)).size,708);
const allowed=new Set(['id','slug','title','description','collection','language_code','content_kind','translations','ingredient_search_terms','yield','prep_time','cook_time','total_time','servings','ingredients','steps','categories','instructions','notes','originals','photos','source_id','source','canonical_ingredient_ids']);
for(const r of data.recipes){
 for(const key of Object.keys(r))assert.ok(allowed.has(key),'Unexpected public field '+key);
 assert.ok(r.collection.slug&&r.collection.name&&r.language_code);
 assert.ok(typeof r.description==='string'&&r.description.trim(),'Missing native-language description');assert.match(r.description,/^A .+\.$/,'Catalog description must be a concise menu-style sentence');assert.ok(!r.description.includes('recipe featuring'),'Catalog description must not be an ingredient list');assert.ok(r.description.length<=140,'Catalog description must remain concise');
 assert.ok(['en','pt'].includes(r.language_code),'Unexpected native language');
 for(const t of Object.values(r.translations)){assert.equal(t.ingredients.length,r.ingredients.length);assert.equal(t.steps.length,r.steps.length);assert.ok(t.title&&typeof t.instructions==='string'&&typeof t.description==='string'&&t.description.trim());for(const text of [...t.ingredients,...t.steps])assert.ok(typeof text==='string'&&text.trim());}
 for(const o of r.originals){assert.ok(!/[\\/]/.test(o.document_name),'Source name exposes a path');assert.ok(o.text);if(o.source_kind!=='transcription')assert.ok(o.locator);}
}
assert.ok(data.recipes.every(r=>r.source_id&&r.source?.publication==='Cook Book'&&Array.isArray(r.canonical_ingredient_ids)),'Source and canonical metadata must be retained');
for(const [name,expected]of Object.entries(edition.files)){const file=path.resolve(root,name);assert.ok(file.startsWith(root+path.sep));assert.equal(crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'),expected);}
console.log('Verified 708 Mayflower entries, stable IDs, source metadata, public allowlist and checksums.');
