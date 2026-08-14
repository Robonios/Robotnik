// ===== FUNDING OPERATIONS PAGE =====
var summaryData = null, roundsData = null;
var currentPeriod = '1Y';

// ===== RPCI scope (single source of truth) =====
// data/index/rpci_scope.json is emitted by scripts/calculate_private_index.py and
// defines which round types are RPCI-eligible "primary capital" vs lifecycle
// "exits". The page READS it rather than hand-maintaining a parallel EXCLUDED_ROUNDS
// / M&A list, so the funding page and the index can never drift.
var excludedRoundsSet = null;   // {roundValue: 1} — excluded from primary capital
var mnaIncludedSet = null;      // {"company|date": 1} — the only M&A that count as primary
function buildScope(scope){
  excludedRoundsSet = {};
  ((scope && scope.excluded_rounds) || []).forEach(function(r){ excludedRoundsSet[r] = 1; });
  mnaIncludedSet = {};
  ((scope && scope.mna_included) || []).forEach(function(m){ mnaIncludedSet[(m.company||'')+'|'+(m.date||'')] = 1; });
}
// RPCI-eligible primary capital: a round counts unless it is an excluded type;
// M&A counts only when the acquirer is private in-universe (mna_included).
function isPrimary(r){
  if(!excludedRoundsSet) return true; // scope not loaded -> degrade to unfiltered
  var rd = (r.round||'').trim();
  if(rd === 'M&A') return !!mnaIncludedSet[(r.company||'')+'|'+(r.date||'')];
  return !excludedRoundsSet[rd];
}
// Lifecycle exits surfaced separately: IPOs (listed or filed) + M&A that is NOT primary.
function isExit(r){
  var rd = (r.round||'').trim();
  if(rd === 'IPO' || rd === 'IPO (filed)') return true;
  if(rd === 'M&A') return !isPrimary(r);
  return false;
}
// Non-venture capital events: excluded round types that are neither venture rounds
// nor exits — Strategic / Government / Grant / Debt / Bridge / Undisclosed / Other /
// blank. Stored, but not primary capital. Together primary + exits + non-venture
// partition every (dated, non-Token/Cross-Stack) row exactly once.
function isNonVenture(r){
  var rd = (r.round||'').trim();
  if(rd === 'IPO' || rd === 'IPO (filed)' || rd === 'M&A') return false; // exits or M&A
  return !!(excludedRoundsSet && excludedRoundsSet[rd]);
}
var trendsChart = null, sectorChart = null;
var topRoundsSortCol = 'amount', topRoundsSortAsc = false;

var sectorColors = {
  'Semiconductors':'#F5D921','Robotics':'#3B82F6','Space':'#94A3B8',
  'Materials':'#FB923C'
};
var sectorPillCls = {
  'Semiconductors':'sp-semi','Robotics':'sp-robo','Space':'sp-space',
  'Materials':'sp-mat'
};
var stageOrder = {'Seed':0,'Pre-Seed':0,'Series A':1,'Series B':2,'Series C':3,'Series D':4,'Series D+':5,'Series E':5,'Series F':5,'Series G':5,'Series H':5};

// ===== Chart.js global defaults =====
Chart.defaults.color = '#8B92A5';
Chart.defaults.font.family = 'Roboto Mono';
Chart.defaults.font.size = 9;

var tooltipStyle = {
  backgroundColor:'#161B22',titleColor:'#F5D921',bodyColor:'#E6E8ED',
  borderColor:'#1E2330',borderWidth:1,padding:8,cornerRadius:4
};

// ===== Utilities =====
function fmtM(n){if(!n)return'n/d';if(n>=1000)return'$'+(n/1000).toFixed(1)+'B';return'$'+Math.round(n).toLocaleString()+'M'}
function fmtDate(d){if(!d)return'\u2014';var p=d.split('-');var months=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];return p[2].replace(/^0/,'')+'-'+months[parseInt(p[1])]+'-'+p[0].slice(2)}
function esc(s){var d=document.createElement('div');d.textContent=s||'';return d.innerHTML}

function daysAgo(n){var d=new Date();d.setDate(d.getDate()-n);return d.toISOString().slice(0,10)}
function monthKey(iso){if(!iso)return null;var months=['','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];var p=iso.split('-');return months[parseInt(p[1])]+'-'+p[0].slice(2)}

// ===== Period filtering =====
function periodDays(p){return p==='3M'?90:p==='6M'?180:p==='1Y'?365:null /* ALL */}
// Primary-capital filter: base filter (dated, non-Token/Cross-Stack) AND RPCI-eligible.
// This single point makes every downstream aggregate (KPIs, trends, donut, top rounds,
// top investors, stage distribution, commentary) count only RPCI's eligible set.
function filterByPeriod(rounds,p){
  if(p==='ALL'){
    return rounds.filter(function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isPrimary(r)});
  }
  var cutoff=daysAgo(periodDays(p));
  return rounds.filter(function(r){return r.date&&r.date>=cutoff&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isPrimary(r)});
}
function filterByPriorPeriod(rounds,p){
  if(p==='ALL')return[];/* No prior comparison for ALL window */
  var days=periodDays(p);
  var start=daysAgo(days*2);
  var end=daysAgo(days);
  return rounds.filter(function(r){return r.date&&r.date>=start&&r.date<end&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isPrimary(r)});
}
// Lifecycle exits for the current period (IPOs + excluded M&A), rendered in their own section.
function filterExits(rounds,p){
  var ok=function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isExit(r)};
  if(p==='ALL')return rounds.filter(ok);
  var cutoff=daysAgo(periodDays(p));
  return rounds.filter(function(r){return r.date>=cutoff&&ok(r)});
}
// Non-venture capital events for the current period, rendered in their own section.
function filterNonVenture(rounds,p){
  var ok=function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isNonVenture(r)};
  if(p==='ALL')return rounds.filter(ok);
  var cutoff=daysAgo(periodDays(p));
  return rounds.filter(function(r){return r.date>=cutoff&&ok(r)});
}
// Every dated non-Token/Cross-Stack row in the period (denominator for reconciliation).
function filterAllInWindow(rounds,p){
  var ok=function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'};
  if(p==='ALL')return rounds.filter(ok);
  var cutoff=daysAgo(periodDays(p));
  return rounds.filter(function(r){return r.date>=cutoff&&ok(r)});
}

function median(nums){
  if(!nums||!nums.length)return 0;
  var s=nums.slice().sort(function(a,b){return a-b});
  var m=Math.floor(s.length/2);
  return s.length%2===0?(s[m-1]+s[m])/2:s[m];
}
function calcMetrics(items){
  var disclosed=items.filter(function(r){return r.amount_m!=null});
  var total=0;disclosed.forEach(function(r){total+=r.amount_m});
  var medianDeal=median(disclosed.map(function(r){return r.amount_m}));
  var sectorBk={};
  items.forEach(function(r){
    if(!sectorBk[r.sector])sectorBk[r.sector]={rounds:0,capital_m:0};
    sectorBk[r.sector].rounds++;
    if(r.amount_m)sectorBk[r.sector].capital_m+=r.amount_m;
  });
  var mostActive=null,maxRounds=0;
  for(var s in sectorBk){if(sectorBk[s].rounds>maxRounds){maxRounds=sectorBk[s].rounds;mostActive=s}}
  var largest=null;
  disclosed.forEach(function(r){if(!largest||r.amount_m>largest.amount_m)largest=r});
  // stage — 7-bucket split: Pre-seed, Seed, Series A, Series B, Series C, Series D+, Other
  // Pre-Seed must be checked BEFORE Seed (substring match). Non-venture round
  // values (IPO, M&A, Strategic, Government, Debt, Undisclosed, Pre-IPO, Grant)
  // all consolidate into Other per v1.1.3 polish spec — visual clarity > granularity.
  var stageBk={};
  items.forEach(function(r){
    var rd=r.round||'';
    var stage;
    if(rd.indexOf('Pre-Seed')>=0)stage='Pre-seed';
    else if(rd.indexOf('Seed')>=0)stage='Seed';
    else if(rd.indexOf('Series A')>=0)stage='Series A';
    else if(rd.indexOf('Series B')>=0)stage='Series B';
    else if(rd.indexOf('Series C')>=0)stage='Series C';
    else if(rd.indexOf('Series D')>=0||rd.indexOf('Series E')>=0||rd.indexOf('Series F')>=0||rd.indexOf('Series G')>=0||rd.indexOf('Series H')>=0)stage='Series D+';
    else stage='Other';
    if(!stageBk[stage])stageBk[stage]={rounds:0,capital_m:0};
    stageBk[stage].rounds++;
    if(r.amount_m)stageBk[stage].capital_m+=r.amount_m;
  });
  return{total_capital_m:total,num_rounds:items.length,avg_deal_size_m:disclosed.length?total/disclosed.length:0,median_deal_size_m:medianDeal,most_active_sector:mostActive,largest_round:largest?{company:largest.company,amount_m:largest.amount_m,sector:largest.sector}:null,sector_breakdown:sectorBk,stage_breakdown:stageBk};
}

// Get monthly breakdown by sector for a set of rounds
function monthlyBySector(rounds){
  var result={};
  rounds.forEach(function(r){
    var mk=monthKey(r.date);
    if(!mk||!r.amount_m)return;
    if(!result[mk])result[mk]={};
    if(!result[mk][r.sector])result[mk][r.sector]=0;
    result[mk][r.sector]+=r.amount_m;
  });
  return result;
}

// Generate ordered month keys for last N months
function getMonthKeys(n){
  var keys=[];
  var d=new Date();
  for(var i=n-1;i>=0;i--){
    var dt=new Date(d.getFullYear(),d.getMonth()-i,1);
    var months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    keys.push(months[dt.getMonth()]+'-'+String(dt.getFullYear()).slice(2));
  }
  return keys;
}

// ===== Init =====
async function init(){
  var cb='?v='+Date.now();
  var [sResp,rResp,scResp]=await Promise.all([fetch('data/funding/summary.json'+cb),fetch('data/funding/rounds.json'+cb),fetch('data/index/rpci_scope.json'+cb)]);
  summaryData=await sResp.json();
  roundsData=(await rResp.json()).rounds;
  try{ buildScope(await scResp.json()); }catch(e){ console.warn('rpci_scope load failed; funding page will show unfiltered (all rounds)',e); }
  renderAll();
}

function setPeriod(btn){
  document.querySelectorAll('.time-btn').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  currentPeriod=btn.dataset.period;
  renderAll();
}

// Overview is the only navigable tab; Rounds / Investors / Funds buttons
// route directly to the early-access form via openEarlyAccess() (no
// intermediate gated-content surface). Guard against missing tab divs.
function setTab(tab,btn){
  document.querySelectorAll('.fund-tab').forEach(function(b){b.classList.remove('active')});
  if(btn)btn.classList.add('active');
  var el=document.getElementById('tab-'+tab);
  if(el)el.style.display='';
}

// ===== Main Render =====
function renderAll(){
  if(!roundsData)return;
  var current=filterByPeriod(roundsData,currentPeriod);
  var prior=filterByPriorPeriod(roundsData,currentPeriod);
  var p=calcMetrics(current);
  var pp=prior.length>0?calcMetrics(prior):null;
  var periodLabel=currentPeriod==='3M'?'3 months':currentPeriod==='6M'?'6 months':currentPeriod==='1Y'?'12 months':'all-time window';

  // Metrics
  var chg=function(curr,prev,hasPrior){
    if(!hasPrior||!prev)return'';
    var pct=prev===0?0:((curr-prev)/prev*100).toFixed(0);
    var cls=pct>=0?'v-green':'v-red';
    return' <span class="metric-change '+cls+'">'+(pct>=0?'+':'')+pct+'%<\/span><span style="font-size:8px;color:#5A6178"> vs prior<\/span>';
  };
  var hasPrior=pp&&pp.num_rounds>0;
  // ex-mega-deals YoY (rounds where amount_m < 10000 -- i.e., excluding $10B+ deals)
  var exMegaSub='';
  if(hasPrior){
    var currExMega=current.filter(function(r){return!r.amount_m||r.amount_m<10000});
    var priorExMega=prior.filter(function(r){return!r.amount_m||r.amount_m<10000});
    var currExMegaCap=0;currExMega.forEach(function(r){if(r.amount_m)currExMegaCap+=r.amount_m});
    var priorExMegaCap=0;priorExMega.forEach(function(r){if(r.amount_m)priorExMegaCap+=r.amount_m});
    if(priorExMegaCap>0){
      var exPct=((currExMegaCap-priorExMegaCap)/priorExMegaCap*100).toFixed(0);
      exMegaSub='ex-mega-deals: '+(exPct>=0?'+':'')+exPct+'% YoY';
    }
  }
  // Avg Deal Size \u2014 mean + median (two-line treatment; median is the more
  // honest representation given mega-deal skew from SpaceX/Waymo/Globalstar)
  var meanChg=chg(p.avg_deal_size_m,pp?pp.avg_deal_size_m:0,hasPrior);
  var medChg=chg(p.median_deal_size_m,pp?pp.median_deal_size_m:0,hasPrior);
  var avgHtml='<div class="metric-value" style="font-size:0.95rem">'+fmtM(p.avg_deal_size_m)+
    ' <span style="font-size:8px;color:#5A6178;font-weight:400">mean</span>'+meanChg+'<\/div>'+
    '<div class="metric-sub" style="color:#e6e8ed;font-size:10px;margin-top:0.25rem">'+fmtM(p.median_deal_size_m)+
    ' <span style="color:#5A6178">median</span>'+medChg+'<\/div>';

  // Most Active Sector \u2014 five-line breakdown by sector (sorted desc by deal count;
  // omit zero-count buckets). Replaces single-stat tile per v1.1.3 polish pass.
  var sectorRows=Object.keys(p.sector_breakdown)
    .map(function(s){return{name:s,rounds:p.sector_breakdown[s].rounds}})
    .filter(function(x){return x.rounds>0})
    .sort(function(a,b){return b.rounds-a.rounds});
  var sectorHtml='<div style="font-family:var(--font);margin-top:0.15rem">';
  sectorRows.forEach(function(x,i){
    sectorHtml+='<div style="display:flex;justify-content:space-between;align-items:baseline;font-size:10px;padding:1.5px 0;'+
      (i>0?'border-top:1px solid rgba(37,42,54,0.5);':'')+
      '"><span style="color:#e6e8ed">'+esc(x.name)+'<\/span>'+
      '<span style="color:#8B92A5;font-variant-numeric:tabular-nums">'+x.rounds+'<\/span><\/div>';
  });
  sectorHtml+='<\/div>';

  var cards=[
    {label:'Capital Raised',value:fmtM(p.total_capital_m),change:chg(p.total_capital_m,pp?pp.total_capital_m:0,hasPrior),sub:exMegaSub},
    {label:'Number of Rounds',value:p.num_rounds,change:chg(p.num_rounds,pp?pp.num_rounds:0,hasPrior)},
    {label:'Avg Deal Size',htmlOverride:avgHtml},
    {label:'Most Active Sector',htmlOverride:sectorHtml},
    {label:'Largest Round',value:p.largest_round?esc(p.largest_round.company):'\u2014',sub:p.largest_round?fmtM(p.largest_round.amount_m):''},
    {label:'Top Investor',value:getTopInvestor(current),sub:''}
  ];
  var mg=document.getElementById('metrics-grid');mg.innerHTML='';
  cards.forEach(function(c){
    var d=document.createElement('div');d.className='metric-card';
    if(c.htmlOverride){
      d.innerHTML='<div class="metric-label">'+c.label+'<\/div>'+c.htmlOverride;
    }else{
      d.innerHTML='<div class="metric-label">'+c.label+'<\/div><div class="metric-value">'+c.value+(c.change||'')+'<\/div>'+(c.sub?'<div class="metric-sub">'+c.sub+'<\/div>':'');
    }
    mg.appendChild(d);
  });

  renderTopRounds(current);
  renderSectorChart(p);
  renderTrendsChart(current);
  renderTopInvestors(current);
  renderStageDistribution(p);
  renderNotable(p,periodLabel);
  var exitsRows=filterExits(roundsData,currentPeriod);
  var nvRows=filterNonVenture(roundsData,currentPeriod);
  renderExits(exitsRows);
  renderNonVenture(nvRows);
  // Reconciliation: primary + exits + non-venture must equal every row in the window.
  var windowTotal=filterAllInWindow(roundsData,currentPeriod).length;
  var recon=current.length+exitsRows.length+nvRows.length;
  window.__fundRecon={primary:current.length,exits:exitsRows.length,nonventure:nvRows.length,sum:recon,windowTotal:windowTotal,ok:recon===windowTotal};
  if(recon!==windowTotal) console.warn('funding reconciliation mismatch',window.__fundRecon);

  // "View all N rounds in dataset" — always shows the FULL dataset row count,
  // unfiltered. A VC sees the same headline number here as on the CSV they
  // receive (no in-scope filter delta to explain). Updates dynamically as
  // new rounds are added in subsequent monthly regenerations.
  var viewAllLink=document.getElementById('view-all-rounds-link');
  if(viewAllLink){
    viewAllLink.innerHTML='View all '+roundsData.length.toLocaleString()+' rounds in dataset &rarr;';
  }
}

function getTopInvestor(rounds){
  var counts={};
  rounds.forEach(function(r){
    var seen={};
    [r.lead_investors,r.co_investors].forEach(function(f){
      if(!f)return;
      f.split(/,(?![^()]*\))/).forEach(function(inv){
        inv=inv.trim();
        var il=inv.toLowerCase();if(inv.length<3||il==='n/d'||il==='multiple'||il==='undisclosed'||il==='various'||il==='chinese vcs'||il==='not disclosed')return;
        if(seen[il])return;seen[il]=1;
        counts[inv]=(counts[inv]||0)+1;
      });
    });
  });
  var best=null,max=0;
  for(var k in counts){if(counts[k]>max){max=counts[k];best=k}}
  return best?esc(best):'\u2014';
}

// ===== Top Rounds (sortable) =====
var currentTopRounds=[];
function renderTopRounds(rounds){
  currentTopRounds=rounds.filter(function(r){return r.amount_m!=null}).sort(function(a,b){return b.amount_m-a.amount_m}).slice(0,10);
  topRoundsSortCol='amount';topRoundsSortAsc=false;
  drawTopRounds();
}

function sortTopRounds(col){
  if(topRoundsSortCol===col)topRoundsSortAsc=!topRoundsSortAsc;
  else{topRoundsSortCol=col;topRoundsSortAsc=col==='company'||col==='sector'||col==='date'}

  currentTopRounds.sort(function(a,b){
    var va,vb;
    if(col==='company'){va=(a.company||'').toLowerCase();vb=(b.company||'').toLowerCase();return va<vb?-1:va>vb?1:0}
    if(col==='sector'){va=a.sector;vb=b.sector;return va<vb?-1:va>vb?1:0}
    if(col==='round'){va=stageOrder[a.round]!=null?stageOrder[a.round]:99;vb=stageOrder[b.round]!=null?stageOrder[b.round]:99;return va-vb}
    if(col==='amount'){return(a.amount_m||0)-(b.amount_m||0)}
    if(col==='date'){return(a.date||'')<(b.date||'')?-1:1}
    return 0;
  });
  if(!topRoundsSortAsc)currentTopRounds.reverse();
  drawTopRounds();
}

function drawTopRounds(){
  // Update sort arrows
  ['company','sector','round','amount','date'].forEach(function(c){
    var el=document.getElementById('sort-'+c);
    if(el)el.textContent=topRoundsSortCol===c?(topRoundsSortAsc?'\u25B2':'\u25BC'):'';
  });
  var tbody=document.getElementById('top-rounds-body');tbody.innerHTML='';
  currentTopRounds.forEach(function(r,i){
    var tr=document.createElement('tr');
    tr.innerHTML='<td style="color:#5A6178">'+(i+1)+'<\/td><td style="font-weight:600">'+esc(r.company)+'<\/td><td><span class="sector-pill '+(sectorPillCls[r.sector]||'')+'">'+esc(r.sector)+'<\/span><\/td><td>'+esc(r.round)+'<\/td><td class="r" style="font-weight:600">'+fmtM(r.amount_m)+'<\/td><td style="color:#5A6178">'+fmtDate(r.date)+'<\/td>';
    tbody.appendChild(tr);
  });
}

// ===== Trends Chart (always 6M minimum; 'ALL' shows full dataset history) =====
function renderTrendsChart(currentRounds){
  var days=periodDays(currentPeriod);
  var chartMonths,activeCutoffMonths,dimStart,chartRounds;
  if(currentPeriod==='ALL'){
    // Show every month from earliest dated round through now; no dimming.
    chartRounds=roundsData.filter(function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isPrimary(r)});
    var earliest=chartRounds.reduce(function(a,r){return r.date<a?r.date:a},'9999-99-99');
    var ed=earliest.split('-');var now=new Date();
    chartMonths=(now.getFullYear()-parseInt(ed[0]))*12+(now.getMonth()+1-parseInt(ed[1]))+1;
    activeCutoffMonths=chartMonths;dimStart=0;/* no dim */
  }else{
    chartMonths=Math.max(6,Math.ceil(days/30));
    activeCutoffMonths=Math.ceil(days/30);
    dimStart=chartMonths-activeCutoffMonths;
    var chartCutoff=daysAgo(chartMonths*31);
    chartRounds=roundsData.filter(function(r){return r.date&&r.date>=chartCutoff&&r.sector!=='Token'&&r.sector!=='Cross-Stack'&&isPrimary(r)});
  }
  var allMonths=getMonthKeys(chartMonths);
  var mbs=monthlyBySector(chartRounds);

  var sectors=['Semiconductors','Robotics','Space','Materials'];
  var datasets=sectors.map(function(s){
    var data=allMonths.map(function(m){return mbs[m]&&mbs[m][s]?Math.round(mbs[m][s]):0});
    // Build per-bar opacity
    var bgColors=allMonths.map(function(_,idx){
      var base=sectorColors[s];
      if(currentPeriod==='3M'&&idx<dimStart){
        // Parse hex to rgba with 0.35 opacity
        var r2=parseInt(base.slice(1,3),16),g=parseInt(base.slice(3,5),16),b=parseInt(base.slice(5,7),16);
        return'rgba('+r2+','+g+','+b+',0.35)';
      }
      return base;
    });
    return{label:s,backgroundColor:bgColors,data:data};
  });

  if(trendsChart)trendsChart.destroy();
  trendsChart=new Chart(document.getElementById('trends-chart'),{
    type:'bar',
    data:{labels:allMonths,datasets:datasets},
    options:{
      responsive:true,maintainAspectRatio:false,
      plugins:{
        legend:{display:true,position:'bottom',labels:{color:'#E6E8ED',font:{family:'Roboto Mono',size:9},boxWidth:10,padding:8}},
        tooltip:tooltipStyle
      },
      scales:{
        x:{stacked:true,ticks:{color:'#5A6178',font:{family:'Roboto Mono',size:9}},grid:{color:'#1E2330'}},
        y:{stacked:true,ticks:{color:'#5A6178',font:{family:'Roboto Mono',size:9},callback:function(v){return'$'+v.toLocaleString()+'M'}},grid:{color:'#1E2330'}}
      }
    }
  });
}

// ===== Sector Donut =====
function renderSectorChart(p){
  var sectors=Object.keys(p.sector_breakdown);
  var vals=sectors.map(function(s){return p.sector_breakdown[s].capital_m});
  var total=vals.reduce(function(a,b){return a+b},0);
  if(sectorChart)sectorChart.destroy();
  sectorChart=new Chart(document.getElementById('sector-chart'),{
    type:'doughnut',
    data:{labels:sectors,datasets:[{data:vals,backgroundColor:sectors.map(function(s){return sectorColors[s]}),borderWidth:0}]},
    options:{
      responsive:true,cutout:'60%',
      plugins:{
        tooltip:tooltipStyle,
        legend:{display:false}
      }
    }
  });
  // Render HTML legend with guaranteed light text
  var legendEl=document.getElementById('sector-legend');
  if(legendEl){
    legendEl.innerHTML=sectors.map(function(s,i){
      var v=vals[i];
      var pct=total>0?(v/total*100).toFixed(0)+'%':'0%';
      var color=sectorColors[s];
      return '<span style="display:inline-flex;align-items:center;margin-right:10px;margin-bottom:4px;font-size:9px;font-family:\'Space Grotesk\',sans-serif;font-variant-numeric:tabular-nums;color:#E6E8ED;">'
        +'<span style="display:inline-block;width:10px;height:10px;border-radius:2px;background:'+color+';margin-right:5px;flex-shrink:0;"><\/span>'
        +esc(s)+' '+pct+' ('+fmtM(v)+')<\/span>';
    }).join('');
  }
}

// ===== Top Investors =====
function renderTopInvestors(rounds){
  var counts={};
  rounds.forEach(function(r){
    var seen={};
    [r.lead_investors,r.co_investors].forEach(function(f){
      if(!f)return;
      f.split(/,(?![^()]*\))/).forEach(function(inv){
        inv=inv.trim();
        var il=inv.toLowerCase();if(inv.length<3||il==='n/d'||il==='multiple'||il==='undisclosed'||il==='various'||il==='chinese vcs'||il==='not disclosed')return;
        if(seen[il])return;seen[il]=1;
        counts[inv]=(counts[inv]||0)+1;
      });
    });
  });
  var sorted=Object.keys(counts).map(function(k){return{name:k,deals:counts[k]}}).sort(function(a,b){return b.deals-a.deals}).slice(0,10);
  var maxDeals=sorted.length?sorted[0].deals:1;
  var container=document.getElementById('top-investors');container.innerHTML='';
  sorted.forEach(function(inv){
    var d=document.createElement('div');d.className='inv-bar';
    d.innerHTML='<div class="inv-name" title="'+esc(inv.name)+'">'+esc(inv.name)+'<\/div><div class="inv-fill" style="width:'+Math.round(inv.deals/maxDeals*120)+'px"><\/div><div class="inv-count">'+inv.deals+'<\/div>';
    container.appendChild(d);
  });
}

// ===== Stage Distribution =====
// 10-bucket split aligned with v1.0 round enum (Series ladder + Strategic / Government / Debt / IPO+M&A / Other).
// Hide buckets with zero rounds in the active period to keep the chart compact.
function renderStageDistribution(p){
  if(!p.stage_breakdown)return;
  // 7-bucket split per v1.1.3 polish spec: Pre-seed + Series ladder + Other.
  // Other consolidates non-venture round values (IPO/M&A/Strategic/Govt/Debt/etc).
  // Pre-seed color (#FCD34D) is a slightly lighter yellow than Seed's (#F5D921)
  // to signal "earlier-in-funnel" while staying visually adjacent.
  var stages=['Pre-seed','Seed','Series A','Series B','Series C','Series D+','Other'];
  var stgColors=['#FCD34D','#F5D921','#3B82F6','#22C55E','#a78bfa','#ef4444','#5A6178'];
  var maxRounds=Math.max.apply(null,stages.map(function(s){return(p.stage_breakdown[s]?p.stage_breakdown[s].rounds:0)}));
  if(maxRounds===0)maxRounds=1;
  var container=document.getElementById('stage-dist');container.innerHTML='';
  stages.forEach(function(s,i){
    var d=p.stage_breakdown[s];
    if(!d||d.rounds===0)return;/* skip empty buckets */
    var el=document.createElement('div');el.className='stage-row';
    el.innerHTML='<div class="stage-label">'+s+'<\/div><div class="stage-bar" style="width:'+Math.round(d.rounds/maxRounds*100)+'px;background:'+stgColors[i]+'"><\/div><div class="stage-val">'+d.rounds+' ('+fmtM(d.capital_m)+')<\/div>';
    container.appendChild(el);
  });
}

// ===== Notable =====
function renderNotable(p,periodLabel){
  var mostActive=p.most_active_sector||'Robotics';
  var mostActiveRounds=p.sector_breakdown[mostActive]?p.sector_breakdown[mostActive].rounds:0;
  // Count mega-rounds from filtered period data
  var current=filterByPeriod(roundsData,currentPeriod);
  var megas=current.filter(function(r){return r.amount_m&&r.amount_m>=500}).length;
  // Find sector with highest avg deal size
  var bestAvgSector='',bestAvg=0;
  for(var s in p.sector_breakdown){
    var sd=p.sector_breakdown[s];
    var avg=sd.rounds>0?sd.capital_m/sd.rounds:0;
    if(avg>bestAvg){bestAvg=avg;bestAvgSector=s;}
  }
  // Period phrasing: "in the last 3 months" vs "across the full dataset (since Jan 2023)"
  var phrase=currentPeriod==='ALL'?'across the full dataset (since Jan 2023)':'in the last '+periodLabel;
  document.getElementById('notable-card').innerHTML=
    'Tovarishch, <strong>'+p.num_rounds+' frontier stack rounds<\/strong> detected '+phrase+', deploying <strong>'+fmtM(p.total_capital_m)+'<\/strong> of capital. '+esc(mostActive)+' dominates deal flow with '+mostActiveRounds+' rounds, but '+esc(bestAvgSector)+' commands the highest average deal size at '+fmtM(Math.round(bestAvg))+' per round. <strong>'+megas+' mega-rounds<\/strong> exceeding $500M signal deep conviction in frontier compute and physical AI infrastructure.';
}

// ===== Lifecycle Exits =====
// IPOs (listed + filed) and excluded M&A (public / out-of-universe acquirers).
// Stored for the record but deliberately excluded from every primary-capital
// figure and from the RPCI. Private in-universe M&A is NOT here — it stays in
// the primary view because it redeploys private capital (feeds RPCI).
function renderExits(exits){
  var tbody=document.getElementById('exits-body');
  var sec=document.getElementById('exits-section');
  if(!tbody||!sec)return;
  if(!exits.length){sec.style.display='none';return;}
  sec.style.display='';
  var sorted=exits.slice().sort(function(a,b){return (b.amount_m||0)-(a.amount_m||0)});
  tbody.innerHTML='';
  sorted.slice(0,12).forEach(function(r){
    var t=(r.round||'').trim();
    var label=t==='M&A'?'Acquisition':(t==='IPO (filed)'?'IPO (filed)':'IPO');
    var tr=document.createElement('tr');
    tr.innerHTML='<td style="font-weight:600">'+esc(r.company)+'<\/td>'+
      '<td><span style="font-size:9px;color:#8B92A5;border:1px solid #252A36;border-radius:3px;padding:1px 5px">'+label+'<\/span><\/td>'+
      '<td>'+esc(r.sector)+'<\/td>'+
      '<td class="r" style="font-weight:600;color:#8B92A5">'+fmtM(r.amount_m)+'<\/td>'+
      '<td style="color:#5A6178">'+fmtDate(r.date)+'<\/td>';
    tbody.appendChild(tr);
  });
  var ipos=exits.filter(function(r){var t=(r.round||'').trim();return t==='IPO'||t==='IPO (filed)'}).length;
  var mnas=exits.length-ipos;
  var val=0;exits.forEach(function(r){if(r.amount_m)val+=r.amount_m});
  var sum=document.getElementById('exits-summary');
  if(sum){
    sum.innerHTML=exits.length+' exit'+(exits.length!==1?'s':'')+' in view — '+
      ipos+' IPO'+(ipos!==1?'s':'')+', '+mnas+' acquisition'+(mnas!==1?'s':'')+
      ' — totalling '+fmtM(val)+', all excluded from the capital figures above'+
      (sorted.length>12?' (top 12 shown)':'')+'.';
  }
}

// ===== Non-venture capital events =====
// Strategic / Government / Grant / Debt / Bridge / Undisclosed / Other / blank —
// excluded from primary capital and from the RPCI, and not lifecycle exits either.
// Stored for completeness; surfaced here so no row silently vanishes from the page.
function renderNonVenture(items){
  var tbody=document.getElementById('nonventure-body');
  var sec=document.getElementById('nonventure-section');
  if(!tbody||!sec)return;
  if(!items.length){sec.style.display='none';return;}
  sec.style.display='';
  var sorted=items.slice().sort(function(a,b){return (b.amount_m||0)-(a.amount_m||0)});
  tbody.innerHTML='';
  sorted.slice(0,12).forEach(function(r){
    var typ=(r.round||'').trim()||'Undisclosed';
    var tr=document.createElement('tr');
    tr.innerHTML='<td style="font-weight:600">'+esc(r.company)+'<\/td>'+
      '<td><span style="font-size:9px;color:#8B92A5;border:1px solid #252A36;border-radius:3px;padding:1px 5px">'+esc(typ)+'<\/span><\/td>'+
      '<td>'+esc(r.sector)+'<\/td>'+
      '<td class="r" style="font-weight:600;color:#8B92A5">'+fmtM(r.amount_m)+'<\/td>'+
      '<td style="color:#5A6178">'+fmtDate(r.date)+'<\/td>';
    tbody.appendChild(tr);
  });
  var val=0;items.forEach(function(r){if(r.amount_m)val+=r.amount_m});
  var sum=document.getElementById('nonventure-summary');
  if(sum){
    sum.innerHTML=items.length+' non-venture event'+(items.length!==1?'s':'')+' in view — totalling '+fmtM(val)+
      ', excluded from the capital figures above'+(sorted.length>12?' (top 12 shown)':'')+'.';
  }
}

// ===== Gated tab content removed (v1.1.3 polish): the Rounds / Investors /
// Frontier Funds tabs now route their button clicks directly to
// openEarlyAccess() \u2014 no intermediate "Early Access Required" surface to
// populate. The previous buildGatedTables() function was removed alongside
// the gated tab divs in funding.html. =====

// ===== Robotnik Private Capital Index (RPCI) =====
// Loads data/index/private_capital_index.json and renders the chart panel
// at the top of the page. Independent of the Funding Ops metrics (which
// use the trailing 3M/6M/1Y window selector); the RPCI is monthly with a
// fixed 3M trailing window per spec.
var rpciChart = null;
var rpciData = null;

async function initRPCI() {
  try {
    var resp = await fetch('data/index/private_capital_index.json?v=' + Date.now());
    if (!resp.ok) throw new Error('RPCI JSON fetch failed: ' + resp.status);
    rpciData = await resp.json();
  } catch (e) {
    console.warn('RPCI load failed', e);
    var panel = document.getElementById('rpci-panel');
    if (panel) panel.style.display = 'none';
    return;
  }
  if (!rpciData || !rpciData.series || !rpciData.series.length) return;
  renderRPCIHeader();
  renderRPCIChart();
}

function fmtIdx(v) {
  if (v == null) return '—';
  return Number(v).toLocaleString(undefined, {minimumFractionDigits: 1, maximumFractionDigits: 1});
}

function renderRPCIHeader() {
  var series = rpciData.series;
  var latest = series[series.length - 1];
  var prior = series.length >= 2 ? series[series.length - 2] : null;
  var cur = document.getElementById('rpci-current-value');
  var mon = document.getElementById('rpci-current-month');
  var tr = document.getElementById('rpci-trailing-value');
  var mom = document.getElementById('rpci-mom-change');
  if (cur) cur.textContent = fmtIdx(latest.value);
  if (mon) {
    // Format month_key (YYYY-MM) into "Mon YYYY" display
    var parts = latest.month.split('-');
    var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
    mon.textContent = months[parseInt(parts[1])-1] + ' ' + parts[0];
  }
  if (tr) tr.textContent = fmtIdx(latest.value_3m_trailing);
  if (mom) {
    if (!prior) {
      mom.textContent = '—';
    } else {
      var delta = latest.value - prior.value;
      var pct = prior.value !== 0 ? (delta / prior.value * 100) : 0;
      var sign = pct >= 0 ? '+' : '';
      mom.textContent = sign + pct.toFixed(1) + '%';
      mom.style.color = pct >= 0 ? '#22c55e' : '#ef4444';
    }
  }
}

function renderRPCIChart() {
  var canvas = document.getElementById('rpci-chart');
  if (!canvas || typeof Chart === 'undefined') return;

  // v1.4: chart displays Jan 2024 onward (full-confidence segment only).
  // The 2023 calibration rows remain in rpciData.series for API consumers
  // but are filtered out here so the displayed line is uniformly weighted
  // (5-component full) with no segment-styling needed.
  var series = rpciData.series.filter(function(r) { return !r.calibration; });

  var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  var labels = series.map(function(r) {
    var p = r.month.split('-');
    return months[parseInt(p[1])-1] + '-' + p[0].slice(2);
  });
  var monthlyData = series.map(function(r) { return r.value; });
  var trailingData = series.map(function(r) { return r.value_3m_trailing; });
  // value_6m_trailing is also available in the JSON for research but
  // intentionally not plotted — 6M is too lagging for monthly cadence.

  // Index of the base month (March 2025) within the displayed series for
  // the vertical marker. With the chart starting Jan 2024, March 2025 sits
  // 14 entries in.
  var baseIdx = series.findIndex(function(r) { return r.month === '2025-03'; });

  // Plugin to draw the base-value horizontal line at y=1000 and a vertical
  // marker at the base month (March 2025). Mirrors the public-index
  // chart's visual pattern. (The calibration → live divider was retired in
  // v1.4 alongside the 2023 segment.)
  var rpciBaselinePlugin = {
    id: 'rpciBaselines',
    afterDatasetsDraw: function(chart) {
      var ctx = chart.ctx;
      var area = chart.chartArea;
      var xs = chart.scales.x;
      var ys = chart.scales.y;
      if (!area || !xs || !ys) return;

      // Horizontal reference line at the base value (1,000)
      var yBase = ys.getPixelForValue(rpciData.base_value);
      if (yBase >= area.top && yBase <= area.bottom) {
        ctx.save();
        ctx.strokeStyle = 'rgba(230,232,237,0.18)';
        ctx.lineWidth = 1;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.moveTo(area.left, yBase);
        ctx.lineTo(area.right, yBase);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.font = '10px "Roboto Mono", monospace';
        ctx.fillStyle = 'rgba(230,232,237,0.55)';
        ctx.textAlign = 'right';
        ctx.textBaseline = 'bottom';
        ctx.fillText('Base 1,000', area.right - 4, yBase - 3);
        ctx.restore();
      }

      // Vertical marker at the base month (March 2025)
      if (baseIdx >= 0) {
        var xBase = xs.getPixelForValue(baseIdx);
        ctx.save();
        ctx.strokeStyle = 'rgba(245,217,33,0.30)';
        ctx.lineWidth = 1;
        ctx.setLineDash([4, 3]);
        ctx.beginPath();
        ctx.moveTo(xBase, area.top);
        ctx.lineTo(xBase, area.bottom);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.font = '10px "Roboto Mono", monospace';
        ctx.fillStyle = 'rgba(245,217,33,0.75)';
        ctx.textAlign = 'left';
        ctx.textBaseline = 'top';
        ctx.fillText('Mar 25 base', xBase + 4, area.top + 2);
        ctx.restore();
      }
    },
  };

  if (rpciChart) rpciChart.destroy();
  rpciChart = new Chart(canvas, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [
        {
          label: 'Monthly',
          data: monthlyData,
          borderColor: 'rgba(245,217,33,0.55)',
          backgroundColor: 'rgba(245,217,33,0.10)',
          borderWidth: 1.5,
          pointRadius: 2.5,
          pointBackgroundColor: '#F5D921',
          pointHoverRadius: 5,
          tension: 0,
          fill: false,
        },
        {
          label: '3M trailing',
          data: trailingData,
          borderColor: '#F5D921',
          backgroundColor: 'rgba(245,217,33,0.10)',
          borderWidth: 2.5,
          pointRadius: 0,
          pointHoverRadius: 4,
          pointBackgroundColor: '#F5D921',
          tension: 0.25,
          fill: true,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: {
          display: true,
          position: 'bottom',
          labels: { color: '#E6E8ED', font: { family: 'Roboto Mono', size: 10 }, boxWidth: 12, padding: 10 }
        },
        tooltip: {
          backgroundColor: '#161B22',
          titleColor: '#F5D921',
          bodyColor: '#E6E8ED',
          borderColor: '#1E2330',
          borderWidth: 1,
          padding: 10,
          cornerRadius: 4,
          titleFont: { family: 'Roboto Mono', size: 11, weight: 'bold' },
          bodyFont: { family: 'Roboto Mono', size: 10 },
          callbacks: {
            label: function(ctx) {
              var v = ctx.parsed.y;
              return ctx.dataset.label + ': ' + (v == null ? '—' : Number(v).toFixed(1));
            },
            afterBody: function(items) {
              if (!items || !items.length) return '';
              var idx = items[0].dataIndex;
              // The chart displays the filtered (Jan 2024 onward) series,
              // so the tooltip index refers to that filtered array — keep
              // it consistent for MoM + component lookups.
              var row = series[idx];
              if (!row || !row.components) return '';
              var lines = [];
              // MoM line — month-on-month delta from the prior monthly point.
              // Null for the first row in the displayed series (Jan 2024).
              if (idx > 0) {
                var prior = series[idx - 1];
                if (prior && prior.value) {
                  var d = (row.value - prior.value) / prior.value * 100;
                  var s = (d >= 0 ? '+' : '') + d.toFixed(1) + '%';
                  lines.push('MoM: ' + s);
                }
              }
              lines.push('');
              lines.push('Components (normalised, 1000 @ base):');
              var labelsM = {
                capital_deployed:        'Capital deployed   (30%)',
                deal_count:              'Deal count         (20%)',
                stage_weighted_activity: 'Stage-weighted     (25%)',
                round_size_vs_trailing:  'Size vs trailing   (15%)',
                investor_breadth:        'Investor breadth   (10%)',
              };
              Object.keys(labelsM).forEach(function(k) {
                var v = row.components[k];
                if (v != null) {
                  lines.push('  ' + labelsM[k] + '  ' + Number(v).toFixed(1));
                }
              });
              lines.push('');
              lines.push('Raw: ' + row.deal_count_raw + ' deals · $' +
                         (row.capital_deployed_raw_usd / 1e9).toFixed(1) + 'B (capped)');
              return lines;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: '#5A6178',
            font: { family: 'Roboto Mono', size: 9 },
            autoSkip: true,
            maxRotation: 0,
            maxTicksLimit: 14,
          },
          grid: { color: '#1E2330' },
        },
        y: {
          // Auto-scale; do not force a floor. The Base 1,000 reference
          // line (drawn by rpciBaselinePlugin) anchors the reader
          // regardless of where the axis floor lands.
          ticks: {
            color: '#5A6178',
            font: { family: 'Roboto Mono', size: 9 },
            callback: function(v) { return Number(v).toLocaleString(); },
          },
          grid: { color: '#1E2330' },
          beginAtZero: false,
        },
      },
    },
    plugins: [rpciBaselinePlugin],
  });
}

// Fire the RPCI panel alongside the rest of the page init
initRPCI();

init();
