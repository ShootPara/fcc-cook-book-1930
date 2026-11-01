import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const source=fs.readFileSync('dist/app.js','utf8');
const loader=source.slice(source.indexOf('async function loadRecipeEdition(){'),source.indexOf('(async()=>{try{edition=await loadRecipeEdition();'));
assert.ok(loader.startsWith('async function loadRecipeEdition(){'));
const hashes=['a'.repeat(64),'b'.repeat(64)];
const requests=[];
let currentHash=hashes[0],manifestOK=true,dataOK=true;
const context=vm.createContext({fetch:async(url,options)=>{
 requests.push({url,cache:options.cache});
 if(url==='data/edition.json')return {ok:manifestOK,json:async()=>({files:{'recipes.json':currentHash}})};
 return {ok:dataOK,json:async()=>({recipes:[{id:1}]})};
}});
vm.runInContext(loader,context);
for(const hash of [hashes[0],hashes[0],hashes[1]]){
 currentHash=hash;
 const data=await context.loadRecipeEdition();
 assert.equal(data.recipes[0].id,1);
 assert.deepEqual(requests.at(-2),{url:'data/edition.json',cache:'no-cache'});
 assert.deepEqual(requests.at(-1),{url:'data/recipes.json?v='+hash,cache:'force-cache'});
}
assert.equal(requests[1].url,requests[3].url,'Unchanged editions reuse the same cache key');
assert.notEqual(requests[3].url,requests[5].url,'Changed editions use a new cache key');
currentHash='invalid';
await assert.rejects(()=>context.loadRecipeEdition(),/could not be loaded/);
currentHash=hashes[0];manifestOK=false;
await assert.rejects(()=>context.loadRecipeEdition(),/could not be loaded/);
manifestOK=true;dataOK=false;
await assert.rejects(()=>context.loadRecipeEdition(),/could not be loaded/);
console.log('Verified manifest revalidation, stable and changed cache keys, and loading failures.');
