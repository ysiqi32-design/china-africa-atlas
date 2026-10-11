/* Daily research leads: GDELT metadata, NOT verified news facts. Local review state stays in browser. */
'use strict';
let ATLAS_NEWS=window.ATLAS_DATA_BUNDLE?.news||{countries:{},country_status:{},status:'not_yet_fetched'};
let newsSelectedCountry='GIN',newsLimit=6,newsTopic='all',newsSource='all',newsText='';
const NEWS_MODULES={'all':'全部主题','general':'暂未分类','diplomacy':'外交','trade':'贸易','investment':'直接投资','financing':'融资债务','projects':'基础设施','resources':'能源矿产','industry':'工业技术','payments':'金融支付','security':'军事安全','multilateral':'多边外交','society':'教育文化','opinion':'民意与社会','external':'外部伙伴'};
const NEWS_TRUSTED={ 'reuters.com':'Reuters','france24.com':'France 24','jeuneafrique.com':'Jeune Afrique','africanews.com':'Africanews','un.org':'联合国','worldbank.org':'世界银行','focac.org':'中非合作论坛','fmprc.gov.cn':'中国外交部','gov.cn':'中国政府机构','africa-union.org':'非盟'};
function newsPublisher(domain){const d=String(domain||'').toLowerCase();for(const [host,label] of Object.entries(NEWS_TRUSTED)){if(d===host||d.endsWith('.'+host))return label}return d||'来源待核';}
function newsGroup(domain){const d=String(domain||'').toLowerCase();if(!d)return 'other';if(/(^|\.)(gov|gouv)\.[a-z.]+$/.test(d)||d.endsWith('focac.org')||d.endsWith('fmprc.gov.cn')||d.endsWith('un.org')||d.endsWith('worldbank.org'))return 'institution';if(['reuters.com','france24.com','jeuneafrique.com','africanews.com','apnews.com','bbc.com'].some(t=>d===t||d.endsWith('.'+t)))return 'media';return 'other';}
function newsReviewState(){try{return JSON.parse(localStorage.getItem('atlas-news-review-v1')||'{}')||{}}catch{return {}}}
function newsSetReview(id,action){try{const all=newsReviewState();if(action==='none')delete all[id];else all[id]={status:action,changed_at:new Date().toISOString()};localStorage.setItem('atlas-news-review-v1',JSON.stringify(all));renderNewsPanel()}catch(e){if(typeof showToast==='function')showToast('本地存储不可用，请检查浏览器设置')}}
function newsSafeHref(raw){try{const x=new URL(raw);if(!['https:','http:'].includes(x.protocol)||x.username||x.password)return '#';return x.href}catch{return '#'}}
function newsEscape(text){return String(text??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function newsDate(text){if(!text)return '时间未知';const d=new Date(text);return Number.isNaN(d.getTime())?'时间未知':new Intl.DateTimeFormat('zh-CN',{timeZone:'UTC',year:'numeric',month:'2-digit',day:'2-digit'}).format(d)}
function newsCount(){return Object.values(ATLAS_NEWS.countries||{}).reduce((n,list)=>n+(Array.isArray(list)?list.length:0),0)}
function newsLeadList(){const list=ATLAS_NEWS.countries?.[newsSelectedCountry]||[],state=newsReviewState();let rows=list.filter(x=>x && x.verification==='unverified_discovery' && x.url && x.title && state[x.id]?.status!=='hidden');
 if(newsTopic!=='all')rows=rows.filter(x=>(x.modules||[]).includes(newsTopic));
 if(newsSource!=='all')rows=rows.filter(x=>newsGroup(x.domain)===newsSource);
 if(newsText.trim()){const s=newsText.toLowerCase();rows=rows.filter(x=>(x.title+' '+x.domain).toLowerCase().includes(s));}
 return rows.sort((a,b)=>(b.detected_at_utc||'').localeCompare(a.detected_at_utc||''));}
function renderNewsPanel(iso){if(iso)newsSelectedCountry=iso;const root=document.getElementById('newsPanel');if(!root)return;
 const all=ATLAS_NEWS.countries?.[newsSelectedCountry]||[],filtered=newsLeadList(),shown=filtered.slice(0,newsLimit),review=newsReviewState();const health=ATLAS_NEWS.country_status?.[newsSelectedCountry]||{};
 const updated=health.last_success_at_utc||ATLAS_NEWS.last_success_at_utc;
 const status=health.status==='fetch_failed'?'本国最近一次检查失败（可能遭遇接口限流；保留旧线索）':updated?`最近成功索引：${newsDate(updated)} · 最近${ATLAS_NEWS.lookback_days||14}日发现`: '尚未完成首次自动抓取';
 root.innerHTML=`<div class="news-head"><div><div class="overline teal">COUNTRY INTELLIGENCE · ARTICLE DISCOVERY</div><h3>国别最新动态 <span class="news-count">${all.length} 条索引线索</span></h3><p>自动发现的标题仅用于研究检索，不代表报道属实或与双边关系确有关联。数据源限流时按小批次轮换国家（计划每天4国，约14天一轮），单国更新日期以状态提示为准。</p></div><div class="news-side"><span class="news-status">${newsEscape(status)}</span><button id="newsJump" class="ghost small">查看更新说明 ↗</button></div></div>
 <div class="news-toolbar"><label>研究维度<select id="newsTopic">${Object.entries(NEWS_MODULES).map(([id,name])=>`<option value="${id}" ${newsTopic===id?'selected':''}>${name}</option>`).join('')}</select></label><label>资料类型<select id="newsSource"><option value="all" ${newsSource==='all'?'selected':''}>所有来源</option><option value="institution" ${newsSource==='institution'?'selected':''}>政府 / 国际机构</option><option value="media" ${newsSource==='media'?'selected':''}>指定新闻机构</option><option value="other" ${newsSource==='other'?'selected':''}>其他媒体</option></select></label><label>搜索标题<input id="newsSearch" maxlength="90" value="${newsEscape(newsText)}" placeholder="如矿业、railway、贸易" /></label><button class="ghost small" id="newsReload" title="重新读取网站已发布的数据；不直接抓取新闻源">↻ 读取最新快照</button></div>
 <div class="news-cards">${shown.map(x=>{const state=review[x.id]?.status||'none';const terms=(x.modules||[]).map(z=>NEWS_MODULES[z]||z).slice(0,3);return `<article class="news-item"><div class="news-metadata"><span class="news-unverified">待核验 · 自动检索</span><span>${newsEscape(newsPublisher(x.domain))}</span><span>索引发现 ${newsDate(x.detected_at_utc)}</span></div><a class="news-title" href="${newsEscape(newsSafeHref(x.url))}" target="_blank" rel="noopener noreferrer">${newsEscape(x.title)} ↗</a><div class="news-categories">${terms.map(t=>`<span>${newsEscape(t)}</span>`).join('')}<small>主题由标题关键词粗分类</small></div><div class="news-actions"><button type="button" class="news-save ${state==='saved'?'selected':''}" data-id="${newsEscape(x.id)}" data-action="${state==='saved'?'none':'saved'}">${state==='saved'?'✓ 已加入核验清单':'＋ 加入核验清单'}</button><button type="button" class="news-ignore" data-id="${newsEscape(x.id)}" data-action="hidden">忽略此线索</button></div></article>`}).join('')||(all.length?'<div class="news-empty">当前筛选没有匹配的线索，可以切换维度或清除筛选。</div>':'<div class="news-empty">暂无已入库的新闻索引。请先在 GitHub Actions 执行「Discover Africa–China news leads」进行首次抓取；未检索到不意味着没有发生事件。</div>')}</div>
 <div class="news-bottom"><span>展示 ${shown.length} / ${filtered.length} 条 · 检索平台：<a href="https://www.gdeltproject.org/" target="_blank" rel="noopener noreferrer">GDELT</a> · 标注日期为GDELT发现时间，并非原文发表日期</span><div><button id="newsExportSaved" class="ghost small">↓ 导出待核验清单</button>${filtered.length>shown.length?'<button id="newsMore" class="ghost small">查看更多线索</button>':''}</div></div>`;
 root.querySelector('#newsTopic').onchange=e=>{newsTopic=e.target.value;newsLimit=6;renderNewsPanel()};
 root.querySelector('#newsSource').onchange=e=>{newsSource=e.target.value;newsLimit=6;renderNewsPanel()};
 root.querySelector('#newsSearch').oninput=e=>{newsText=e.target.value;newsLimit=6;renderNewsPanel();const el=document.getElementById('newsSearch');el?.focus();el?.setSelectionRange(newsText.length,newsText.length)};
 root.querySelectorAll('[data-action]').forEach(el=>el.onclick=()=>newsSetReview(el.dataset.id,el.dataset.action));
 root.querySelector('#newsMore')?.addEventListener('click',()=>{newsLimit+=12;renderNewsPanel()});
 root.querySelector('#newsExportSaved')?.addEventListener('click',newsExportSaved);
 root.querySelector('#newsReload')?.addEventListener('click',()=>newsReload(true));
 root.querySelector('#newsJump')?.addEventListener('click',()=>{const about=document.getElementById('aboutOverlay');if(about)about.hidden=false});
}
function newsExportSaved(){const state=newsReviewState(),out=[];for(const [iso,list] of Object.entries(ATLAS_NEWS.countries||{}))for(const item of list){if(state[item.id]?.status==='saved')out.push(item)}
 if(!out.length){if(typeof showToast==='function')showToast('核验清单为空；请先收藏线索');return}
 const rows=[['国家ISO3','新闻标题（待核验）','来源域名','GDELT发现时间','维度','原文URL','核验状态']];for(const r of out)rows.push([r.country,r.title,r.domain,r.detected_at_utc,(r.modules||[]).join(';'),r.url,'待核验']);
 const csv='\ufeff'+rows.map(row=>row.map(v=>'"'+String(v??'').replaceAll('"','""')+'"').join(',')).join('\r\n');download(`AfricaAtlas_待核验新闻清单_${new Date().toISOString().slice(0,10)}.csv`,csv,'text/csv;charset=utf-8');
}
async function newsReload(report=false){try{
 // Only read our published JSON. The browser never scrapes publishers or requests GDELT directly.
 const res=await fetch('./data/news.json?cache='+Date.now(),{cache:'no-store'});
 if(!res.ok)throw new Error('HTTP '+res.status);
 const v=await res.json();if(v.dataset!=='africa_china_news_discovery'||typeof v.countries!=='object')throw new Error('数据格式异常');
 ATLAS_NEWS=v;renderNewsPanel();if(report&&typeof showToast==='function')showToast('已读取网站发布的最新新闻索引快照');
 }catch(e){if(report&&typeof showToast==='function')showToast('读取发布快照失败，保留现有线索');}
}
function initNews(){const jump=document.getElementById('newsTopNav');if(jump)jump.onclick=()=>document.getElementById('newsPanel')?.scrollIntoView({behavior:'smooth',block:'start'});
 renderNewsPanel(newsSelectedCountry);newsReload(false);}
