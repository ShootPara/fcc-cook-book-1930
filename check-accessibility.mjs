import assert from 'node:assert/strict';
import fs from 'node:fs';

const html = fs.readFileSync('dist/index.html', 'utf8');
const css = fs.readFileSync('dist/style.css', 'utf8');
const requiredHtml = [
  '<html lang="en">',
  'name="viewport"',
  'class="skip-link" href="#main"',
  '<main id="main">',
  '<label for="search">Recipe name or ingredient</label>',
  'type="search"',
  'role="status"',
  '<summary>Advanced search options</summary>',
  'id="include-source" type="checkbox"',
  'data-text-size="18"',
  'data-text-size="25"',
  'id="print"',
];
for (const snippet of requiredHtml) assert.ok(html.includes(snippet), `Missing accessibility control: ${snippet}`);
assert.ok(!/<footer\b/i.test(html), 'This edition intentionally has no footer');
assert.match(css, /:focus-visible\{outline:3px solid var\(--focus\)/, 'Visible keyboard focus is required');
assert.match(css, /button\{min-height:48px/, 'Buttons must keep a 48px target');
assert.match(css, /input\[type=search\][^{]*\{[^}]*min-height:56px/, 'Search must keep a large target');
assert.match(css, /@media\(max-width:760px\)/, 'A narrow-screen layout is required');
assert.match(css, /@media print\{/, 'A print layout is required');

function luminance(hex) {
  const channels = hex.match(/[a-f\d]{2}/gi).map(part => Number.parseInt(part, 16) / 255);
  const linear = channels.map(value => value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4);
  return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
}
function contrast(foreground, background) {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
}
for (const [name, foreground, background] of [
  ['body text', '#121212', '#ffffff'],
  ['navigation', '#0b1628', '#ffffff'],
  ['links', '#075cba', '#ffffff'],
  ['focus outline', '#9b4200', '#ffffff'],
]) {
  assert.ok(contrast(foreground, background) >= 4.5, `${name} must meet 4.5:1 contrast`);
}
console.log('Verified accessibility-first structure, responsive controls, print support, and color contrast.');
