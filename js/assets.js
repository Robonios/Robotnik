// ═══════════════════════════════════════════════════════════
// FRONTIER ASSETS PAGE — Messari-style data table
// Full-width, frozen columns, column groups, sparklines
// ═══════════════════════════════════════════════════════════

var assetsData = [];
var assetsFiltered = [];
var assetsSector = 'all';
var assetsSort = 'mcap';
var assetsSortDir = -1;
var assetsPerPage = 50;
var assetsCurrentPage = 0;
var assetsColGroup = 'overview';

var SMAP = { 'Semiconductors':'semi','Semiconductor':'semi','Robotics':'robo','Space':'space','Materials':'materials','Materials & Inputs':'materials' };
var SLBL = { semi:'Semi', robo:'Robo', space:'Space', materials:'Materials' };
var SCSS = { semi:'sector-semi', robo:'sector-robo', space:'sector-space', materials:'sector-materials' };

// ── Column definitions by group ──
var COL_GROUPS = {
  overview: [
    {key:'price',label:'Price',sort:'price',r:1},
    {key:'ccy',label:'Ccy',sort:null,r:0},
    {key:'24h',label:'24H',sort:'24h',r:1},
    {key:'7d',label:'7D',sort:'7d',r:1},
    {key:'30d',label:'30D',sort:'30d',r:1},
    {key:'spark30',label:'Trend',sort:null,r:1},
    {key:'ytd',label:'YTD',sort:'ytd',r:1},
    {key:'mcap',label:'MCap',sort:'mcap',r:1},
    {key:'pe',label:'P/E',sort:'pe',r:1},
  ],
  performance: [
    {key:'price',label:'Price',sort:'price',r:1},
    {key:'24h',label:'24H',sort:'24h',r:1},
    {key:'7d',label:'7D',sort:'7d',r:1},
    {key:'30d',label:'30D',sort:'30d',r:1},
    {key:'spark30',label:'Trend',sort:null,r:1},
    {key:'ytd',label:'YTD',sort:'ytd',r:1},
    {key:'3m',label:'3M',sort:'3m',r:1},
    {key:'6m',label:'6M',sort:'6m',r:1},
    {key:'1y',label:'1Y',sort:'1y',r:1},
    {key:'3y',label:'3Y',sort:'3y',r:1},
    {key:'5y',label:'5Y',sort:'5y',r:1},
    {key:'ath',label:'ATH',sort:'ath',r:1},
    {key:'fromAth',label:'%ATH',sort:'fromAth',r:1},
  ],
  mcap: [
    {key:'mcap',label:'MCap',sort:'mcap',r:1},
    {key:'mcap7d',label:'7D',sort:null,r:1},
    {key:'mcap30d',label:'30D',sort:null,r:1},
    {key:'mcapYtd',label:'YTD Start',sort:null,r:1},
    {key:'pe',label:'P/E',sort:'pe',r:1},
    {key:'ps',label:'P/S',sort:'ps',r:1},
    {key:'pb',label:'P/B',sort:'pb',r:1},
  ],
  volume: [
    {key:'price',label:'Price',sort:'price',r:1},
    {key:'vol',label:'Volume',sort:'vol',r:1},
    {key:'vol7d',label:'Avg 7D',sort:'vol7d',r:1},
    {key:'vol30d',label:'Avg 30D',sort:'vol30d',r:1},
    {key:'mcap',label:'MCap',sort:'mcap',r:1},
  ],
  valuation: [
    {key:'price',label:'Price',sort:'price',r:1},
    {key:'mcap',label:'MCap',sort:'mcap',r:1},
    {key:'pe',label:'P/E',sort:'pe',r:1},
    {key:'fwdpe',label:'Fwd P/E',sort:'fwdpe',r:1},
    {key:'eveb',label:'EV/EBITDA',sort:'eveb',r:1},
    {key:'ps',label:'P/S',sort:'ps',r:1},
    {key:'rev',label:'Rev TTM',sort:'rev',r:1},
    {key:'margin',label:'Op Margin',sort:'margin',r:1},
    {key:'divyld',label:'Div Yield',sort:'divyld',r:1},
  ],
  intelligence: [
    {key:'vctier',label:'Value Chain',sort:null,r:0},
    {key:'bnrisk',label:'Bottleneck',sort:null,r:0},
    {key:'keycust',label:'Key Customers',sort:null,r:0},
    {key:'keysupp',label:'Key Suppliers',sort:null,r:0},
    {key:'rnotes',label:"Robotnik's Notes",sort:null,r:0},
  ],
};

// Enrichment data (loaded async)
var _enrichmentData = null;

// ── Formatters ──
function fp(price,ccy){if(!price)return'\u2014';var c=(ccy||'USD').toUpperCase();var s=c==='GBP'?'\u00a3':c==='EUR'?'\u20ac':c==='JPY'?'\u00a5':c==='KRW'?'\u20a9':c==='HKD'?'HK$':c==='CHF'?'CHF ':c==='TWD'?'NT$':c==='CNY'?'\u00a5':c==='SEK'?'SEK ':c==='NOK'?'NOK':'$';return s+price.toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});}
function fm(n){if(!n||n<=0)return'\u2014';if(n>=1e12)return'$'+(n/1e12).toFixed(2)+'T';if(n>=1e9)return'$'+(n/1e9).toFixed(1)+'B';if(n>=1e6)return'$'+(n/1e6).toFixed(0)+'M';return'$'+n.toLocaleString();}
function fpc(v){if(v===null||v===undefined)return'\u2014';var cls=v>=0?'v-green':'v-red';var sgn=v>=0?'+':'';return'<span class="'+cls+'">'+sgn+v.toFixed(2)+'%</span>';}
function fv(v){if(!v||v<=0)return'\u2014';if(v>=1e9)return(v/1e9).toFixed(1)+'B';if(v>=1e6)return(v/1e6).toFixed(1)+'M';if(v>=1e3)return(v/1e3).toFixed(0)+'K';return String(v);}
function fn(v,d){if(!v||v<=0)return'\u2014';return v.toFixed(d||1);}
function fmg(v){if(!v)return'\u2014';return(v*100).toFixed(1)+'%';}

// ── Sparkline SVG ──
function sparkSvg(arr,w,h){
  if(!arr||arr.length<2)return'\u2014';
  var mn=Math.min.apply(null,arr),mx=Math.max.apply(null,arr);
  if(mx===mn){mx+=1;}
  var pts=arr.map(function(v,i){return(i/(arr.length-1)*w).toFixed(1)+','+(h-2-(v-mn)/(mx-mn)*(h-4)).toFixed(1);}).join(' ');
  var col=arr[arr.length-1]>=arr[0]?'#F5D921':'#F87171';
  return'<svg width="'+w+'" height="'+h+'" viewBox="0 0 '+w+' '+h+'" style="display:inline-block;vertical-align:middle"><polyline points="'+pts+'" fill="none" stroke="'+col+'" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
}

// ── Cell renderer ──
function cellHtml(e,key){
  switch(key){
    case'price':return fp(e.price,e.currency);
    case'ccy':return'<span class="dim">'+(e.currency||'USD')+'</span>';
    case'24h':return fpc(e.change_24h_pct);
    case'7d':return fpc(e.change_7d_pct);
    case'30d':return fpc(e.change_30d_pct);
    case'ytd':return fpc(e.change_ytd_pct);
    case'3m':return fpc(e.change_3m_pct);
    case'6m':return fpc(e.change_6m_pct);
    case'1y':return fpc(e.change_1y_pct);
    case'3y':return fpc(e.change_3y_pct);
    case'5y':return fpc(e.change_5y_pct);
    case'spark30':return sparkSvg(e.sparkline_30d,80,24);
    case'mcap':return fm(e.market_cap);
    case'mcap7d':return fm(e.market_cap);// placeholder — same as current for now
    case'mcap30d':return fm(e.market_cap);
    case'mcapYtd':return fm(e.market_cap);
    case'pe':return fn(e.pe_ratio);
    case'fwdpe':return fn(e.forward_pe);
    case'eveb':return fn(e.ev_ebitda);
    case'ps':return fn(e.ps_ratio);
    case'pb':return fn(e.pb_ratio);
    case'rev':return fm(e.revenue_ttm);
    case'margin':return fmg(e.operating_margin);
    case'divyld':return e.dividend_yield?fn(e.dividend_yield*100)+'%':'\u2014';
    case'vol':return fv(e.volume);
    case'vol7d':return fv(e.volume_avg_7d);
    case'vol30d':return fv(e.volume_avg_30d);
    case'ath':return fp(e.ath,e.currency);
    case'fromAth':return fpc(e.pct_from_ath);
    // Intelligence columns
    case'vctier':case'bnrisk':case'keycust':case'keysupp':case'rnotes':
      if(!_enrichmentData)return'<span class="dim" style="opacity:0.4">\u2014</span>';
      var enr=_enrichmentData[e.ticker];
      if(!enr)return'<span class="dim" style="opacity:0.4">\u2014</span>';
      if(key==='vctier')return'<span class="dim">'+enr.value_chain_tier+'</span>';
      if(key==='bnrisk'){var rc=enr.bottleneck_risk;var cls=rc==='CRITICAL'||rc==='HIGH'?'v-red':rc==='MEDIUM'?'v-green':'dim';return'<span class="'+cls+'">'+rc+'</span>';}
      if(key==='keycust')return'<span class="dim" style="font-size:8px">'+enr.key_customers.substring(0,60)+(enr.key_customers.length>60?'...':'')+'</span>';
      if(key==='keysupp')return'<span class="dim" style="font-size:8px">'+enr.key_suppliers.substring(0,60)+(enr.key_suppliers.length>60?'...':'')+'</span>';
      if(key==='rnotes')return'<span class="dim" style="font-size:8px" title="'+enr.robotnik_notes.replace(/"/g,'&quot;')+'">'+enr.robotnik_notes.substring(0,80)+(enr.robotnik_notes.length>80?'...':'')+'</span>';
      return'\u2014';
    default:return'\u2014';
  }
}

// ── Sort value ──
function sortVal(e,key){
  switch(key){
    case'price':return e.price||0;
    case'24h':return e.change_24h_pct||0;
    case'7d':return e.change_7d_pct||0;
    case'30d':return e.change_30d_pct||0;
    case'ytd':return e.change_ytd_pct||0;
    case'3m':return e.change_3m_pct||0;
    case'6m':return e.change_6m_pct||0;
    case'1y':return e.change_1y_pct||0;
    case'3y':return e.change_3y_pct||0;
    case'5y':return e.change_5y_pct||0;
    case'mcap':return e.market_cap||0;
    case'pe':return e.pe_ratio||9999;
    case'fwdpe':return e.forward_pe||9999;
    case'eveb':return e.ev_ebitda||9999;
    case'ps':return e.ps_ratio||9999;
    case'pb':return e.pb_ratio||9999;
    case'rev':return e.revenue_ttm||0;
    case'margin':return e.operating_margin||0;
    case'divyld':return e.dividend_yield||0;
    case'vol':return e.volume||0;
    case'vol7d':return e.volume_avg_7d||0;
    case'vol30d':return e.volume_avg_30d||0;
    case'ath':return e.ath||0;
    case'fromAth':return e.pct_from_ath||0;
    case'ticker':return e.ticker;
    case'company':return e.name;
    default:return e.market_cap||0;
  }
}

// ── Load data ──
(function(){
  fetch('data/markets/robotnik_public_markets.json?v='+Date.now())
    .then(function(r){return r.ok?r.json():null;})
    .then(function(data){
      if(!data||!data.entities){document.getElementById('assets-summary').textContent='Data not available.';return;}
      assetsData=Object.values(data.entities).filter(function(e){return SMAP[e.sector]!==undefined;});
      var total=assetsData.length;
      var withMcap=assetsData.filter(function(e){return e.market_cap>0;}).length;
      document.getElementById('assets-summary').textContent=total+' entities \u00b7 '+withMcap+' with market cap \u00b7 Updated '+new Date(data.last_updated).toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
      var descEl=document.getElementById('assets-desc');
      if(descEl)descEl.textContent=total+' frontier technology equities across semiconductors, robotics, space, and materials. Data from EODHD. Fundamentals weekly.';
      var sc={};assetsData.forEach(function(e){var s=SMAP[e.sector]||'?';sc[s]=(sc[s]||0)+1;});
      document.querySelectorAll('#asset-tabs .market-tab').forEach(function(t){var s=t.dataset.sector;t.textContent=s==='all'?'All ('+total+')':(SLBL[s]||s)+' ('+(sc[s]||0)+')';});
      renderAssetsTable();
      // Load enrichment data for Intelligence tab
      fetch('data/markets/enrichment_data.json?v='+Date.now())
        .then(function(r){return r.ok?r.json():null;})
        .then(function(enr){if(enr){_enrichmentData=enr;}});
    });
})();

function setColGroup(btn){
  document.querySelectorAll('.col-group-tab').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  assetsColGroup=btn.dataset.group;
  renderAssetsTable();
}

function filterAssets(btn){
  document.querySelectorAll('#asset-tabs .market-tab').forEach(function(b){b.classList.remove('active');});
  btn.classList.add('active');
  assetsSector=btn.dataset.sector;
  assetsCurrentPage=0;
  renderAssetsTable();
}

function sortAssets(col){
  if(assetsSort===col){assetsSortDir*=-1;}else{assetsSort=col;assetsSortDir=-1;}
  renderAssetsTable();
}

function exportAssetsCSV(){
  if(!assetsFiltered.length)return;
  var cols=COL_GROUPS[assetsColGroup]||COL_GROUPS.overview;
  var headers=['#','Ticker','Company','Sector','Subsector'].concat(cols.map(function(c){return c.label;}));
  var rows=[headers.join(',')];
  assetsFiltered.forEach(function(e,i){
    var sk=SMAP[e.sector]||'';
    var sl=SLBL[sk]||e.sector;
    var vals=[i+1,e.ticker,'"'+(e.name||'').replace(/"/g,'""')+'"',sl,'"'+(e.subsector||'')+'"'];
    cols.forEach(function(c){
      var v='';
      if(c.key==='price')v=e.price||'';
      else if(c.key==='ccy')v=e.currency||'USD';
      else if(c.key.match(/^(24h|7d|30d|ytd|3m|6m|1y|3y|5y|fromAth)$/))v=e['change_'+c.key.replace('h','h').replace('fromAth','')+'_pct']||'';
      else if(c.key==='mcap')v=e.market_cap||'';
      else if(c.key==='pe')v=e.pe_ratio||'';
      else if(c.key==='vol')v=e.volume||'';
      else if(c.key==='rev')v=e.revenue_ttm||'';
      else if(c.key==='spark30')v='';
      else v='';
      vals.push(v);
    });
    rows.push(vals.join(','));
  });
  var blob=new Blob([rows.join('\n')],{type:'text/csv'});
  var url=URL.createObjectURL(blob);
  var a=document.createElement('a');
  a.href=url;a.download='robotnik_frontier_assets_'+assetsColGroup+'.csv';
  document.body.appendChild(a);a.click();document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function assetsPage(d){
  var mx=Math.ceil(assetsFiltered.length/assetsPerPage)-1;
  assetsCurrentPage=Math.max(0,Math.min(mx,assetsCurrentPage+d));
  renderAssetsTable();
}

function renderAssetsTable(){
  var thead=document.getElementById('assets-thead');
  var tbody=document.getElementById('assets-tbody');
  if(!thead||!tbody||!assetsData.length)return;

  var cols=COL_GROUPS[assetsColGroup]||COL_GROUPS.overview;
  var search=(document.getElementById('asset-search').value||'').toLowerCase().trim();

  // Filter
  assetsFiltered=assetsData.filter(function(e){
    var sk=SMAP[e.sector]||'?';
    if(assetsSector!=='all'&&sk!==assetsSector)return false;
    if(search&&!e.ticker.toLowerCase().includes(search)&&!e.name.toLowerCase().includes(search))return false;
    return true;
  });

  // Sort
  assetsFiltered.sort(function(a,b){
    var va=sortVal(a,assetsSort),vb=sortVal(b,assetsSort);
    if(typeof va==='string')return va<vb?-assetsSortDir:va>vb?assetsSortDir:0;
    return(va-vb)*assetsSortDir;
  });

  // Header
  var hh='<tr>';
  hh+='<th class="frozen f0">#</th>';
  hh+='<th class="frozen f1" onclick="sortAssets(\'ticker\')">Ticker '+(assetsSort==='ticker'?(assetsSortDir===-1?'\u25bc':'\u25b2'):'')+'</th>';
  hh+='<th class="frozen f2" onclick="sortAssets(\'company\')">Company '+(assetsSort==='company'?(assetsSortDir===-1?'\u25bc':'\u25b2'):'')+'</th>';
  hh+='<th>Sector</th>';
  hh+='<th>Sub</th>';
  for(var ci=0;ci<cols.length;ci++){
    var c=cols[ci];
    var arrow=assetsSort===c.sort?(assetsSortDir===-1?'\u25bc':'\u25b2'):'';
    var onclick=c.sort?'onclick="sortAssets(\''+c.sort+'\')"':'';
    hh+='<th class="'+(c.r?'r':'')+'" '+onclick+'>'+c.label+' '+arrow+'</th>';
  }
  hh+='</tr>';
  thead.innerHTML=hh;

  // Body
  var start=assetsCurrentPage*assetsPerPage;
  var page=assetsFiltered.slice(start,start+assetsPerPage);
  var rows='';
  for(var ri=0;ri<page.length;ri++){
    var e=page[ri];
    var sk=SMAP[e.sector]||'semi';
    var sc=SCSS[sk]||'sector-semi';
    var sl=SLBL[sk]||e.sector;
    var sub=e.subsector||'\u2014';
    rows+='<tr>';
    rows+='<td class="frozen f0 dim">'+(start+ri+1)+'</td>';
    rows+='<td class="frozen f1 ticker-cell">'+e.ticker+'</td>';
    rows+='<td class="frozen f2" style="max-width:120px;overflow:hidden;text-overflow:ellipsis;">'+e.name+'</td>';
    rows+='<td><span class="sector-tag '+sc+'">'+sl+'</span></td>';
    rows+='<td class="dim" style="font-size:9px;">'+sub+'</td>';
    for(var ci2=0;ci2<cols.length;ci2++){
      rows+='<td class="'+(cols[ci2].r?'r':'')+'">'+cellHtml(e,cols[ci2].key)+'</td>';
    }
    rows+='</tr>';
  }
  tbody.innerHTML=rows||'<tr><td colspan="'+(5+cols.length)+'" style="text-align:center;padding:2rem;color:var(--text-dim);">No data</td></tr>';

  // Pagination
  var tp=Math.ceil(assetsFiltered.length/assetsPerPage);
  document.getElementById('assets-showing').textContent='Showing '+(assetsFiltered.length?start+1:0)+'\u2013'+Math.min(start+assetsPerPage,assetsFiltered.length)+' of '+assetsFiltered.length;
  document.getElementById('assets-page-info').textContent='Page '+(assetsCurrentPage+1)+' of '+Math.max(tp,1);
  document.getElementById('assets-prev').disabled=assetsCurrentPage===0;
  document.getElementById('assets-next').disabled=assetsCurrentPage>=tp-1;
}
