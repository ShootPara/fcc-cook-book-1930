import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const nodes = new Map();
let focused = null;
class Element {
  constructor(tag = '') { this.tag = tag; this.children = []; this.value = ''; this.checked = false; this.hidden = false; this.textContent = ''; }
  append(...items) { this.children.push(...items); }
  replaceChildren(...items) { this.children = items; }
  addEventListener() {}
  scrollIntoView() {}
  focus() { focused = this; }
}
const get = id => { if (!nodes.has(id)) nodes.set(id, new Element()); return nodes.get(id); };
const document = { getElementById: get, createElement: tag => new Element(tag), createTextNode: text => ({ textContent: text }), querySelectorAll: () => [] };
const data = JSON.parse(fs.readFileSync('dist/data/recipes.json', 'utf8'));
const context = vm.createContext({ document, location: { hash: '' }, window: { addEventListener() {}, scrollTo() {} }, fetch: async url => ({ ok: true, json: async () => url.includes('edition.json') ? { files: { 'recipes.json': 'a'.repeat(64) } } : data }) });
vm.runInContext(fs.readFileSync('dist/app.js', 'utf8'), context);
await new Promise(resolve => setImmediate(resolve));
assert.equal(get('cards').children.length, 24);
assert.equal(get('result-count').textContent, 'Showing 24 of 708 recipes');
const buttons = get('catalog-groups').children.flatMap(section => section.children[1].children.map(li => li.children[0]));
const chapters = new Set(data.recipes.flatMap(r => r.categories));
assert.equal(buttons.length, chapters.size);
assert.deepEqual(new Set(buttons.map(b => b.children[0].textContent)), chapters);

// Every recipe must become reachable, without duplicates, through Show more.
while (!get('show-more').hidden) get('show-more').onclick();
assert.equal(get('cards').children.length, 708);
assert.equal(new Set(get('cards').children.map(card => card.href)).size, 708);
assert.equal(focused, get('cards').children[696]);
assert.equal(get('result-count').textContent, 'Showing 708 of 708 recipes');

// Chapter changes reset the limit; the final partial page is available.
buttons.find(b => b.children[0].textContent === 'Cakes With Butter').onclick();
assert.equal(get('cards').children.length, 24);
get('show-more').onclick();
assert.equal(get('cards').children.length, 48);
assert.equal(focused, get('cards').children[24]);
get('show-more').onclick();
assert.equal(get('cards').children.length, 71);
assert.equal(get('show-more').hidden, true);

// Narrow searches and empty results reset correctly, too.
get('search').value = 'xyz-no-such-recipe';
vm.runInContext('search()', context);
assert.equal(get('result-count').textContent, 'Showing 0 of 0 recipes');
assert.equal(get('show-more').hidden, true);
get('search').value = '';
get('chapter').value = '';
vm.runInContext('search()', context);
assert.equal(get('cards').children.length, 24);
assert.equal(get('show-more').hidden, false);
console.log('Verified all 31 catalog chapters, access to all 708 recipes, partial pages, focus, and filter resets.');

vm.runInContext('showRecipe(all[0])', context);
const detail = get('recipe-content').children;
assert.equal(detail[0].className, 'print-heading');
assert.equal(detail[0].children[0].textContent, 'Mayflower Guild Cook Book (1930)');
const citation = detail.find(node => node.className === 'book-citation');
assert.ok(citation.children[0].textContent.includes('Dalm Printing Co., 1930'));
assert.equal(citation.children[1].href, 'https://babel.hathitrust.org/cgi/pt?id=nyp.33433038851568');
assert.equal(citation.children[2].textContent, citation.children[1].href);
console.log('Verified cookbook print heading, bibliographic citation, and printable source URL.');
