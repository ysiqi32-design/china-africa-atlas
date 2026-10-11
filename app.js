/* China–Africa Atlas: research-oriented interactive front end; no fake statistics.
   Dynamic WDI values are fetched only from public World Bank API.
   Curated events/projects and UN Comtrade trade are rendered from traceable normalized snapshots; missing values remain missing. */
'use strict';
const $=id=>document.getElementById(id);
function readNote(key){try{return localStorage.getItem(key)||''}catch(e){return ''}}
function writeNote(key,value){try{localStorage.setItem(key,value);return true}catch(e){return false}}
const COUNTRIES=window.ATLAS_MAP_DATA.filter(x=>!x.special), MAP_DATA=window.ATLAS_MAP_DATA;
const FOCUS=new Set(['GIN','COD','MLI','NER','SEN','CIV','DZA','EGY','ZAF','NGA','AGO','ZMB','CMR','TCD','ETH']);
const INDICATORS=[
 ['SP.POP.TOTL','人口总量','people','基础面'],['NY.GDP.MKTP.CD','GDP（现价美元）','usd','基础面'],['NY.GDP.PCAP.CD','人均GDP','usd','基础面'],['NY.GDP.MKTP.KD.ZG','GDP增长率','pct','基础面'],
 ['FP.CPI.TOTL.ZG','消费者价格通胀','pct','基础面'],['SL.UEM.TOTL.ZS','失业率（ILO估计）','pct','社会'],['SP.POP.0014.TO.ZS','0–14岁人口比重','pct','社会'],['SE.SEC.ENRR','中学总入学率','pct','社会'],
 ['NV.IND.MANF.ZS','制造业增加值 / GDP','pct','产业'],['NV.AGR.TOTL.ZS','农业增加值 / GDP','pct','产业'],['NV.SRV.TOTL.ZS','服务业增加值 / GDP','pct','产业'],
 ['NE.TRD.GNFS.ZS','货物及服务贸易 / GDP','pct','贸易'],['BX.KLT.DINV.CD.WD','FDI净流入（美元）','usd','投资'],['GC.DOD.TOTL.GD.ZS','中央政府债务 / GDP','pct','融资'],
 ['EG.ELC.ACCS.ZS','电力可及率','pct','基础设施'],['IT.NET.USER.ZS','互联网使用人口比重','pct','数字']
];
const I_BY_CODE=Object.fromEntries(INDICATORS.map(x=>[x[0],x]));
const SRC={
 wb:['世界银行 World Development Indicators','https://data.worldbank.org/'],
 wbapi:['World Bank Indicators API','https://datahelpdesk.worldbank.org/knowledgebase/articles/889392'],
 comtrade:['UN Comtrade 联合国商品贸易','https://comtradeplus.un.org/'],
 imf:['IMF 经济数据与国际金融统计','https://data.imf.org/'],
 wits:['WITS 关税与贸易数据','https://wits.worldbank.org/'],
 mofcom:['中国商务部','https://www.mofcom.gov.cn/'],
 cais:['SAIS-CARI 中非关系数据','https://www.sais-cari.org/data'],
 bu:['波士顿大学中国对非贷款','https://www.bu.edu/gdp/chinese-loans-to-africa-database-data-download/'],
 aid:['AidData 全球中国项目','https://china.aiddata.org/'],
 ids:['世界银行国际债务统计','https://www.worldbank.org/en/programs/debt-statistics/ids'],
 eiti:['EITI 采掘业透明度报告','https://eiti.org/eiti-reporting'],
 usgs:['USGS 矿产资料','https://www.usgs.gov/centers/national-minerals-information-center'],
 unctad:['UNCTAD 投资与发展','https://unctadstat.unctad.org/'],
 unido:['UNIDO 工业统计','https://stat.unido.org/'],
 fco:['中非合作论坛','https://www.focac.org/'],
 fa:['中国外交部','https://www.fmprc.gov.cn/'],
 sipri:['SIPRI 武器转让数据库','https://www.sipri.org/databases/armstransfers'],
 unv:['联合国维和行动','https://peacekeeping.un.org/en/troop-and-police-contributors'],
 unvote:['联合国数字图书馆投票资料','https://digitallibrary.un.org/'],
 unicef:['UNESCO教育统计（UIS）','https://uis.unesco.org/'],
 afro:['Afrobarometer 民调数据库','https://www.afrobarometer.org/'],
 acled:['ACLED 事件数据','https://acleddata.com/conflict-data'],
 dfi:['中国人民银行','https://www.pbc.gov.cn/'],
 ne:['Natural Earth 地图来源','https://www.naturalearthdata.com/']
};
const MODULES=[
 {id:'base',name:'01 国家基本面',short:'国家基本面',desc:'人口、发展水平、经济结构、财政与区域制度背景。',questions:['人口规模与青年结构','GDP与人均GDP','经济增长、通胀与失业','制造业 / 农业 / 服务业结构','财政债务与发展需求','区域经济组织与货币制度'],source:['wb','imf','unctad'],wdi:['SP.POP.TOTL','NY.GDP.MKTP.CD','NY.GDP.PCAP.CD','NY.GDP.MKTP.KD.ZG','FP.CPI.TOTL.ZG']},
 {id:'diplomacy',name:'02 双边外交',short:'外交与政治关系',desc:'建交历史、双边伙伴关系、元首互访、重大协议和对华政策。',questions:['建交日期与外交关系变更','高层互访及政策重点','双边关系官方定位','中非合作论坛实施情况','“一带一路”相关安排','东道国的对华政策'],source:['fa','fco'],wdi:[]},
 {id:'trade',name:'03 双边贸易',short:'双边贸易',desc:'中非商品流量、贸易差额、商品结构、双向市场依赖与关税政策。',questions:['中国对该国出口 / 自该国进口','进出口商品结构 HS2/4/6','中国在该国进口与出口中的份额','该国对中国关键商品供应贡献','贸易差额及10年以上趋势','关税、市场准入及非关税壁垒'],source:['comtrade','wits','cais'],wdi:['NE.TRD.GNFS.ZS']},
 {id:'investment',name:'04 直接投资',short:'投资与企业',desc:'区分中国FDI流量、存量、绿地投资、收并购及企业层面的权益。',questions:['对华直接投资流量 / 存量','中国在东道国外资中的份额','主要中资企业与经营行业','股权与项目控制权','本地就业和采购','利润汇出、纳税及撤资风险'],source:['mofcom','unctad','cais'],wdi:['BX.KLT.DINV.CD.WD']},
 {id:'financing',name:'05 债务与融资',short:'债务与发展融资',desc:'贷款承诺、拨付、余额、偿还、债务重组与不同债权人结构。',questions:['中国官方贷款承诺与实际拨付','中国债权占政府外债比例','未偿债务及本息偿还','贷款利率与担保安排','援助 / 优惠贷款 / 商业贷款区分','债务重组与其他债权方'],source:['bu','ids','aid','imf'],wdi:['GC.DOD.TOTL.GD.ZS']},
 {id:'projects',name:'06 基础设施',short:'工程与基础设施',desc:'项目的融资、施工、所有权、运营权和投产绩效需要分别衡量。',questions:['中国企业工程承包营业额','新签工程合同与在建规模','重大港口 / 铁路 / 电力项目','融资与项目所有权','运营管理权及维护责任','工程就业、本地采购及利用率'],source:['cais','aid','wb'],wdi:['EG.ELC.ACCS.ZS']},
 {id:'resources',name:'07 能源与资源',short:'能源资源供应链',desc:'从资源储量到中国进口依赖、矿权结构及东道国资源政策。',questions:['矿产储量、实际产量、出口','中国该资源进口依赖份额','中资企业矿权 / 油气资产','出口配额、税费及许可','资源收益与国有化政策','替代供应国与战略安全'],source:['usgs','eiti','comtrade'],wdi:[]},
 {id:'industry',name:'08 产业合作',short:'工业化与技术',desc:'产业园区、制造业本土化、本地加工、技能培训和产业价值链。',questions:['中资制造业项目与产能','制造业增加值占GDP比重','本地原料加工与工业园区','技术培训、研发和工人技能','产业本地采购率','中国制成品与本土产业竞争'],source:['unido','wb','unctad'],wdi:['NV.IND.MANF.ZS','NV.AGR.TOTL.ZS']},
 {id:'payments',name:'09 金融支付',short:'金融与人民币合作',desc:'本币清算、跨境支付、商业银行布局与实际融资币种。',questions:['本币互换协定及规模','人民币清算机构与CIPS接入','实际人民币结算规模','在非中资商业银行业务','熊猫债与人民币融资','合同支付及外汇限制'],source:['dfi','imf'],wdi:[]},
 {id:'security',name:'10 安全合作',short:'军事与安全',desc:'联合国维和、军事培训、主要常规武器转让以及涉华项目风险。',questions:['国防高层交往及相关协议','中国军售（SIPRI TIV口径）','联合训练和反恐合作','联合国维和人员贡献','中国企业项目安全','武装冲突和政变风险'],source:['sipri','unv','acled'],wdi:[]},
 {id:'multilateral',name:'11 多边外交',short:'多边制度合作',desc:'联合国议题立场、非盟及地区合作机制、全球治理倡议。',questions:['联合国大会重点议题投票','人权理事会相关立场','WTO与气候融资谈判','中非合作论坛行动落实','非盟与地区组织成员关系','全球南方倡议与实际项目'],source:['unvote','fco','fa'],wdi:[]},
 {id:'society',name:'12 社会交流',short:'教育与人文交流',desc:'留学、人员迁移、医疗教育、学术和社区网络联系。',questions:['赴华留学人数及奖学金','职业培训与技术技能交流','孔子学院 / 中文教育','中国在非企业雇员与本地人员','移民、商人及侨民网络','医疗、教育和科研合作'],source:['unicef','cais','fco'],wdi:['SE.SEC.ENRR']},
 {id:'opinion',name:'13 公众与风险',short:'社会认知与政治风险',desc:'区分总体民调、青年态度、政府立场、具体抗议和企业争议。',questions:['对华经济政治影响的正负面评价','不同年龄 / 城乡 / 教育组态度','针对中资企业的劳资和环保争议','涉华抗议与政策处罚事件','企业与政府回应及事件后果','信息环境与数据偏差'],source:['afro','acled'],wdi:['SL.UEM.TOTL.ZS']},
 {id:'external',name:'14 外部关系',short:'其他外部伙伴',desc:'在东道国对外关系结构中定位中国，而非预设大国竞争。',questions:['前五大进口 / 出口伙伴','主要外资来源国及债权人','外部安全伙伴','区域贸易及货币制度','与欧美、中东、印度等伙伴合作','国际金融组织改革项目'],source:['comtrade','imf','unctad','wits'],wdi:[]}
];
const COUNTRY_LEADS={
 GIN:'铝土矿出口与本地氧化铝精炼政策；西芒杜铁矿—铁路—港口产业链；中国矿产原料供应集中度。',
 COD:'铜钴矿项目、钴出口配额及上游矿产政策；研究中国冶炼产业链与东道国市场权力。',
 NER:'石油项目的本地就业要求、政府与外国投资者谈判，以及安全局势对合作的影响。',
 MLI:'矿业法修订、国家股权安排及锂矿项目；区分主权主义政治叙事与合同的实际变化。',
 SEN:'2024年政权更替后的产业发展政策；对华商品贸易与本地商业利益；FRAPP社会运动和公众调查。',
 CIV:'农产品出口、对华市场准入、城市基础设施与西非区域商业网络。',
 DZA:'长期工程建设项目、能源工业和大型制造业合作；区分工程收入与直接投资。',
 AGO:'石油产业、对华出口、债务及基础设施融资模式的变化。',
 ZAF:'制造业、电力与清洁能源产业、贸易结构以及金砖多边合作。',
 NGA:'人口与大型市场、制造业进口、基础设施项目和西非区域商业联系。',
 EGY:'工业园区、苏伊士经济区和基础设施项目；制造业价值链与区域贸易。',
 ZMB:'铜矿、跨境物流与电力供应链；中国投资和本地增值。',
 CMR:'中非地区基础设施、贸易与区域市场；发展融资与政府财政约束。',
 ETH:'产业园区、工业制造业、铁路与融资；比较项目运行和长期产业效果。',
 TCD:'区域安全、石油、财政和政治环境的动态变化。'
};
const DATA={}; // country ISO3 -> indicator code -> [{year,value}]
const ATLAS_BUNDLE=window.ATLAS_DATA_BUNDLE||{};
const STORE={
  trade:ATLAS_BUNDLE.trade||{countries:{}},
  records:ATLAS_BUNDLE.records||{records:[]},
};
for (const moduleId of ['investment','financing','engineering','resources','industry','payments','security','multilateral','society','surveys','external','diplomacy']) {
  STORE[moduleId]=ATLAS_BUNDLE[moduleId]||{countries:{}};
}
function recordsFor(iso,mod){return (STORE.records.records||[]).filter(r=>r.country===iso&&r.modules?.includes(mod)).sort((a,b)=>b.date.localeCompare(a.date));}
function tradeRows(iso=selected){return (STORE.trade.countries?.[iso]||[]).slice().sort((a,b)=>b.year-a.year)}
function latestTrade(iso=selected){return tradeRows(iso).find(r=>typeof r.china_exports_usd==='number'&&typeof r.china_imports_usd==='number')||null;}
function usdFmt(v){if(typeof v!=='number'||!Number.isFinite(v))return '未发布';return new Intl.NumberFormat('zh-CN',{style:'currency',currency:'USD',maximumFractionDigits:0}).format(v)}
function checkedUrl(v){try{const u=new URL(v);return ['https:','http:'].includes(u.protocol)?escapeHTML(u.href):'#'}catch{return '#'}}
function tradeCard(iso){let r=latestTrade(iso);return r?`<div class="trade-summary"><div class="data-status status-ready">${r.year}年 · 已入库 · 中国报告口径</div><div class="trade-values"><div><small>中国出口至${country(iso).zh}</small><strong>${usdFmt(r.china_exports_usd)}</strong></div><div><small>中国自${country(iso).zh}进口</small><strong>${usdFmt(r.china_imports_usd)}</strong></div><div><small>中国贸易顺差（负数为逆差）</small><strong>${usdFmt(r.china_exports_usd-r.china_imports_usd)}</strong></div></div><p class="data-caption">UN Comtrade · 统计年 ${r.year} · 统一使用中国报告国口径。贸易顺差方向为中国视角，不能与该国自己发布的数额混用。数据采集时间：${escapeHTML(STORE.trade.updated_at_utc||'未记录')}</p><a class="source-provenance" href="${checkedUrl(STORE.trade.source_url||'https://comtradeplus.un.org/')}" target="_blank" rel="noopener noreferrer">查看UN Comtrade 原始数据库 ↗</a></div>`:`<div class="data-empty"><strong>对华双边贸易尚未入库</strong><span>已准备UN Comtrade批量采集程序。待GitHub定时任务成功获取，才会显示各国真实的进出口、差额和历史趋势；这不是零贸易额。</span><a href="https://comtradeplus.un.org/" target="_blank" rel="noopener noreferrer">查询原始贸易数据 ↗</a></div>`}
function tradeTrend(iso=selected){const rows=tradeRows(iso).filter(r=>typeof r.china_exports_usd==='number'&&typeof r.china_imports_usd==='number').slice(0,12).reverse();if(rows.length<2)return '';
 const both=rows.flatMap(r=>[r.china_exports_usd,r.china_imports_usd]);const ymax=Math.max(1,...both)*1.1;const W=540,H=135,x=i=>28+i*(W/(rows.length-1)),y=v=>H-(v/ymax)*(H-30);
 const line=key=>rows.map((r,i)=>`${i?'L':'M'} ${x(i).toFixed(1)} ${y(r[key]).toFixed(1)}`).join(' ');
 const pts=key=>rows.map((r,i)=>`<circle cx="${x(i)}" cy="${y(r[key])}" r="3"><title>${r.year}: ${usdFmt(r[key])}</title></circle>`).join('');
 return `<div class="mod-mini-header">年度贸易趋势 · 单位美元 · 中国报告口径</div><div class="trade-legend"><span>● 中国向该国出口</span><span>● 中国从该国进口</span></div><svg viewBox="0 0 600 160" class="trade-chart" aria-label="双边贸易年度变化"><line x1="28" y1="135" x2="569" y2="135" stroke="#d4e4e1"/><path d="${line('china_exports_usd')}" fill="none" stroke="#128b87" stroke-width="2.8"/> <path d="${line('china_imports_usd')}" fill="none" stroke="#c89a4a" stroke-width="2.8"/><g fill="#128b87">${pts('china_exports_usd')}</g><g fill="#c89a4a">${pts('china_imports_usd')}</g><text x="28" y="153" fill="#799592" font-size="11">${rows[0].year}</text><text x="568" y="153" fill="#799592" font-size="11" text-anchor="end">${rows.at(-1).year}</text></svg>`;
}
function datasetTable(mod,iso){const dataKey=({projects:'engineering',opinion:'surveys'})[mod]||mod;const db=STORE[dataKey];const rows=db?.countries?.[iso]||[];
 if (!rows.length)return '';
 return `<div class="mod-mini-header">专题数据库记录 · ${rows.length} 条</div><div class="research-records">${rows.slice(0,40).map(r=>{const name=escapeHTML(r.label||r.indicator||r.title||'未命名');const val=r.value===null||r.value===undefined?'未公布':typeof r.value==='number'?numberFormatter.format(r.value):escapeHTML(r.value);return `<div class="research-record"><div class="record-title">${name}</div><div><strong>${val}</strong> ${escapeHTML(r.unit||'')} · ${escapeHTML(r.year||r.date||'年份未公布')}</div><small>${escapeHTML(r.source_name||db.source||'来源待核')} · ${escapeHTML(r.status||'资料待复核')}</small>${r.source_url?`<a href="${checkedUrl(r.source_url)}" target="_blank" rel="noopener noreferrer">来源 ↗</a>`:''}</div>`}).join('')}</div>`;
}
function verifiedRecords(mod,iso){const events=recordsFor(iso,mod);if(!events.length)return '';
 return `<div class="mod-mini-header">已有来源的国别项目 / 政策事件 · ${events.length} 条</div><div class="research-records">${events.map(r=>`<div class="research-record"><div class="record-meta">${escapeHTML(r.date)} · ${escapeHTML(r.type)} · ${escapeHTML(r.verification)}</div><div class="record-title">${escapeHTML(r.title)}</div><p>${escapeHTML(r.summary)}</p><a href="${checkedUrl(r.source_url)}" target="_blank" rel="noopener noreferrer">原始出处：${escapeHTML(r.source_name)} ↗</a></div>`).join('')}</div>`;
}
function moduleDataBlock(m){
 const has=recordsFor(selected,m.id).length+(STORE[({projects:'engineering',opinion:'surveys'})[m.id]||m.id]?.countries?.[selected]?.length||0);
 let content='';if(m.id==='trade')content+=tradeCard(selected)+tradeTrend(selected);
 content+=datasetTable(m.id,selected)+verifiedRecords(m.id,selected);
 if (!has&&m.id!=='trade')content+=`<div class="data-empty"><strong>本国此维度暂无核验后入库的专门资料</strong><span>已建立数据字段与来源入口；待数据导入或事件核验。缺失不代表数值为0，也不能据此断定不存在合作。</span></div>`;
 if (m.id==='trade'&&!has)content+=`<div class="data-caption">对华贸易须从UN Comtrade获取，不使用WDI的“总贸易占GDP比重”代替。</div>`;
 return content;
}

let SNAPSHOT=(ATLAS_BUNDLE.worldbank_snapshot?.countries||null),selected='GIN',activeFilter='all',selectedModule='base',activeZoom=1,second='SEN',compareOpen=false,loadingToken=0;
const numberFormatter=new Intl.NumberFormat('zh-CN',{maximumFractionDigits:1});
function format(v,type){if(typeof v!=='number'||!Number.isFinite(v))return '—';if(type==='people')return v>=1e8?(v/1e8).toFixed(2)+' 亿':(v/1e4).toFixed(0)+' 万';if(type==='usd')return v>=1e9?(v/1e9).toFixed(2)+' 十亿美元':v>=1e6?(v/1e6).toFixed(1)+' 百万美元':'$'+numberFormatter.format(v);if(type==='pct')return numberFormatter.format(v)+'%';return numberFormatter.format(v)}
function escapeHTML(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function country(iso){return COUNTRIES.find(d=>d.code===iso)||COUNTRIES[0]}
function showToast(s){const el=$('toast');el.textContent=s;el.classList.add('visible');clearTimeout(showToast._t);showToast._t=setTimeout(()=>el.classList.remove('visible'),2600)}
function makeCountryList(){const q=$('search').value.trim().toLowerCase();const filtered=COUNTRIES.filter(x=>(activeFilter==='all'||activeFilter==='fr'&&x.francophone||activeFilter==='focus'&&FOCUS.has(x.code))&&(`${x.zh} ${x.en} ${x.code}`.toLowerCase().includes(q))).sort((a,b)=>a.zh.localeCompare(b.zh,'zh'));
 $('countryCount').textContent=`${filtered.length} 个国家`;
 $('countryList').innerHTML=filtered.map((x,i)=>`<div class="country-row ${selected===x.code?'selected':''}" data-iso="${x.code}" role="option" aria-selected="${selected===x.code}" tabindex="0"><span class="number">${String(i+1).padStart(2,'0')}</span><span class="cname">${x.zh}</span>${FOCUS.has(x.code)?'<span class="focus-dot" aria-label="重点关注"></span>':''}<span class="code">${x.code}</span></div>`).join('')||'<div style="padding:15px;color:#a4bbbb">没有匹配的国家</div>';
 [...$('countryList').querySelectorAll('.country-row')].forEach(el=>{el.onclick=()=>choose(el.dataset.iso);el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(el.dataset.iso)}}})}
function mapBuild(){const group=$('mapCountries'); group.innerHTML='';MAP_DATA.forEach(x=>{
  if(x.path){const node=document.createElementNS('http://www.w3.org/2000/svg','path');node.setAttribute('d',x.path);node.setAttribute('data-iso',x.code);node.setAttribute('class',`map-country ${x.special?'is-disputed':''}`);node.setAttribute('role','button');node.setAttribute('aria-label',x.zh);node.setAttribute('tabindex',x.special?'-1':'0');group.append(node);if(!x.special)bindMapNode(node,x)}
  if(x.point){const p=document.createElementNS('http://www.w3.org/2000/svg','circle');p.setAttribute('cx',x.point[0]);p.setAttribute('cy',x.point[1]);p.setAttribute('r',5.8);p.setAttribute('data-iso',x.code);p.setAttribute('class','map-island');p.setAttribute('role','button');p.setAttribute('tabindex','0');p.setAttribute('aria-label',x.zh);group.append(p);bindMapNode(p,x);const label=document.createElementNS('http://www.w3.org/2000/svg','text');label.setAttribute('x',x.point[0]+9);label.setAttribute('y',x.point[1]+4);label.setAttribute('class','map-label');label.textContent=x.zh;group.append(label)}
 });mapUpdate()}
function bindMapNode(el,x){el.addEventListener('click',()=>choose(x.code));el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(x.code)}});el.addEventListener('pointerenter',()=>{const t=$('mapTooltip');t.hidden=false;t.textContent=`${x.zh}  ·  ${x.code}`});el.addEventListener('pointermove',e=>{const r=$('africaMap').getBoundingClientRect();const t=$('mapTooltip');t.style.left=Math.min(e.clientX-r.left+15,r.width-140)+'px';t.style.top=(e.clientY-r.top-27)+'px'});el.addEventListener('pointerleave',()=>$('mapTooltip').hidden=true)}
function mapUpdate(){document.querySelectorAll('[data-iso].map-country,[data-iso].map-island').forEach(el=>{const x=country(el.dataset.iso),on=selected===el.dataset.iso;el.classList.toggle('active',on);el.classList.toggle('dim',activeFilter==='fr'&&!x.francophone||activeFilter==='focus'&&!FOCUS.has(x.code))});}
function setZoom(z){activeZoom=Math.max(1,Math.min(2.8,z));const svg=$('africaMap'),w=850/activeZoom,h=770/activeZoom,ax=425-w/2,ay=385-h/2;svg.setAttribute('viewBox',`${ax} ${ay} ${w} ${h}`)}
function latest(code,iso=selected){let r=DATA[iso]?.[code];return r?.[0]||null}
function series(code,iso=selected){return DATA[iso]?.[code]||[]}
function metricCard(code){const item=I_BY_CODE[code],v=latest(code);return `<div class="metric-card"><div class="mlabel"><span>${item[1]}</span><span>${v?v.year:'—'}</span></div><div class="mvalue ${v?'':'muted'}">${v?format(v.value,item[2]):'暂无数据'}</div><div class="mfoot">世界银行 WDI · ${v?`统计 ${v.year} 年`:'等待接口返回'}</div></div>`}
function renderMetrics(){const display=['SP.POP.TOTL','NY.GDP.MKTP.CD','NY.GDP.MKTP.KD.ZG','NY.GDP.PCAP.CD'];$('metricGrid').innerHTML=display.map(metricCard).join('')}
function renderTrendSelect(){const el=$('trendSelect');el.innerHTML=INDICATORS.filter(x=>['SP.POP.TOTL','NY.GDP.MKTP.CD','NY.GDP.MKTP.KD.ZG','NV.IND.MANF.ZS','FP.CPI.TOTL.ZG','IT.NET.USER.ZS'].includes(x[0])).map(x=>`<option value="${x[0]}">${x[1]}</option>`).join('')}
function renderTrend(){const svg=$('trendChart'),code=$('trendSelect').value,rows=series(code).slice(0,10).reverse();const item=I_BY_CODE[code];if(!rows.length){svg.innerHTML='<text x="300" y="66" text-anchor="middle" fill="#a0b5b5" font-size="14">暂无可绘制的历史数据 · 请联网刷新</text>';$('trendNote').textContent='未取得连续序列；请检查网络或源数据覆盖范围。';return}
 let min=Math.min(...rows.map(x=>x.value)),max=Math.max(...rows.map(x=>x.value));if(min===max){min-=1;max+=1}const lo=min-(max-min)*.16,hi=max+(max-min)*.16;
 const pts=rows.map((r,i)=>{const x=22+i*(556/(Math.max(1,rows.length-1))),y=110-(r.value-lo)/(hi-lo)*92;return [x,y,r]});
 const path=pts.map((p,i)=>`${i?'L':'M'} ${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(' ');
 const area=path+` L ${pts.at(-1)[0]} 111 L ${pts[0][0]} 111 Z`;
 svg.innerHTML=`<defs><linearGradient id="linefill" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#3cb6a6" stop-opacity=".20"/><stop offset="1" stop-color="#3cb6a6" stop-opacity="0"/></linearGradient></defs><line x1="20" y1="110" x2="580" y2="110" stroke="#d6e4e2" stroke-dasharray="3 5"/><path d="${area}" fill="url(#linefill)"/><path d="${path}" fill="none" stroke="#158d85" stroke-width="2.5"/>${pts.map(p=>`<circle cx="${p[0]}" cy="${p[1]}" r="3.1" fill="#15968e" stroke="#fff" stroke-width="1.5"><title>${p[2].year}: ${format(p[2].value,item[2])}</title></circle>`).join('')}<text x="22" y="125" fill="#98aaaa" font-size="10">${rows[0].year}</text><text x="578" text-anchor="end" y="125" fill="#98aaaa" font-size="10">${rows.at(-1).year}</text>`;
 $('trendNote').textContent=`${rows[0].year}—${rows.at(-1).year} · ${item[1]} · 世界银行；存在缺测年份时折线仅连接已公布年份。`}
function renderModules(){
 const tabs=$('moduleTabs');tabs.innerHTML=MODULES.map(m=>`<button class="module-tab ${selectedModule===m.id?'active':''}" role="tab" aria-selected="${selectedModule===m.id}" data-mod="${m.id}">${m.name}</button>`).join('');tabs.querySelectorAll('button').forEach(n=>n.onclick=()=>{selectedModule=n.dataset.mod;renderModules()});
 const m=MODULES.find(x=>x.id===selectedModule);
 let extra='';if(m.wdi.length){extra=`<div class="mod-mini-header">已接入的世界银行统计</div><div class="tag-grid">${m.wdi.map(i=>{const d=latest(i);return `<span class="data-tag">${I_BY_CODE[i][1]}：<strong>${d?format(d.value,I_BY_CODE[i][2])+' ('+d.year+')':'暂无数据'}</strong></span>`}).join('')}</div>`}
 const links=m.source.map(k=>`<a class="source-link" href="${SRC[k][1]}" target="_blank" rel="noopener noreferrer">${SRC[k][0]} <small>打开原始来源 ↗</small></a>`).join('');
 const noteKey=`atlas-note-${selected}-${m.id}`;const saved=readNote(noteKey);
 $('moduleContent').innerHTML=`<h4 class="mod-title">${m.short}</h4><p class="mod-desc">${m.desc}</p>${m.id==='trade'?moduleDataBlock(m):`${extra}${moduleDataBlock(m)}`}${typeof localDossierBlock==='function'?localDossierBlock(selected,m.id):''}<div class="mod-mini-header">该维度研究指标</div><div class="tag-grid">${m.questions.map(q=>`<span class="data-tag">${q}</span>`).join('')}</div>${COUNTRY_LEADS[selected]?`<div class="mod-mini-header">研究线索（仅作提示，不能代替来源）</div><div class="research-lead">${COUNTRY_LEADS[selected]}</div>`:''}<div class="mod-mini-header">原始资料数据库</div><div class="source-links">${links}</div><div class="mod-mini-header">我的研究笔记 · 本设备保存</div><textarea class="note-area" id="moduleNote" placeholder="记录该国政策变化、重要文献、待检验假设…">${escapeHTML(saved)}</textarea><div class="note-actions"><span>浏览器本地保存，清除缓存可能丢失，请定期导出</span><button class="note-save" id="saveNote">保存笔记</button></div>`;
 $('saveNote').onclick=()=>{if(writeNote(noteKey,$('moduleNote').value))showToast('笔记已保存在本浏览器');else showToast('无法本地保存，请导出备份')};
}
function renderCountry(){const c=country(selected);$('regionBadge').textContent=c.region;$('countryIso').textContent=c.code;$('frBadge').textContent=c.francophone?'法语相关地区':'';$('selectedName').textContent=c.zh;$('selectedEn').textContent=c.en;$('profileLead').textContent=COUNTRY_LEADS[selected]||'点击研究维度，查看国别资料字段、可用统计及权威来源。';$('mapState').textContent=`已选 · ${c.zh}`;renderMetrics();renderTrend();renderModules();makeCountryList();mapUpdate()}
function choose(iso){selected=iso;selectedModule='base';renderCountry();loadCountry(iso)}
function status(msg,mode='warn'){$('liveStatus').textContent=msg;$('liveDot').className='status-circle '+mode}
function normalizeRecords(records){const out={};for(const r of records){const code=r?.indicator?.id;const val=r?.value;const year=Number(r?.date);if(!I_BY_CODE[code]||typeof val!=='number'||!Number.isFinite(val)||!Number.isInteger(year))continue;(out[code]??=[]).push({year,value:val})}for(const k in out){out[k].sort((a,b)=>b.year-a.year);out[k]=out[k].filter((v,i,a)=>a.findIndex(u=>u.year===v.year)===i).slice(0,15)}return out}
async function fetchCountryLive(iso){const codes=INDICATORS.map(i=>i[0]).join(';');const u=`https://api.worldbank.org/v2/country/${iso}/indicator/${codes}?source=2&format=json&mrnev=12&per_page=500`;
 const ctrl=new AbortController();const t=setTimeout(()=>ctrl.abort(),11000);try{const res=await fetch(u,{signal:ctrl.signal,cache:'no-store'});if(!res.ok)throw new Error('HTTP '+res.status);const json=await res.json();if(!Array.isArray(json)||!Array.isArray(json[1]))throw new Error('非预期API返回格式');return normalizeRecords(json[1])}finally{clearTimeout(t)}}
async function ensureSnapshot(){if(SNAPSHOT!==null)return SNAPSHOT;SNAPSHOT={};try{const r=await fetch('./data/worldbank_snapshot.json',{cache:'no-cache'});if(r.ok){const d=await r.json();SNAPSHOT=d.countries||{}}}catch(e){}return SNAPSHOT}
async function loadCountry(iso,force=false){const token=++loadingToken;
 if(DATA[iso]&&!force){status('已加载 · 选择刷新可获取新数据','ok');return}
 status('正在读取公开统计数据…','warn');
 const snapshot=await ensureSnapshot();if(token!==loadingToken)return;
 if(snapshot[iso]&&!DATA[iso]){DATA[iso]=snapshot[iso];if(selected===iso){renderMetrics();renderTrend();renderModules();status('已显示周期性快照 · 正在核对在线数据','warn')}}
 try{const d=await fetchCountryLive(iso);if(!Object.keys(d).length)throw new Error('接口无可用记录');DATA[iso]=d;if(selected===iso){renderMetrics();renderTrend();renderModules();status('已从世界银行 API 更新 · 每项显示统计年','ok')}}
 catch(e){if(selected===iso){if(DATA[iso])status('在线更新失败，当前显示最近可用快照','warn');else status('无法连接世界银行接口 · 数据仍待获取','warn')}}}
async function init(){renderTrendSelect();makeCountryList();mapBuild();renderCountry();ensureSnapshot();loadCountry(selected);
 $('search').addEventListener('input',makeCountryList);$('search').addEventListener('keydown',e=>{if(e.key==='Enter'){const x=$('countryList').querySelector('.country-row');if(x)choose(x.dataset.iso)}});
 window.addEventListener('keydown',e=>{if(e.key==='/'&&document.activeElement.tagName!=='INPUT'&&document.activeElement.tagName!=='TEXTAREA'){e.preventDefault();$('search').focus()}if(e.key==='Escape'){hideOverlays();if(typeof localHidePanel==='function')localHidePanel()}});
 document.querySelectorAll('.filter').forEach(n=>n.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(i=>i.classList.remove('active'));n.classList.add('active');activeFilter=n.dataset.filter;makeCountryList();mapUpdate()}));
 $('zoomIn').onclick=()=>setZoom(activeZoom+.27);$('zoomOut').onclick=()=>setZoom(activeZoom-.27);$('zoomReset').onclick=()=>setZoom(1);$('trendSelect').onchange=renderTrend;
 $('refreshBtn').onclick=()=>loadCountry(selected,true);$('compareBtn').onclick=showCompare;$('closeCompare').onclick=hideOverlays;$('aboutBtn').onclick=()=>$('aboutOverlay').hidden=false;$('closeAbout').onclick=hideOverlays;
 ['compareOverlay','aboutOverlay'].forEach(id=>$(id).onclick=e=>{if(e.target===$(id))hideOverlays()});if(typeof initLocalUpload==='function')initLocalUpload();$('compareB').onchange=()=>{second=$('compareB').value;renderCompare();loadCompare(second).then(()=>{if(compareOpen)renderCompare()})};$('compareExport').onclick=exportCompare;$('exportBtn').onclick=exportCurrent;
}
function hideOverlays(){$('compareOverlay').hidden=true;$('aboutOverlay').hidden=true;compareOpen=false}
async function showCompare(){if(second===selected)second=selected==='SEN'?'GIN':'SEN';$('compareA').value=country(selected).zh;$('compareB').innerHTML=COUNTRIES.filter(x=>x.code!==selected).sort((a,b)=>a.zh.localeCompare(b.zh,'zh')).map(x=>`<option value="${x.code}">${x.zh}</option>`).join('');$('compareB').value=second;$('compareOverlay').hidden=false;compareOpen=true;renderCompare();loadCompare(second).then(()=>{if(compareOpen)renderCompare()})}
async function loadCompare(iso){if(DATA[iso])return;const snap=await ensureSnapshot();if(snap[iso])DATA[iso]=snap[iso];try{DATA[iso]=await fetchCountryLive(iso)}catch(e){} }
function renderCompare(){const iso=second;const target=$('compareTable');if(!compareOpen)return;
 target.innerHTML=`<div class="compare-row head"><div>同口径世界银行指标</div><div>${country(selected).zh}</div><div>${country(iso).zh}</div></div>`+INDICATORS.map(row=>{const a=latest(row[0],selected),b=latest(row[0],iso);return `<div class="compare-row"><div>${row[1]}</div><div class="${a?'':'cell-muted'}">${a?format(a.value,row[2])+' · '+a.year:'暂无'}</div><div class="${b?'':'cell-muted'}">${b?format(b.value,row[2])+' · '+b.year:'暂无'}</div></div>`}).join('') + '<div class="compare-row head"><div>对华贸易 · 中国报告口径</div><div>'+country(selected).zh+'</div><div>'+country(iso).zh+'</div></div>' + ['china_exports_usd','china_imports_usd'].map((k,i)=>{const a=latestTrade(selected),b=latestTrade(iso);return '<div class="compare-row"><div>'+(i===0?'中国对该国出口':'中国从该国进口')+'</div><div>'+(a?usdFmt(a[k])+' · '+a.year:'暂无')+'</div><div>'+(b?usdFmt(b[k])+' · '+b.year:'暂无')+'</div></div>'}).join('') + '<p style="font-size:10px;color:#90a3a4;line-height:1.7">各国最新可用统计年份可能不同。贸易使用中国报告口径；通用FDI净流入不是中国对该国投资。</p>'}
function download(name,text,type){const a=document.createElement('a'),url=URL.createObjectURL(new Blob([text],{type}));a.href=url;a.download=name;document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1500)}
function exportCurrent(){const c=country(selected),out={country:{code:c.code,name:c.zh,english:c.en,region:c.region,francophone:c.francophone},source:'World Bank WDI / UN Comtrade / curated primary records',exported_at:new Date().toISOString(),indicators:DATA[selected]||{},trade:tradeRows(selected),records:(STORE.records.records||[]).filter(r=>r.country===selected),modules:Object.fromEntries(['investment','financing','engineering','resources','industry','payments','security','multilateral','society','surveys','external','diplomacy'].map(k=>[k,STORE[k]?.countries?.[selected]||[]])),notes:{}};MODULES.forEach(m=>{const n=readNote(`atlas-note-${selected}-${m.id}`);if(n)out.notes[m.id]=n});download(`AfricaAtlas_${selected}_${new Date().toISOString().slice(0,10)}.json`,JSON.stringify(out,null,2),'application/json;charset=utf-8');showToast('已导出当前国别指标及本地笔记')}
function exportCompare(){const lines=[['指标','世界银行代码',country(selected).zh,'A数据年份',country(second).zh,'B数据年份']];INDICATORS.forEach(x=>{const a=latest(x[0],selected),b=latest(x[0],second);lines.push([x[1],x[0],a?.value??'',a?.year??'',b?.value??'',b?.year??''])});const ta=latestTrade(selected),tb=latestTrade(second);for(const [key,name] of [['china_exports_usd','中国对该国出口'],['china_imports_usd','中国自该国进口']])lines.push([name,'UN Comtrade / CHN reporter',ta?.[key]??'',ta?.year??'',tb?.[key]??'',tb?.year??'']);download(`AfricaAtlas_${selected}_vs_${second}.csv`,'\uFEFF'+lines.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(',')).join('\r\n'),'text/csv;charset=utf-8')}
init();
