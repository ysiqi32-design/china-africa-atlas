const fs=require('fs'),vm=require('vm'),assert=require('assert');const js=fs.readFileSync(require('path').join(__dirname,'..','upload.js'),'utf8');
const ctx={console,window:{crypto:{randomUUID:()=> 'test-id'}},URL,Date,Math,Number,String,Array,Map,Set,Intl,Blob,TextDecoder,TextEncoder,Promise,NaN,localStorage:{},COUNTRIES:[{code:'GIN',zh:'几内亚',en:'Guinea'},{code:'SEN',zh:'塞内加尔',en:'Senegal'}],MODULES:[{id:'base',name:'01 国家基本面',short:'国家基本面'},{id:'trade',name:'02 双边贸易',short:'双边贸易'},{id:'resources',name:'03 资源',short:'资源'}]};vm.createContext(ctx);vm.runInContext(js,ctx);
const rows=vm.runInContext("localParseCsv('country,module,title,year,value,unit\\nGIN,resources,\\\"铝土矿,资源\\\",2024,12.5,万吨\\n')",ctx);assert.equal(rows.length,1);assert.equal(rows[0].title,'铝土矿,资源');
const v=vm.runInContext("localNormalize({country:'GIN',module:'resources',title:'铝土矿',year:'2024',value:'1,234',unit:'万吨'},'stat',{})",ctx);assert.equal(v.value,1234);assert.equal(v.country,'GIN');
const c=vm.runInContext("localNormalize({country:'SEN',module:'trade',title:'监管政策',date:'2025-02-02',source_url:'https://example.com'},'event',{})",ctx);assert.equal(c.date,'2025-02-02');
let bad=false;try{vm.runInContext("localNormalize({country:'SEN',module:'trade',title:'X',date:'2025-02-02',source_url:'javascript:alert(1)'},'event',{})",ctx)}catch(e){bad=true}assert.ok(bad);
assert.equal(vm.runInContext("localEsc('<img src=x>')",ctx),'&lt;img src=x&gt;');
console.log('PASS: CSV quoted field / numeric parsing / country-module validation / URL rejection / HTML escape');
