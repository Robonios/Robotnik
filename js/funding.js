// ===== FUNDING OPERATIONS PAGE =====
var summaryData = null, roundsData = null;
var currentPeriod = '1Y';
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
function filterByPeriod(rounds,p){
  if(p==='ALL'){
    return rounds.filter(function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'});
  }
  var cutoff=daysAgo(periodDays(p));
  return rounds.filter(function(r){return r.date&&r.date>=cutoff&&r.sector!=='Token'&&r.sector!=='Cross-Stack'});
}
function filterByPriorPeriod(rounds,p){
  if(p==='ALL')return[];/* No prior comparison for ALL window */
  var days=periodDays(p);
  var start=daysAgo(days*2);
  var end=daysAgo(days);
  return rounds.filter(function(r){return r.date&&r.date>=start&&r.date<end&&r.sector!=='Token'&&r.sector!=='Cross-Stack'});
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
  var [sResp,rResp]=await Promise.all([fetch('data/funding/summary.json'+cb),fetch('data/funding/rounds.json'+cb)]);
  summaryData=await sResp.json();
  roundsData=(await rResp.json()).rounds;
  renderAll();
  buildGatedTables();
}

function setPeriod(btn){
  document.querySelectorAll('.time-btn').forEach(function(b){b.classList.remove('active')});
  btn.classList.add('active');
  currentPeriod=btn.dataset.period;
  renderAll();
}

function setTab(tab,btn){
  document.querySelectorAll('.fund-tab').forEach(function(b){b.classList.remove('active')});
  if(btn)btn.classList.add('active');
  else document.querySelector('.fund-tab[onclick*="'+tab+'"]')?.classList.add('active');
  ['overview','rounds','investors','funds'].forEach(function(t){
    document.getElementById('tab-'+t).style.display=t===tab?'':'none';
  });
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

  // "View all N rounds in dataset" — always shows the FULL frontier-stack
  // dataset size (Token / Cross-Stack excluded for consistency with filterByPeriod),
  // regardless of the active time window. Updates dynamically as new rounds
  // are added in subsequent monthly regenerations.
  var viewAllLink=document.getElementById('view-all-rounds-link');
  if(viewAllLink){
    var datasetCount=roundsData.filter(function(r){
      return r.sector!=='Token'&&r.sector!=='Cross-Stack';
    }).length;
    viewAllLink.innerHTML='View all '+datasetCount.toLocaleString()+' rounds in dataset &rarr;';
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
    chartRounds=roundsData.filter(function(r){return r.date&&r.sector!=='Token'&&r.sector!=='Cross-Stack'});
    var earliest=chartRounds.reduce(function(a,r){return r.date<a?r.date:a},'9999-99-99');
    var ed=earliest.split('-');var now=new Date();
    chartMonths=(now.getFullYear()-parseInt(ed[0]))*12+(now.getMonth()+1-parseInt(ed[1]))+1;
    activeCutoffMonths=chartMonths;dimStart=0;/* no dim */
  }else{
    chartMonths=Math.max(6,Math.ceil(days/30));
    activeCutoffMonths=Math.ceil(days/30);
    dimStart=chartMonths-activeCutoffMonths;
    var chartCutoff=daysAgo(chartMonths*31);
    chartRounds=roundsData.filter(function(r){return r.date&&r.date>=chartCutoff&&r.sector!=='Token'&&r.sector!=='Cross-Stack'});
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

// ===== Gated Tables =====
function buildGatedTables(){
  var rt=document.getElementById('rounds-blur-table');
  var tbl=document.createElement('table');tbl.className='top-table';tbl.style.margin='1rem';
  tbl.innerHTML='<thead><tr><th>Company<\/th><th>Sector<\/th><th>Round<\/th><th class="r">Amount<\/th><th>Lead<\/th><th>Date<\/th><th>Location<\/th><\/tr><\/thead>';
  var tb=document.createElement('tbody');
  roundsData.slice(0,15).forEach(function(r){
    var tr=document.createElement('tr');
    tr.innerHTML='<td>'+esc(r.company)+'<\/td><td>'+esc(r.sector)+'<\/td><td>'+esc(r.round||'')+'<\/td><td class="r">'+(r.amount_m?fmtM(r.amount_m):'n/d')+'<\/td><td>'+esc(r.lead_investors||'\u2014')+'<\/td><td>'+fmtDate(r.date)+'<\/td><td>'+esc(r.location||'\u2014')+'<\/td>';
    tb.appendChild(tr);
  });
  tbl.appendChild(tb);rt.appendChild(tbl);

  var it=document.getElementById('investors-blur-table');
  var tbl2=document.createElement('table');tbl2.className='top-table';tbl2.style.margin='1rem';
  tbl2.innerHTML='<thead><tr><th>Investor<\/th><th class="r"># Deals<\/th><th>Sectors<\/th><\/tr><\/thead>';
  var tb2=document.createElement('tbody');
  summaryData.top_investors.slice(0,10).forEach(function(inv){
    var tr=document.createElement('tr');
    tr.innerHTML='<td>'+esc(inv.name)+'<\/td><td class="r">'+inv.deals+'<\/td><td>'+esc(inv.sectors.join(', '))+'<\/td>';
    tb2.appendChild(tr);
  });
  tbl2.appendChild(tb2);it.appendChild(tbl2);
}

init();
